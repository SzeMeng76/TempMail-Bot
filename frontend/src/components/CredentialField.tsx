import { Check, Copy, Eye, EyeOff } from "lucide-react";
import { useState } from "react";

export function CredentialField({
	label,
	value,
	mask = false,
}: {
	label: string;
	value: string;
	mask?: boolean;
}) {
	const [revealed, setRevealed] = useState(!mask);
	const [copied, setCopied] = useState(false);

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(value);
			setCopied(true);
			setTimeout(() => setCopied(false), 1500);
		} catch {
			// clipboard 不可用时静默失败
		}
	};

	return (
		<div className="flex items-center gap-2">
			<span className="text-xs text-slate-500 dark:text-slate-400 w-12 shrink-0">
				{label}
			</span>
			<div className="flex-1 min-w-0 bg-white/70 dark:bg-black/20 border border-white/60 dark:border-white/10 rounded-lg px-3 py-2 font-mono text-sm text-slate-900 dark:text-slate-100 select-all break-all">
				{revealed ? value : "•".repeat(Math.min(value.length, 16))}
			</div>
			{mask && (
				<button
					type="button"
					onClick={() => setRevealed((v) => !v)}
					className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-white/60 dark:hover:bg-white/10 transition-colors shrink-0"
					title={revealed ? "隐藏" : "显示"}
				>
					{revealed ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
				</button>
			)}
			<button
				type="button"
				onClick={handleCopy}
				className="p-2 rounded-lg text-slate-500 dark:text-slate-400 hover:bg-white/60 dark:hover:bg-white/10 transition-colors shrink-0"
				title="复制"
			>
				{copied ? (
					<Check className="w-4 h-4 text-green-600 dark:text-green-400" />
				) : (
					<Copy className="w-4 h-4" />
				)}
			</button>
		</div>
	);
}
