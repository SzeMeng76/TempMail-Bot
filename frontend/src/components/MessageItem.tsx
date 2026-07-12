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
			className="w-full text-left px-4 py-3 flex items-start gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-0"
		>
			{!message.seen && (
				<span className="mt-2 w-2 h-2 rounded-full bg-blue-600 shrink-0" />
			)}
			<div className={`flex-1 min-w-0 ${message.seen ? "pl-5" : ""}`}>
				<div className="flex items-center justify-between gap-2">
					<span
						className={`text-sm truncate ${message.seen ? "text-gray-600" : "font-semibold text-gray-900"}`}
					>
						{message.from?.name || message.from?.address || "未知发件人"}
					</span>
					<span className="text-xs text-gray-400 shrink-0">
						{formatTime(message.createdAt)}
					</span>
				</div>
				<div
					className={`text-sm truncate ${message.seen ? "text-gray-500" : "text-gray-800"}`}
				>
					{message.subject || "(无主题)"}
				</div>
				<div className="text-xs text-gray-400 truncate">{message.intro}</div>
			</div>
		</button>
	);
}
