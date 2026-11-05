import type { MailboxSession, Provider } from "./mailbox";

const STORAGE_KEY = "tempmail.mailbox";

// v1 只存过 mail.tm 的 { address, password }，没有 provider 字段。
// 读到旧结构时补成 mailtm，保证老用户刷新页面还能恢复原邮箱。
function migrate(parsed: unknown): MailboxSession | null {
	if (typeof parsed !== "object" || parsed === null) return null;
	const raw = parsed as Record<string, unknown>;
	if (typeof raw.address !== "string" || !raw.address) return null;

	const provider: Provider =
		raw.provider === "tempmailedu" ? "tempmailedu" : "mailtm";

	if (provider === "tempmailedu") {
		// tempmail.id.vn 不需要密码，地址本身就是全部凭证。
		return { provider, address: raw.address };
	}

	if (typeof raw.password !== "string") return null;
	return { provider, address: raw.address, password: raw.password };
}

export function loadMailbox(): MailboxSession | null {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return null;
		return migrate(JSON.parse(raw));
	} catch {
		return null;
	}
}

export function saveMailbox(session: MailboxSession): void {
	localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearMailbox(): void {
	localStorage.removeItem(STORAGE_KEY);
}
