import { ArrowLeft, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { getMessage, type MessageDetail as MessageDetailType } from "../lib/mailtm";

function buildSrcDoc(detail: MessageDetailType): string {
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

export function MessageDetail({
	token,
	messageId,
	onBack,
}: {
	token: string;
	messageId: string;
	onBack: () => void;
}) {
	const [detail, setDetail] = useState<MessageDetailType | null>(null);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		getMessage(token, messageId)
			.then((data) => {
				if (!cancelled) setDetail(data);
			})
			.catch(() => {
				if (!cancelled) setError("加载邮件失败");
			});
		return () => {
			cancelled = true;
		};
	}, [token, messageId]);

	return (
		<div className="flex flex-col h-full">
			<div className="flex items-center gap-2 px-4 py-3 border-b border-gray-100 shrink-0">
				<button
					type="button"
					onClick={onBack}
					className="p-1.5 rounded-md hover:bg-gray-100 text-gray-600"
				>
					<ArrowLeft className="w-4 h-4" />
				</button>
				<span className="text-sm text-gray-500">返回收件箱</span>
			</div>

			{error && <div className="p-4 text-sm text-red-600">{error}</div>}

			{!detail && !error && (
				<div className="flex-1 flex items-center justify-center text-gray-400">
					<Loader2 className="w-5 h-5 animate-spin" />
				</div>
			)}

			{detail && (
				<>
					<div className="px-4 py-3 border-b border-gray-100 shrink-0">
						<h2 className="text-base font-semibold text-gray-900 break-words">
							{detail.subject || "(无主题)"}
						</h2>
						<div className="mt-1 text-xs text-gray-500 space-y-0.5">
							<div>发件人：{detail.from?.address}</div>
							<div>时间：{new Date(detail.createdAt).toLocaleString("zh-CN")}</div>
						</div>
					</div>
					<iframe
						title="邮件内容"
						srcDoc={buildSrcDoc(detail)}
						sandbox=""
						className="flex-1 w-full border-0"
					/>
				</>
			)}
		</div>
	);
}
