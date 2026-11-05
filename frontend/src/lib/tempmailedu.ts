// tempmail.id.vn 客户端。
//
// 这个来源的 API key 是账号级凭证，绝不能进前端包。浏览器只跟本站的
// /api/vn/... 打交道，由 vnproxy 在服务端持有 key、决定用哪个账号、
// 以及在账号满了之后删掉最旧的邮箱。前端只看到自己的那一个地址。
//
// 注意 mail_id 不可缓存：删掉重建的同名地址会拿到新 id。

import type { MailMessage, MailMessageDetail } from "./mailbox";

const BASE_URL = "/api/vn";

interface Envelope<T> {
	success: boolean;
	message: string;
	// 失败时由 vnproxy 带上，决定前端给什么提示。
	kind?: "quota" | "notfound" | "auth" | "other";
	data: T;
}

interface RawMessage {
	id: number | string;
	from?: string;
	sender_name?: string;
	subject?: string;
	body?: string;
	created_at?: string;
	read_at?: string | null;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE_URL}${path}`, {
		...init,
		headers: {
			"Content-Type": "application/json",
			Accept: "application/json",
			...init?.headers,
		},
	});

	let payload: unknown = null;
	try {
		payload = await res.json();
	} catch {
		// 非 JSON（网关错误页等），走下面的兜底文案
	}

	if (!res.ok) {
		const envelope = payload as Partial<Envelope<unknown>> | null;
		const kind = envelope?.kind;

		// 额度用满是这个来源最常见、也最需要引导用户的失败：
		// 这个邮箱在本月已经读不了了，但换一个来源或重新生成仍然可以。
		// 界面上不暴露服务商名称，只说「当前来源」。
		if (kind === "quota") {
			throw new Error(
				"当前来源的读取额度已用尽，可以换个域名重新生成，或稍后再试。",
			);
		}
		if (kind === "notfound") {
			throw new Error("该邮箱已被回收，请重新生成。");
		}
		if (res.status === 503 || kind === "auth") {
			throw new Error("临时邮箱服务未启用");
		}
		throw new Error(envelope?.message || `请求失败 (${res.status})`);
	}

	const envelope = payload as Envelope<T>;
	if (!envelope || envelope.success === false) {
		throw new Error(envelope?.message || "请求失败");
	}
	return envelope.data;
}

/** 读取可用域名。服务端未启用时返回空数组，前端据此隐藏入口。 */
export async function getDomains(): Promise<string[]> {
	const data = await request<string[]>("/domains");
	return Array.isArray(data) ? data : [];
}

/** 探活：nginx/vnproxy 没配 key 时这里失败，前端应该隐藏此来源。 */
export async function isAvailable(): Promise<boolean> {
	try {
		const res = await fetch(`${BASE_URL}/healthz`, {
			headers: { Accept: "application/json" },
		});
		return res.ok;
	} catch {
		return false;
	}
}

/** 创建邮箱。prefix 为空则服务端随机；domain 为空则服务端随机挑一个。 */
export async function createMailbox(
	prefix?: string,
	domain?: string,
): Promise<string> {
	const data = await request<{ address: string }>("/create", {
		method: "POST",
		body: JSON.stringify({ prefix: prefix || "", domain: domain || "" }),
	});
	if (!data?.address) throw new Error("服务端未返回邮箱地址");
	return data.address;
}

function stripTags(html: string): string {
	return html
		.replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ")
		.replace(/<[^>]+>/g, " ")
		.replace(/\s+/g, " ")
		.trim();
}

function looksLikeHtml(body: string): boolean {
	return /<[a-z][\s\S]*>/i.test(body);
}

function toSummary(raw: RawMessage): MailMessage {
	const body = raw.body || "";
	const plain = looksLikeHtml(body) ? stripTags(body) : body;
	return {
		id: String(raw.id),
		subject: raw.subject || "",
		intro: plain.slice(0, 120),
		seen: Boolean(raw.read_at),
		createdAt: raw.created_at || new Date().toISOString(),
		from: { address: raw.from || "", name: raw.sender_name || "" },
	};
}

export async function getMessages(address: string): Promise<MailMessage[]> {
	const data = await request<RawMessage[]>(
		`/messages?address=${encodeURIComponent(address)}`,
	);
	return (data || []).map(toSummary);
}

export async function getMessage(
	address: string,
	messageId: string,
): Promise<MailMessageDetail> {
	const raw = await request<RawMessage>(
		`/message?address=${encodeURIComponent(address)}&id=${encodeURIComponent(messageId)}`,
	);
	const summary = toSummary(raw);
	const body = raw.body || "";
	const isHtml = looksLikeHtml(body);

	return {
		...summary,
		html: isHtml ? [body] : undefined,
		text: isHtml ? stripTags(body) : body,
	};
}

/** 主动删除邮箱。用户点「换一个」时可以顺手回收，省一个名额。 */
export async function deleteMailbox(address: string): Promise<void> {
	await request<{ deleted: boolean }>("/delete", {
		method: "POST",
		body: JSON.stringify({ address }),
	});
}
