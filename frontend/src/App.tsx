import { ChevronDown, Link2, Mail, RefreshCw, RotateCcw } from "lucide-react";
import { useState } from "react";
import { CopyButton } from "./components/CopyButton";
import { Faq } from "./components/Faq";
import { Features } from "./components/Features";
import { Footer } from "./components/Footer";
import { HowItWorks } from "./components/HowItWorks";
import { MessageDetail } from "./components/MessageDetail";
import { MessageItem } from "./components/MessageItem";
import { MessageSkeleton } from "./components/MessageSkeleton";
import { Navbar } from "./components/Navbar";
import { InboxView } from "./components/InboxView";
import { useMailbox } from "./hooks/useMailbox";
import { inboxLink, readInboxParam } from "./lib/address";

function RestoreForm({
	onRestore,
}: {
	onRestore: (address: string, password: string) => void;
}) {
	const [address, setAddress] = useState("");
	const [password, setPassword] = useState("");
	// 两种恢复方式：带凭证的（地址+密码）和仅凭地址的。
	// 界面上不写服务商名称，只用中性的说法描述。
	const [mode, setMode] = useState<"credential" | "address">("credential");

	return (
		<form
			onSubmit={(e) => {
				e.preventDefault();
				if (address) onRestore(address.trim(), mode === "credential" ? password : "");
			}}
			className="space-y-2"
		>
			<div className="flex gap-1 p-1 rounded-lg bg-white/40 dark:bg-black/20 border border-white/60 dark:border-white/10">
				<button
					type="button"
					onClick={() => setMode("credential")}
					className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
						mode === "credential"
							? "bg-blue-600 text-white shadow-sm"
							: "text-slate-600 dark:text-slate-300 hover:bg-white/60 dark:hover:bg-white/10"
					}`}
				>
					地址 + 密码
				</button>
				<button
					type="button"
					onClick={() => setMode("address")}
					className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
						mode === "address"
							? "bg-blue-600 text-white shadow-sm"
							: "text-slate-600 dark:text-slate-300 hover:bg-white/60 dark:hover:bg-white/10"
					}`}
				>
					仅地址
				</button>
			</div>

			<div className="flex flex-col sm:flex-row gap-2">
				<input
					type="email"
					required
					placeholder="邮箱地址"
					value={address}
					onChange={(e) => setAddress(e.target.value)}
					className="flex-1 px-3 py-2 rounded-lg text-sm bg-white/60 dark:bg-white/5 border border-white/40 dark:border-white/10 placeholder:text-slate-400 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
				/>
				<button
					type="submit"
					className="px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap bg-blue-600/10 dark:bg-blue-400/10 text-blue-700 dark:text-blue-300 border border-blue-500/30 hover:bg-blue-600/20 dark:hover:bg-blue-400/20 transition-colors"
				>
					恢复邮箱
				</button>
			</div>

			{mode === "credential" && (
				<input
					type="password"
					required
					placeholder="密码"
					value={password}
					onChange={(e) => setPassword(e.target.value)}
					className="w-full px-3 py-2 rounded-lg text-sm bg-white/60 dark:bg-white/5 border border-white/40 dark:border-white/10 placeholder:text-slate-400 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/60"
				/>
			)}

			<p className="text-xs text-slate-400 dark:text-slate-500 leading-5">
				{mode === "credential"
					? "适用于生成时给过密码的邮箱。"
					: "适用于不需要密码的邮箱，只要地址还在就能打开。"}
			</p>
		</form>
	);
}

export default function App() {
	// 带 ?inbox= 进来的是买家/收件人，他们只需要看信，不该看到任何建号控件。
	// 这个判断必须在 useMailbox 之前 —— 否则会白白生成一个邮箱。
	const inboxAddress = readInboxParam();
	if (inboxAddress) {
		return <InboxView address={inboxAddress} />;
	}

	return <HomePage />;
}

function HomePage() {
	const mailbox = useMailbox();
	const [openMessageId, setOpenMessageId] = useState<string | null>(null);
	const [showRestore, setShowRestore] = useState(false);

	const [domain, setDomain] = useState("");
	const [prefix, setPrefix] = useState("");
	const [linkCopied, setLinkCopied] = useState(false);

	const unreadCount = mailbox.messages.filter((m) => !m.seen).length;

	const handleGenerate = () => {
		setOpenMessageId(null);
		mailbox.generate(domain || undefined, prefix.trim() || undefined);
	};

	// 直连链接是给买家/收件人用的：打开就进这个收件箱，不用密码也不用恢复码。
	const handleCopyInboxLink = async () => {
		const address = mailbox.session?.address;
		if (!address) return;
		try {
			await navigator.clipboard.writeText(inboxLink(address));
			setLinkCopied(true);
			window.setTimeout(() => setLinkCopied(false), 2000);
		} catch {
			// 非 HTTPS 或浏览器拒绝时退回让用户手动选中地址。
			setLinkCopied(false);
		}
	};

	return (
		<div id="top" className="relative min-h-screen overflow-hidden">
			{/* 装饰性渐变光斑背景 */}
			<div className="pointer-events-none fixed inset-0 -z-10">
				<div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-blue-400/30 dark:bg-blue-500/20 blur-3xl" />
				<div className="absolute top-1/3 -right-32 w-96 h-96 rounded-full bg-cyan-300/30 dark:bg-cyan-500/10 blur-3xl" />
				<div className="absolute bottom-0 left-1/4 w-96 h-96 rounded-full bg-purple-300/20 dark:bg-purple-500/10 blur-3xl" />
			</div>

			<Navbar />

			<main className="container mx-auto px-4 py-8 sm:py-12 max-w-6xl">
				<header className="text-center mb-8">
					<h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 flex items-center justify-center gap-2">
						<Mail className="w-7 h-7 text-blue-600 dark:text-blue-400" />
						临时邮箱
					</h1>
					<p className="text-slate-500 dark:text-slate-400 text-sm mt-2">
						无需注册，即时收取邮件，保护你的真实邮箱地址
					</p>
				</header>

				<div className="grid lg:grid-cols-2 gap-6">
					<div className="rounded-2xl bg-white/50 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 p-4 sm:p-6 h-full">
						{mailbox.loading ? (
							<div className="space-y-3 animate-pulse">
								<div className="h-11 rounded-lg bg-slate-200/70 dark:bg-white/10" />
								<div className="h-3 w-40 rounded bg-slate-200/70 dark:bg-white/10" />
							</div>
						) : (
							<>
								<div className="flex flex-col sm:flex-row items-center gap-3">
									<div className="flex-1 min-w-0 bg-white/70 dark:bg-black/20 border border-white/60 dark:border-white/10 rounded-lg px-4 py-2.5 font-mono text-sm text-slate-900 dark:text-slate-100 select-all break-all w-full">
										{mailbox.session?.address}
									</div>
									{mailbox.session?.address && (
										<CopyButton text={mailbox.session.address} />
									)}
								</div>

								<div className="flex items-center gap-2 mt-3">
									<button
										type="button"
										onClick={handleGenerate}
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
									{mailbox.session?.provider === "luuvan" && (
										<>
											<span className="text-slate-300 dark:text-slate-600">·</span>
											<button
												type="button"
												onClick={handleCopyInboxLink}
												className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
											>
												<Link2 className="w-3.5 h-3.5" />
												{linkCopied ? "已复制链接" : "复制直连链接"}
											</button>
										</>
									)}
								</div>

								{/* 不选就随机，选了就固定用那个后缀 */}
								<div className="mt-3 space-y-2">
									<input
										type="text"
										value={prefix}
										onChange={(e) => setPrefix(e.target.value)}
										disabled={mailbox.loading}
										maxLength={32}
										placeholder="自定义前缀（留空则随机）"
										className="w-full px-3 py-2 rounded-lg text-sm bg-white/60 dark:bg-white/5 border border-white/40 dark:border-white/10 placeholder:text-slate-400 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/60 disabled:opacity-50"
									/>

									{/* 只要拿到域名就显示选择器；只有一个时也显示，让用户清楚当前用的是哪个后缀 */}
									{mailbox.domains.length > 0 && (
										<div className="relative">
											<select
												value={domain}
												onChange={(e) => setDomain(e.target.value)}
												disabled={mailbox.loading}
												className="appearance-none w-full pl-3 pr-8 py-2 rounded-lg text-sm bg-white/60 dark:bg-white/5 border border-white/40 dark:border-white/10 text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/60 disabled:opacity-50"
											>
												<option value="">随机域名</option>
												{mailbox.domains.map((d) => (
													<option key={d.value} value={d.value}>
														{d.value}
													</option>
												))}
											</select>
											<ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
										</div>
									)}

									<p className="text-xs text-slate-400 dark:text-slate-500 leading-5">
										填前缀 + 固定域名可以重新打开之前建过的同一个地址。
									</p>
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

								<div className="mt-6 pt-6 border-t border-white/60 dark:border-white/10 grid grid-cols-3 gap-3 text-center">
									<div>
										<div className="text-lg font-bold text-blue-600 dark:text-blue-400">
											10s
										</div>
										<div className="text-xs text-slate-500 dark:text-slate-400">
											自动刷新
										</div>
									</div>
									<div>
										<div className="text-lg font-bold text-blue-600 dark:text-blue-400">
											免费
										</div>
										<div className="text-xs text-slate-500 dark:text-slate-400">
											无需注册
										</div>
									</div>
									<div>
										<div className="text-lg font-bold text-blue-600 dark:text-blue-400">
											开源
										</div>
										<div className="text-xs text-slate-500 dark:text-slate-400">
											可自行部署
										</div>
									</div>
								</div>
							</>
						)}
					</div>

					<div className="rounded-2xl bg-white/50 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 shadow-xl shadow-blue-900/5 overflow-hidden flex flex-col">
						<div className="flex items-center justify-between px-4 py-3 border-b border-white/60 dark:border-white/10 shrink-0">
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
								disabled={mailbox.refreshing || !mailbox.session}
								className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 disabled:opacity-50 transition-colors"
							>
								<RefreshCw
									className={`w-3.5 h-3.5 ${mailbox.refreshing ? "animate-spin" : ""}`}
								/>
								刷新
							</button>
						</div>

						<div className="flex-1 min-h-[26rem] overflow-y-auto">
							{openMessageId && mailbox.session ? (
								<MessageDetail
									session={mailbox.session}
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
				</div>

				<Features />
				<HowItWorks />
				<Faq />
			</main>

			<Footer />
		</div>
	);
}
