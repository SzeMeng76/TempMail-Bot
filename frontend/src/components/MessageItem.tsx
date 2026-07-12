import type { MessageSummary } from "../lib/mailtm";

function formatTime(iso: string): string {
	const date = new Date(iso);
	const now = new Date();
	const sameDay = date.toDateString() === now.toDateString();
	return sameDay
		? date.toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
		: date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}

export function MessageItem({
	message,
	onClick,
}: {
	message: MessageSummary;
	onClick: () => void;
}) {
	return (
		<button
			type="button"
			onClick={onClick}
			className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-white/60 dark:hover:bg-white/5 transition-colors border-b border-white/60 dark:border-white/10 last:border-0"
		>
			{!message.seen && (
				<span className="mt-2 w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400 shrink-0" />
			)}
			<div className={`flex-1 min-w-0 ${message.seen ? "pl-5" : ""}`}>
				<div className="flex items-center justify-between gap-2">
					<span
						className={`text-sm truncate ${
							message.seen
								? "text-slate-600 dark:text-slate-400"
								: "font-semibold text-slate-900 dark:text-slate-100"
						}`}
					>
						{message.from?.name || message.from?.address || "未知发件人"}
					</span>
					<span className="text-xs text-slate-400 dark:text-slate-500 shrink-0">
						{formatTime(message.createdAt)}
					</span>
				</div>
				<div
					className={`text-sm truncate ${
						message.seen
							? "text-slate-500 dark:text-slate-500"
							: "text-slate-800 dark:text-slate-200"
					}`}
				>
					{message.subject || "(无主题)"}
				</div>
				<div className="text-xs text-slate-400 dark:text-slate-500 truncate">
					{message.intro}
				</div>
			</div>
		</button>
	);
}
