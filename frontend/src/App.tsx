import { Loader2, Mail, RefreshCw, RotateCcw } from "lucide-react";
import { useState } from "react";
import { CopyButton } from "./components/CopyButton";
import { MessageDetail } from "./components/MessageDetail";
import { MessageItem } from "./components/MessageItem";
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
				className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			<input
				type="password"
				required
				placeholder="密码"
				value={password}
				onChange={(e) => setPassword(e.target.value)}
				className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
			/>
			<button
				type="submit"
				className="px-4 py-2 rounded-md border border-blue-300 text-blue-700 text-sm font-medium hover:bg-blue-50 transition-colors whitespace-nowrap"
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
		<div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-blue-50">
			<main className="container mx-auto px-4 py-8 max-w-3xl">
				<header className="text-center mb-8">
					<h1 className="text-3xl font-bold text-gray-800 flex items-center justify-center gap-2">
						<Mail className="w-7 h-7 text-blue-600" />
						临时邮箱
					</h1>
					<p className="text-gray-500 text-sm mt-2">
						无需注册，即时收取邮件，保护你的真实邮箱地址
					</p>
				</header>

				<div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-6 mb-6">
					{mailbox.loading ? (
						<div className="flex items-center justify-center gap-2 text-gray-500 py-4">
							<Loader2 className="w-5 h-5 animate-spin" />
							正在生成临时邮箱...
						</div>
					) : (
						<>
							<div className="flex flex-col sm:flex-row items-center gap-3">
								<div className="flex-1 min-w-0 bg-gray-50 border border-gray-200 rounded-lg px-4 py-2.5 font-mono text-sm text-gray-900 select-all break-all w-full">
									{mailbox.address}
								</div>
								{mailbox.address && <CopyButton text={mailbox.address} />}
							</div>

							<div className="flex items-center gap-2 mt-3">
								<button
									type="button"
									onClick={() => mailbox.generate()}
									className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-blue-600 transition-colors"
								>
									<RotateCcw className="w-3.5 h-3.5" />
									换一个
								</button>
								<span className="text-gray-300">·</span>
								<button
									type="button"
									onClick={() => setShowRestore((v) => !v)}
									className="text-xs text-gray-600 hover:text-blue-600 transition-colors"
								>
									恢复已有邮箱
								</button>
							</div>

							{showRestore && (
								<div className="mt-3 pt-3 border-t border-gray-100">
									<RestoreForm
										onRestore={(addr, pwd) => {
											mailbox.restore(addr, pwd);
											setShowRestore(false);
										}}
									/>
								</div>
							)}

							{mailbox.error && (
								<p className="text-red-500 text-xs mt-2">{mailbox.error}</p>
							)}
						</>
					)}
				</div>

				<div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
					<div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
						<div className="flex items-center gap-2">
							<span className="font-semibold text-gray-800">收件箱</span>
							{unreadCount > 0 && (
								<span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full">
									{unreadCount} 未读
								</span>
							)}
						</div>
						<button
							type="button"
							onClick={() => mailbox.refresh()}
							disabled={mailbox.refreshing || !mailbox.token}
							className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:text-blue-600 disabled:opacity-50 transition-colors"
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
						) : mailbox.messages.length > 0 ? (
							mailbox.messages.map((m) => (
								<MessageItem
									key={m.id}
									message={m}
									onClick={() => setOpenMessageId(m.id)}
								/>
							))
						) : (
							<div className="flex flex-col items-center justify-center h-full text-gray-400 px-4">
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
