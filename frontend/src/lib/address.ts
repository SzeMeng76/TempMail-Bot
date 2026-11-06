// 地址相关的纯函数。主页和独立阅读视图都要用，所以单独放这里。

import type { DomainOption, Provider } from "./mailbox";

// luuvan 的域名兜底表：域名列表还没加载出来（或请求失败）时也能判断归属。
// 和 bot 侧 luuvan.py 的 _LUUVAN_FALLBACK_DOMAINS 保持一致。
export const LUUVAN_FALLBACK_DOMAINS = [
	"n0ai.cloud",
	"animee.tokyo",
	"vibecoder.io.vn",
	"luuvan.site",
	"luuvan.online",
	"lhuniverse.io.vn",
	"locpnv.click",
];

/**
 * 按域名判断一个地址属于哪个来源。
 *
 * luuvan 的地址任何时候都能直接读（服务端 catch-all），
 * 其余地址交给 tempmail.id.vn（服务端会校验它还在不在池子里）。
 */
export function providerForAddress(
	address: string,
	domains: DomainOption[] = [],
): Provider {
	const domain = address.split("@").pop()?.toLowerCase() ?? "";
	if (!domain) return "tempmailedu";

	const known = domains.filter((d) => d.provider === "luuvan").map((d) => d.value);
	const candidates = known.length > 0 ? known : LUUVAN_FALLBACK_DOMAINS;

	const isLuuvan = candidates.some(
		(d) => domain === d || domain.endsWith(`.${d}`),
	);
	return isLuuvan ? "luuvan" : "tempmailedu";
}

/** 从 URL 里读 ?inbox= 参数，只接受看起来像邮箱地址的值。 */
export function readInboxParam(): string | null {
	if (typeof window === "undefined") return null;
	const value = new URLSearchParams(window.location.search).get("inbox");
	if (!value) return null;
	const address = value.trim().toLowerCase();
	return /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/.test(address) ? address : null;
}

/** 生成给买家的直连链接。 */
export function inboxLink(address: string): string {
	if (typeof window === "undefined") return `?inbox=${encodeURIComponent(address)}`;
	const url = new URL(window.location.href);
	url.search = "";
	url.searchParams.set("inbox", address);
	return url.toString();
}
