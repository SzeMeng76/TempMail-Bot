// mail.tm 客户端。返回类型收敛到 lib/mailbox.ts 的统一模型，组件不接触原始 JSON。

import type { MailMessage, MailMessageDetail } from "./mailbox";

const BASE_URL = "/api/mailtm";

export interface Domain {
	id: string;
	domain: string;
	isActive: boolean;
}

interface HydraCollection<T> {
	"hydra:member": T[];
}

// mail.tm 的邮件字段与统一模型接近，但 html 是数组、from 是对象，需要显式映射。
interface RawMessage {
	id: string;
	subject: string;
	intro: string;
	seen: boolean;
	createdAt: string;
	from: { address: string; name: string };
	text?: string;
	html?: string[];
}

function isHydraCollection<T>(value: unknown): value is HydraCollection<T> {
	return (
		typeof value === "object" &&
		value !== null &&
		"hydra:member" in value &&
		Array.isArray((value as HydraCollection<T>)["hydra:member"])
	);
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

	if (!res.ok) {
		let message = `请求失败 (${res.status})`;
		try {
			const body = await res.json();
			message = body["hydra:description"] || body.message || message;
		} catch {
			// ignore body parse failure
		}
		throw new Error(message);
	}

	return res.json() as Promise<T>;
}

function toSummary(raw: RawMessage): MailMessage {
	return {
		id: String(raw.id),
		subject: raw.subject || "",
		intro: raw.intro || "",
		seen: Boolean(raw.seen),
		createdAt: raw.createdAt,
		from: { address: raw.from?.address || "", name: raw.from?.name || "" },
	};
}

export async function getDomains(): Promise<Domain[]> {
	const data = await request<Domain[] | HydraCollection<Domain>>("/domains");
	return isHydraCollection<Domain>(data) ? data["hydra:member"] : data;
}

// 服务端会在规范化时改写地址（例如把 local part 里的点号去掉），
// 所以必须用它返回的地址，不能用本地拼接的那个去换 token。
export async function createAccount(
	address: string,
	password: string,
): Promise<string> {
	const data = await request<{ address?: string }>("/accounts", {
		method: "POST",
		body: JSON.stringify({ address, password }),
	});
	return data?.address || address;
}

export async function getToken(
	address: string,
	password: string,
): Promise<string> {
	const data = await request<{ token: string }>("/token", {
		method: "POST",
		body: JSON.stringify({ address, password }),
	});
	return data.token;
}

export async function getMessages(token: string): Promise<MailMessage[]> {
	const data = await request<RawMessage[] | HydraCollection<RawMessage>>(
		"/messages",
		{ headers: { Authorization: `Bearer ${token}` } },
	);
	const list = isHydraCollection<RawMessage>(data) ? data["hydra:member"] : data;
	return list.map(toSummary);
}

export async function getMessage(
	token: string,
	id: string,
): Promise<MailMessageDetail> {
	const raw = await request<RawMessage>(`/messages/${id}`, {
		headers: { Authorization: `Bearer ${token}` },
	});
	return {
		...toSummary(raw),
		text: raw.text,
		html: raw.html,
	};
}
