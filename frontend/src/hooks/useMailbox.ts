import { useCallback, useEffect, useRef, useState } from "react";
import {
	type DomainOption,
	type MailboxSession,
	type MailMessage,
	type Provider,
} from "../lib/mailbox";
import * as mailtm from "../lib/mailtm";
import * as tmvn from "../lib/tempmailedu";
import * as lv from "../lib/luuvan";
import { generatePassword, generateUsername } from "../lib/generate";
import { clearMailbox, loadMailbox, saveMailbox } from "../lib/storage";
import { providerForAddress, readInboxParam } from "../lib/address";

// mail.tm 没有读信额度上限，可以放心轮询。
// tempmail.id.vn 免费版只有 900 次读/月，绝不能轮询，只能手动刷新。
const POLL_INTERVAL_MS = 10_000;

interface MailboxState {
	session: MailboxSession | null;
	messages: MailMessage[];
	loading: boolean;
	refreshing: boolean;
	error: string | null;
}

export function useMailbox() {
	const [state, setState] = useState<MailboxState>({
		session: null,
		messages: [],
		loading: true,
		refreshing: false,
		error: null,
	});

	// 可选域名池：两个来源的域名混在一起，界面上不区分来源。
	const [domains, setDomains] = useState<DomainOption[]>([]);
	const pollRef = useRef<number | null>(null);
	const tokenRef = useRef<string | null>(null);

	// 汇总两个来源的可用域名。tempmail.id.vn 没配 key 时只返回 mail.tm 的。
	const loadDomains = useCallback(async (): Promise<DomainOption[]> => {
		const [tm, vn, lvv] = await Promise.allSettled([
			mailtm.getDomains(),
			tmvn.getDomains(),
			lv.getDomains(),
		]);

		const options: DomainOption[] = [];
		if (tm.status === "fulfilled") {
			for (const d of tm.value) {
				if (d.isActive) options.push({ value: d.domain, provider: "mailtm" });
			}
		}
		if (vn.status === "fulfilled") {
			for (const domain of vn.value) {
				options.push({ value: domain, provider: "tempmailedu" });
			}
		}
		if (lvv.status === "fulfilled") {
			for (const domain of lvv.value) {
				options.push({ value: domain, provider: "luuvan" });
			}
		}
		return options;
	}, []);

	useEffect(() => {
		let cancelled = false;
		loadDomains().then((list) => {
			if (!cancelled) setDomains(list);
		});
		return () => {
			cancelled = true;
		};
	}, [loadDomains]);

	const fetchMessages = useCallback(
		async (session: MailboxSession): Promise<MailMessage[]> => {
			if (session.provider === "tempmailedu") {
				return tmvn.getMessages(session.address);
			}
			if (session.provider === "luuvan") {
				return lv.getMessages(session.address);
			}
			if (!tokenRef.current) {
				if (!session.password) throw new Error("缺少登录凭证");
				tokenRef.current = await mailtm.getToken(
					session.address,
					session.password,
				);
			}
			return mailtm.getMessages(tokenRef.current);
		},
		[],
	);

	const openSession = useCallback(
		async (session: MailboxSession): Promise<void> => {
			tokenRef.current = null;
			const messages = await fetchMessages(session);
			saveMailbox(session);
			setState((prev) => ({ ...prev, session, messages, error: null }));
		},
		[fetchMessages],
	);

	const createOn = useCallback(
		async (provider: Provider, prefix: string | undefined, domain: string | undefined) => {
			if (provider === "tempmailedu") {
				const address = await tmvn.createMailbox(prefix, domain);
				await openSession({ provider, address });
				return;
			}

			if (provider === "luuvan") {
				const created = await lv.createMailbox(prefix, domain);
				await openSession({ provider, address: created.address });
				// 游客建号有 24 小时有效期，必须让用户知道，不然会以为能长期用。
				if (!created.viaKey) {
					setState((prev) => ({
						...prev,
						error: "该邮箱将在 24 小时后过期（未配置服务端密钥）。",
					}));
				}
				return;
			}

			const username = prefix || generateUsername();
			const password = generatePassword(16);
			// mail.tm 只支持它自己返回的域名，传了就校验，没传就用第一个可用域名。
			const list = await mailtm.getDomains();
			const active = list.find((d) => d.isActive) ?? list[0];
			if (!active) throw new Error("暂无可用域名，请稍后重试");
			if (domain && domain !== active.domain) {
				throw new Error(`该域名不可用，当前可用：${active.domain}`);
			}
			// 服务端可能改写前缀（例如去掉点号），后续一律用它返回的地址。
			const address = await mailtm.createAccount(
				`${username}@${active.domain}`,
				password,
			);
			await openSession({ provider, address, password });
		},
		[openSession],
	);

	/**
	 * 生成邮箱。
	 *
	 * 不选域名时在两个来源之间随机，用户看到的只是「又拿到了一个地址」。
	 * 选了具体域名时按域名反查它属于哪个来源。
	 */
	const generate = useCallback(
		async (domain?: string, prefix?: string) => {
			setState((prev) => ({ ...prev, loading: true, error: null }));
			try {
				const chosen = domain
					? domains.find((d) => d.value === domain)
					: domains[Math.floor(Math.random() * Math.max(domains.length, 1))];
				const provider: Provider = chosen?.provider ?? "mailtm";
				await createOn(provider, prefix?.trim() || undefined, chosen?.value);
			} catch (err) {
				setState((prev) => ({
					...prev,
					error: err instanceof Error ? err.message : "生成邮箱失败",
				}));
			} finally {
				setState((prev) => ({ ...prev, loading: false }));
			}
		},
		[domains, createOn],
	);

	/**
	 * 恢复已有邮箱。
	 *
	 * 填密码 → 按 mail.tm 处理；不填密码 → 地址就是凭证。
	 * 不填密码时按域名判断归属：luuvan 的地址任何情况下都能直接读，
	 * 剩下的按 tempmail.id.vn 处理（服务端会校验它还在不在池子里）。
	 */
	const restore = useCallback(
		async (address: string, password: string) => {
			setState((prev) => ({ ...prev, loading: true, error: null }));
			try {
				if (password) {
					await openSession({ provider: "mailtm", address, password });
					return;
				}
				await openSession({
					provider: providerForAddress(address, domains),
					address,
				});
			} catch (err) {
				setState((prev) => ({
					...prev,
					error:
						err instanceof Error
							? err.message
							: "恢复失败，请检查地址和密码",
				}));
			} finally {
				setState((prev) => ({ ...prev, loading: false }));
			}
		},
		[openSession],
	);

	const forget = useCallback(() => {
		clearMailbox();
		tokenRef.current = null;
		setState({
			session: null,
			messages: [],
			loading: false,
			refreshing: false,
			error: null,
		});
	}, []);

	const refresh = useCallback(
		async (silent = false) => {
			const session = state.session;
			if (!session) return;
			setState((prev) => ({ ...prev, refreshing: !silent }));
			try {
				const messages = await fetchMessages(session);
				setState((prev) => ({
					...prev,
					messages,
					refreshing: false,
					error: null,
				}));
			} catch (err) {
				setState((prev) => ({
					...prev,
					refreshing: false,
					error: silent
						? prev.error
						: err instanceof Error
							? err.message
							: "刷新失败",
				}));
			}
		},
		[state.session, fetchMessages],
	);

	// 初次加载，优先级：URL 里的 ?inbox=地址 > 本地保存的邮箱 > 新生成一个。
	//
	// ?inbox= 是发给买家的直连链接：地址本身就能读，不需要密码也不需要恢复码。
	// 这条路径不写 localStorage —— 打开别人的链接不该覆盖自己正在用的邮箱。
	useEffect(() => {
		const fromUrl = readInboxParam();

		if (fromUrl) {
			openSession({ provider: providerForAddress(fromUrl, domains), address: fromUrl })
				.catch(() => generate())
				.finally(() => setState((prev) => ({ ...prev, loading: false })));
			return;
		}

		const stored = loadMailbox();
		if (stored) {
			openSession(stored)
				.catch(() => generate())
				.finally(() => setState((prev) => ({ ...prev, loading: false })));
			return;
		}
		generate();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	// 只有 mail.tm 轮询；vn 的额度撑不住。
	useEffect(() => {
		const session = state.session;
		if (!session || session.provider !== "mailtm") return;

		pollRef.current = window.setInterval(() => {
			refresh(true);
		}, POLL_INTERVAL_MS);

		return () => {
			if (pollRef.current) window.clearInterval(pollRef.current);
		};
	}, [state.session, refresh]);

	return {
		...state,
		domains,
		generate,
		restore,
		forget,
		refresh: () => refresh(false),
	};
}
