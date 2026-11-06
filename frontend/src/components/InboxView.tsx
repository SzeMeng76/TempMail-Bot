// 独立阅读视图。
//
// 打开 ?inbox=地址 时渲染这个，而不是主页。
// 主页左侧那些控件（换一个 / 自定义前缀 / 域名下拉 / 恢复邮箱）对拿链接进来的人
// 全是噪音 —— 他已经有地址了，点「换一个」还会把链接顶掉。
//
// 这里只有收件箱本身：地址、复制、刷新、邮件列表、邮件详情。
// 不做已读状态（luuvan 上游不记录），所以列表项统一按未读样式渲染。

import { ArrowLeft, Inbox, Loader2, Mail, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { MailMessage, MailMessageDetail, MailboxSession } from "../lib/mailbox";
import { inboxLink } from "../lib/address";
import * as lv from "../lib/luuvan";
import { CopyButton } from "./CopyButton";

// luuvan 读信不消耗额度，可以安心轮询。5 秒比主页的 10 秒更跟手，
// 因为买家通常正盯着等验证码。
const POLL_INTERVAL_MS = 5_000;

function formatTime(iso: string): string {
	const date = new Date(iso);
	if (Number.isNaN(date.getTime())) return "";
	const now = new Date();
	const sameDay = date.toDateString() === now.toDateString();
	return sameDay
		? date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
		: date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

function buildSrcDoc(detail: MailMessageDetail): string {
	const content =
		(detail.html && detail.html.join("")) ||
		(detail.text ? detail.text.replace(/\n/g, "<br>") : "") ||
		"（无内容）";

	return `<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body { font-family: system-ui, sans-serif; line-height: 1.6; margin: 16px; color: #1f2937; word-wrap: break-word; }
  img { max-width: 100%; height: auto; }
  a { color: #2563eb; }
</style>
</head><body>${content}</body></html>`;
}

function DetailPanel({
	session,
	messageId,
	onBack,
}: {
	session: MailboxSession;
	messageId: string;
	onBack: () => void;
}) {
	const [detail, setDetail] = useState<MailMessageDetail | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		setDetail(null);
		setError(null);
		lv.getMessage(session.address, messageId)
			.then((data) => {
				if (!cancelled) setDetail(data);
			})
			.catch((err) => {
				if (!cancelled) {
					setError(err instanceof Error ? err.message : "加载邮件失败");
				}
			});
		return () => {
			cancelled = true;
		};
	}, [session.address, messageId]);

	return (
		<div className="flex flex-col h-full">
			<div className="flex items-center gap-2 px-4 py-3 border-b border-white/60 dark:border-white/10 shrink-0">
				<button
					type="button"
					onClick={onBack}
					className="p-1.5 rounded-md hover:bg-white/60 dark:hover:bg-white/10 text-slate-600 dark:text-slate-300 transition-colors"
				>
					<ArrowLeft className="w-4 h-4" />
				</button>
				<span className="text-sm text-slate-500 dark:text-slate-400">返回收件箱</span>
			</div>

			{error && (
				<div className="p-4 text-sm text-red-600 dark:text-red-400">{error}</div>
			)}

			{!detail && !error && (
				<div className="flex-1 flex items-center justify-center text-slate-400">
					<Loader2 className="w-5 h-5 animate-spin" />
				</div>
			)}

			{detail && (
				<>
					<div className="px-4 py-3 border-b border-white/60 dark:border-white/10 shrink-0">
						<h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 break-words">
							{detail.subject || "(无主题)"}
						</h2>
						<div className="mt-1 text-xs text-slate-500 dark:text-slate-400 space-y-0.5">
							<div>发件人：{detail.from?.address}</div>
							<div>时间：{new Date(detail.createdAt).toLocaleString("zh-CN")}</div>
						</div>
					</div>
					<iframe
						title="邮件内容"
						srcDoc={buildSrcDoc(detail)}
						sandbox=""
						className="flex-1 w-full border-0 bg-white"
					/>
				</>
			)}
		</div>
	);
}

export function InboxView({ address }: { address: string }) {
	const session: MailboxSession = { provider: "luuvan", address };

	const [messages, setMessages] = useState<MailMessage[]>([]);
	const [loading, setLoading] = useState(true);
	const [refreshing, setRefreshing] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [openId, setOpenId] = useState<string | null>(null);
	const [lastChecked, setLastChecked] = useState<Date | null>(null);
	const [linkCopied, setLinkCopied] = useState(false);

	// 轮询时用 ref 读最新的 openId，避免因为打开邮件而重建定时器。
	const openIdRef = useRef<string | null>(null);
	openIdRef.current = openId;

	const load = useCallback(
		async (silent: boolean) => {
			if (!silent) setLoading(true);
			else setRefreshing(true);
			try {
				const list = await lv.getMessages(address);
				setMessages(list);
				setError(null);
				setLastChecked(new Date());
			} catch (err) {
				// 静默刷新失败不要把已有的列表清掉，只保留上一次的错误提示。
				if (!silent) {
					setError(err instanceof Error ? err.message : "读取失败");
				}
			} finally {
				setLoading(false);
				setRefreshing(false);
			}
		},
		[address],
	);

	useEffect(() => {
		load(false);
	}, [load]);

	useEffect(() => {
		const timer = window.setInterval(() => {
			// 正在看某一封时也继续轮询，但不去打断阅读；
			// 列表在后台更新，返回时就能看到新的。
			load(true);
		}, POLL_INTERVAL_MS);
		return () => window.clearInterval(timer);
	}, [load]);

	const handleCopyLink = async () => {
		try {
			await navigator.clipboard.writeText(inboxLink(address));
			setLinkCopied(true);
			window.setTimeout(() => setLinkCopied(false), 2000);
		} catch {
			setLinkCopied(false);
		}
	};

	return (
		<div className="relative min-h-screen overflow-hidden">
			{/* 和主页一致的装饰背景 */}
			<div className="pointer-events-none fixed inset-0 -z-10">
				<div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-blue-400/30 dark:bg-blue-500/20 blur-3xl" />
				<div className="absolute top-1/3 -right-32 w-96 h-96 rounded-full bg-cyan-300/30 dark:bg-cyan-500/10 blur-3xl" />
				<div className="absolute bottom-0 left-1/4 w-96 h-96 rounded-full bg-purple-300/20 dark:bg-purple-500/10 blur-3xl" />
			</div>

			<div className="container mx-auto px-4 py-6 sm:py-10 max-w-3xl">
				<header className="text-center mb-6">
					<h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100 flex items-center justify-center gap-2">
						<Mail className="w-6 h-6 text-blue-600 dark:text-blue-400" />
						收件箱
					</h1>
				</header>

				{openId ? (
					<div className="rounded-2xl bg-white/70 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 overflow-hidden min-h-[32rem] flex flex-col">
						<DetailPanel
							session={session}
							messageId={openId}
							onBack={() => setOpenId(null)}
						/>
					</div>
				) : (
					<>
						{/* 地址栏：只读展示 + 复制 */}
						<div className="rounded-2xl bg-white/70 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 p-4 sm:p-5">
							<div className="text-xs text-slate-500 dark:text-slate-400 mb-2">
								你的邮箱地址
							</div>
							<div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
								<div className="flex-1 min-w-0 bg-white/70 dark:bg-black/20 border border-white/60 dark:border-white/10 rounded-lg px-4 py-2.5 font-mono text-sm text-slate-900 dark:text-slate-100 select-all break-all">
									{address}
								</div>
								<CopyButton text={address} />
							</div>

							<div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-3 text-xs text-slate-500 dark:text-slate-400">
								<button
									type="button"
									onClick={() => load(true)}
									disabled={refreshing}
									className="inline-flex items-center gap-1.5 hover:text-blue-600 dark:hover:text-blue-400 disabled:opacity-50 transition-colors"
								>
									<RefreshCw
										className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`}
									/>
									刷新
								</button>
								<span className="text-slate-300 dark:text-slate-600">·</span>
								<button
									type="button"
									onClick={handleCopyLink}
									className="hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
								>
									{linkCopied ? "已复制链接" : "复制本页链接"}
								</button>
								<span className="text-slate-300 dark:text-slate-600">·</span>
								<span>
									{lastChecked
										? `每 5 秒自动刷新 · ${lastChecked.toLocaleTimeString("zh-CN", {
												hour: "2-digit",
												minute: "2-digit",
												second: "2-digit",
											})}`
										: "每 5 秒自动刷新"}
								</span>
							</div>
						</div>

						{error && (
							<div className="mt-4 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-sm text-red-600 dark:text-red-400">
								{error}
							</div>
						)}

						{/* 邮件列表 */}
						<div className="mt-4 rounded-2xl bg-white/70 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 overflow-hidden min-h-[18rem]">
							{loading ? (
								<div className="flex items-center justify-center py-20 text-slate-400">
									<Loader2 className="w-5 h-5 animate-spin" />
								</div>
							) : messages.length > 0 ? (
								messages.map((m, idx) => (
									<button
										key={m.id}
										type="button"
										onClick={() => setOpenId(m.id)}
										className="w-full text-left px-4 py-3.5 flex items-start gap-3 hover:bg-white/60 dark:hover:bg-white/5 transition-colors border-b border-white/60 dark:border-white/10 last:border-0"
									>
										<div className="mt-0.5 w-8 h-8 rounded-full bg-blue-500/15 text-blue-700 dark:text-blue-300 flex items-center justify-center text-xs font-semibold shrink-0">
											{idx + 1}
										</div>
										<div className="flex-1 min-w-0">
											<div className="flex items-baseline justify-between gap-2">
												<span className="text-sm font-semibold text-slate-900 dark:text-slate-100 truncate">
													{m.from?.address || "未知发件人"}
												</span>
												<span className="text-xs text-slate-400 dark:text-slate-500 shrink-0">
													{formatTime(m.createdAt)}
												</span>
											</div>
											<div className="text-sm text-slate-800 dark:text-slate-200 truncate">
												{m.subject || "(无主题)"}
											</div>
											{m.intro && (
												<div className="text-xs text-slate-400 dark:text-slate-500 truncate mt-0.5">
													{m.intro}
												</div>
											)}
										</div>
									</button>
								))
							) : (
								<div className="flex flex-col items-center justify-center py-20 px-6 text-center text-slate-400 dark:text-slate-500">
									<Inbox className="w-10 h-10 mb-3 opacity-60" />
									<p className="text-sm text-slate-600 dark:text-slate-300">
										等待邮件到达…
									</p>
									<p className="text-xs mt-1.5 leading-5">
										把这个地址填到需要验证的网站，
										<br />
										收到的邮件会自动出现在这里。
									</p>
								</div>
							)}
						</div>

						<p className="text-center text-xs text-slate-400 dark:text-slate-500 mt-6">
							本页面每 5 秒自动刷新，无需手动操作
						</p>
					</>
				)}
			</div>
		</div>
	);
}
