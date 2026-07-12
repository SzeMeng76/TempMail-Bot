import { useCallback, useEffect, useRef, useState } from "react";
import {
	createAccount,
	getDomains,
	getMessages,
	getToken,
	type MessageSummary,
} from "../lib/mailtm";
import { generatePassword, generateUsername } from "../lib/generate";
import { clearMailbox, loadMailbox, saveMailbox } from "../lib/storage";

const POLL_INTERVAL_MS = 10_000;

interface MailboxState {
	address: string | null;
	password: string | null;
	token: string | null;
	messages: MessageSummary[];
	loading: boolean;
	refreshing: boolean;
	error: string | null;
}

export function useMailbox() {
	const [state, setState] = useState<MailboxState>({
		address: null,
		password: null,
		token: null,
		messages: [],
		loading: true,
		refreshing: false,
		error: null,
	});

	const pollRef = useRef<number | null>(null);

	const authenticate = useCallback(
		async (address: string, password: string) => {
			const token = await getToken(address, password);
			setState((prev) => ({ ...prev, address, password, token, error: null }));
			saveMailbox({ address, password });
			return token;
		},
		[],
	);

	const generate = useCallback(async () => {
		setState((prev) => ({ ...prev, loading: true, error: null }));
		try {
			const domains = await getDomains();
			const active = domains.find((d) => d.isActive) ?? domains[0];
			if (!active) throw new Error("暂无可用域名，请稍后重试");

			const username = generateUsername();
			const password = generatePassword();
			const address = `${username}@${active.domain}`;

			await createAccount(address, password);
			await authenticate(address, password);
		} catch (err) {
			setState((prev) => ({
				...prev,
				error: err instanceof Error ? err.message : "生成邮箱失败",
			}));
		} finally {
			setState((prev) => ({ ...prev, loading: false }));
		}
	}, [authenticate]);

	const restore = useCallback(
		async (address: string, password: string) => {
			setState((prev) => ({ ...prev, loading: true, error: null }));
			try {
				await authenticate(address, password);
			} catch {
				setState((prev) => ({ ...prev, error: "邮箱地址或密码错误" }));
			} finally {
				setState((prev) => ({ ...prev, loading: false }));
			}
		},
		[authenticate],
	);

	const forget = useCallback(() => {
		clearMailbox();
		setState({
			address: null,
			password: null,
			token: null,
			messages: [],
			loading: false,
			refreshing: false,
			error: null,
		});
	}, []);

	const refresh = useCallback(async (token: string, silent = false) => {
		setState((prev) => ({ ...prev, refreshing: !silent }));
		try {
			const messages = await getMessages(token);
			setState((prev) => ({ ...prev, messages, refreshing: false }));
		} catch {
			setState((prev) => ({ ...prev, refreshing: false }));
		}
	}, []);

	// 初次加载：尝试恢复已保存的邮箱，否则自动生成一个
	useEffect(() => {
		const stored = loadMailbox();
		if (stored) {
			authenticate(stored.address, stored.password)
				.catch(() => generate())
				.finally(() => setState((prev) => ({ ...prev, loading: false })));
		} else {
			generate();
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	// 邮箱就位后开始轮询收件箱
	useEffect(() => {
		if (!state.token) return;

		refresh(state.token, true);

		pollRef.current = window.setInterval(() => {
			if (state.token) refresh(state.token, true);
		}, POLL_INTERVAL_MS);

		return () => {
			if (pollRef.current) window.clearInterval(pollRef.current);
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [state.token]);

	return {
		...state,
		generate,
		restore,
		forget,
		refresh: () => state.token && refresh(state.token),
	};
}
