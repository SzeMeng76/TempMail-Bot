import { Mail, RefreshCw, RotateCcw } from "lucide-react";
import { useState } from "react";
import { CopyButton } from "./components/CopyButton";
import { CredentialField } from "./components/CredentialField";
import { MessageDetail } from "./components/MessageDetail";
import { MessageItem } from "./components/MessageItem";
import { MessageSkeleton } from "./components/MessageSkeleton";
import { useMailbox } from "./hooks/useMailbox";

function RestoreForm({
	onRestore,
}: {
	onRestore: (address: string, password: string) => void;
}) {
	const [address, setAddress] = useState("");
	const [password, setPassword] = useState("");

	return (
		<form
			onSubmit={(e) => {
				e.preventDefault();
				if (address && password) onRestore(address.trim(), password);
			}}
			className="flex flex-col sm:flex-row gap-2"
		>
			<input
				type="email"
				required
				placeholder="邮箱地址"
				value={address}
				onChange={(e) => setAddress(e.target.value)}
				className="flex-1 px-3 py-2 rounded-lg text-sm bg-white/60 dark:bg-white/5 border border-white/40 dark:border-white/10 placeholder:text-slate-400 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
			/>
			<input
				type="password"
				required
				placeholder="密码"
				value={password}
				onChange={(e) => setPassword(e.target.value)}
				className="flex-1 px-3 py-2 rounded-lg text-sm bg-white/60 dark:bg-white/5 border border-white/40 dark:border-white/10 placeholder:text-slate-400 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
			/>
			<button
				type="submit"
				className="px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap bg-blue-600/10 dark:bg-blue-400/10 text-blue-700 dark:text-blue-300 border border-blue-500/30 hover:bg-blue-600/20 dark:hover:bg-blue-400/20 transition-colors"
			>
				恢复邮箱
			</button>
		</form>
	);
}

export default function App() {
	const mailbox = useMailbox();
	const [openMessageId, setOpenMessageId] = useState<string | null>(null);
	const [showRestore, setShowRestore] = useState(false);

	const unreadCount = mailbox.messages.filter((m) => !m.seen).length;

	return (
		<div className="relative min-h-screen overflow-hidden">
			{/* 装饰性渐变光斑背景 */}
			<div className="pointer-events-none fixed inset-0 -z-10">
				<div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-blue-400/30 dark:bg-blue-500/20 blur-3xl" />
				<div className="absolute top-1/3 -right-32 w-96 h-96 rounded-full bg-cyan-300/30 dark:bg-cyan-500/10 blur-3xl" />
				<div className="absolute bottom-0 left-1/4 w-96 h-96 rounded-full bg-purple-300/20 dark:bg-purple-500/10 blur-3xl" />
			</div>

			<main className="container mx-auto px-4 py-8 sm:py-12 max-w-3xl">
				<header className="text-center mb-8">
					<h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 flex items-center justify-center gap-2">
						<Mail className="w-7 h-7 text-blue-600 dark:text-blue-400" />
						临时邮箱
					</h1>
					<p className="text-slate-500 dark:text-slate-400 text-sm mt-2">
						无需注册，即时收取邮件，保护你的真实邮箱地址
					</p>
				</header>

				<div className="rounded-2xl bg-white/50 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 p-4 sm:p-6 mb-6">
					{mailbox.loading ? (
						<div className="space-y-3 animate-pulse">
							<div className="h-11 rounded-lg bg-slate-200/70 dark:bg-white/10" />
							<div className="h-3 w-40 rounded bg-slate-200/70 dark:bg-white/10" />
						</div>
					) : (
						<>
							<div className="flex flex-col sm:flex-row items-center gap-3">
								<div className="flex-1 min-w-0 bg-white/70 dark:bg-black/20 border border-white/60 dark:border-white/10 rounded-lg px-4 py-2.5 font-mono text-sm text-slate-900 dark:text-slate-100 select-all break-all w-full">
									{mailbox.address}
								</div>
								{mailbox.address && <CopyButton text={mailbox.address} />}
							</div>

							{mailbox.password && (
								<div className="mt-2 space-y-2">
									<CredentialField label="密码" value={mailbox.password} mask />
									{mailbox.token && (
										<CredentialField label="令牌" value={mailbox.token} mask />
									)}
								</div>
							)}

							<div className="flex items-center gap-2 mt-3">
								<button
									type="button"
									onClick={() => mailbox.generate()}
									className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
								>
									<RotateCcw className="w-3.5 h-3.5" />
									换一个
								</button>
								<span className="text-slate-300 dark:text-slate-600">·</span>
								<button
									type="button"
									onClick={() => setShowRestore((v) => !v)}
									className="text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
								>
									恢复已有邮箱
								</button>
							</div>

							{showRestore && (
								<div className="mt-3 pt-3 border-t border-white/60 dark:border-white/10">
									<RestoreForm
										onRestore={(addr, pwd) => {
											mailbox.restore(addr, pwd);
											setShowRestore(false);
										}}
									/>
								</div>
							)}

							{mailbox.error && (
								<p className="text-red-500 dark:text-red-400 text-xs mt-2">
									{mailbox.error}
								</p>
							)}
						</>
					)}
				</div>

				<div className="rounded-2xl bg-white/50 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 overflow-hidden">
					<div className="flex items-center justify-between px-4 py-3 border-b border-white/60 dark:border-white/10">
						<div className="flex items-center gap-2">
							<span className="font-semibold text-slate-800 dark:text-slate-100">
								收件箱
							</span>
							{unreadCount > 0 && (
								<span className="bg-blue-500/15 text-blue-700 dark:text-blue-300 text-xs px-2 py-0.5 rounded-full">
									{unreadCount} 未读
								</span>
							)}
						</div>
						<button
							type="button"
							onClick={() => mailbox.refresh()}
							disabled={mailbox.refreshing || !mailbox.token}
							className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 disabled:opacity-50 transition-colors"
						>
							<RefreshCw
								className={`w-3.5 h-3.5 ${mailbox.refreshing ? "animate-spin" : ""}`}
							/>
							刷新
						</button>
					</div>

					<div className="h-[26rem] overflow-y-auto">
						{openMessageId ? (
							<MessageDetail
								token={mailbox.token!}
								messageId={openMessageId}
								onBack={() => setOpenMessageId(null)}
							/>
						) : mailbox.loading ? (
							<MessageSkeleton />
						) : mailbox.messages.length > 0 ? (
							mailbox.messages.map((m) => (
								<MessageItem
									key={m.id}
									message={m}
									onClick={() => setOpenMessageId(m.id)}
								/>
							))
						) : (
							<div className="flex flex-col items-center justify-center h-full text-slate-400 dark:text-slate-500 px-4">
								<div className="text-4xl mb-3">📭</div>
								<p className="text-sm">收件箱为空</p>
								<p className="text-xs mt-1">收件箱每 10 秒自动刷新</p>
							</div>
						)}
					</div>
				</div>
			</main>
		</div>
	);
}
