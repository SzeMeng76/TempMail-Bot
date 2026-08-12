const BASE_URL = "/api/mailtm";

export interface Domain {
	id: string;
	domain: string;
	isActive: boolean;
}

export interface MessageSummary {
	id: string;
	subject: string;
	intro: string;
	seen: boolean;
	createdAt: string;
	from: { address: string; name: string };
}

export interface MessageDetail extends MessageSummary {
	text?: string;
	html?: string[];
}

interface HydraCollection<T> {
	"hydra:member": T[];
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

export async function getDomains(): Promise<Domain[]> {
	const data = await request<Domain[] | HydraCollection<Domain>>("/domains");
	return isHydraCollection<Domain>(data) ? data["hydra:member"] : data;
}

export async function createAccount(
	address: string,
	password: string,
): Promise<void> {
	await request("/accounts", {
		method: "POST",
		body: JSON.stringify({ address, password }),
	});
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

export async function getMessages(token: string): Promise<MessageSummary[]> {
	const data = await request<MessageSummary[] | HydraCollection<MessageSummary>>(
		"/messages",
		{ headers: { Authorization: `Bearer ${token}` } },
	);
	return isHydraCollection<MessageSummary>(data) ? data["hydra:member"] : data;
}

export async function getMessage(
	token: string,
	id: string,
): Promise<MessageDetail> {
	return request<MessageDetail>(`/messages/${id}`, {
		headers: { Authorization: `Bearer ${token}` },
	});
}
