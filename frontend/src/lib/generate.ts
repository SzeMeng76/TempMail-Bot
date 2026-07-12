const USERNAME_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789";
const PASSWORD_CHARS =
	"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

function randomString(chars: string, length: number): string {
	let result = "";
	for (let i = 0; i < length; i++) {
		result += chars[Math.floor(Math.random() * chars.length)];
	}
	return result;
}

export function generateUsername(length = 10): string {
	return randomString(USERNAME_CHARS, length);
}

export function generatePassword(length = 16): string {
	return randomString(PASSWORD_CHARS, length);
}
