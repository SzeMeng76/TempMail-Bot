// luuvan.site 客户端。
//
// 和其他两个来源一样，浏览器只跟本站的 /api/vn/lv/... 打交道：
// 建号用的 API key 是账号级凭证，绝不能进前端包。读信本身虽然不需要 key，
// 但对方站点没有返回 CORS 头，浏览器直连会被拦，所以也走中转。
//
// 这个来源最特别的地方：地址本身就是读信凭证（服务端是 catch-all）。
// 不需要恢复码、不需要 token，地址发出去就能读 —— 发卡密就是靠这一点。

import type { MailMessage, MailMessageDetail } from "./mailbox";

const BASE_URL = "/api/vn/lv";

interface Envelope<T> {
	success: boolean;
	message: string;
	kind?: "quota" | "notfound" | "auth" | "other";
	data: T;
}

interface RawMessage {
	id: string;
	from?: string;
	subject?: string;
	received_at?: string;
	intro?: string;
}

interface RawDetail extends RawMessage {
	text?: string;
	html?: string;
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
		// 非 JSON（网关错误页），走下面的兜底文案
	}

	if (!res.ok) {
		const envelope = payload as Partial<Envelope<unknown>> | null;
		const kind = envelope?.kind;

		if (kind === "quota") {
			throw new Error("创建额度已用完，可以稍后再试，或换个来源生成。");
		}
		if (kind === "notfound") {
			throw new Error("该邮箱不存在。");
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

/** 域名列表。读信不需要 key，所以这个来源永远可用。 */
export async function getDomains(): Promise<string[]> {
	const data = await request<string[]>("/domains");
	return Array.isArray(data) ? data : [];
}

export interface CreatedMailbox {
	address: string;
	/** 游客建号只有 24 小时；有 key 时是一百年后。 */
	expiresAt: string;
	/** false 表示走的是游客额度，需要提醒用户邮箱会过期。 */
	viaKey: boolean;
}

export async function createMailbox(
	prefix?: string,
	domain?: string,
): Promise<CreatedMailbox> {
	const data = await request<CreatedMailbox>("/create", {
		method: "POST",
		body: JSON.stringify({ prefix: prefix || "", domain: domain || "" }),
	});
	if (!data?.address) throw new Error("服务端未返回邮箱地址");
	return data;
}

function stripTags(html: string): string {
	return html
		.replace(/<(script|style)[\s\S]*?<\/\1>/gi, " ")
		.replace(/<[^>]+>/g, " ")
		.replace(/\s+/g, " ")
		.trim();
}

function toSummary(raw: RawMessage): MailMessage {
	return {
		id: String(raw.id),
		subject: raw.subject || "",
		intro: raw.intro || "",
		// 这个来源不记录已读状态，统一按未读展示。
		seen: false,
		createdAt: raw.received_at || new Date().toISOString(),
		from: { address: raw.from || "", name: "" },
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
	const raw = await request<RawDetail>(
		`/message?address=${encodeURIComponent(address)}&id=${encodeURIComponent(messageId)}`,
	);
	const summary = toSummary(raw);
	const html = raw.html || "";
	const text = raw.text || "";

	// 正文可能只有 HTML、只有纯文本，或者两者都有；组件按 html 优先渲染。
	return {
		...summary,
		html: html ? [html] : undefined,
		text: html ? stripTags(html) : text,
	};
}
