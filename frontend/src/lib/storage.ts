const STORAGE_KEY = "tempmail.mailbox";

export interface StoredMailbox {
	address: string;
	password: string;
}

export function loadMailbox(): StoredMailbox | null {
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) return null;
		const parsed = JSON.parse(raw);
		if (typeof parsed.address === "string" && typeof parsed.password === "string") {
			return parsed;
		}
		return null;
	} catch {
		return null;
	}
}

export function saveMailbox(mailbox: StoredMailbox): void {
	localStorage.setItem(STORAGE_KEY, JSON.stringify(mailbox));
}

export function clearMailbox(): void {
	localStorage.removeItem(STORAGE_KEY);
}
