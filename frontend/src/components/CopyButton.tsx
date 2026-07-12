import { Check, Copy } from "lucide-react";
import { useState } from "react";

export function CopyButton({ text }: { text: string }) {
	const [copied, setCopied] = useState(false);

	const handleCopy = async () => {
		try {
			await navigator.clipboard.writeText(text);
			setCopied(true);
			setTimeout(() => setCopied(false), 1500);
		} catch {
			// clipboard 不可用时静默失败
		}
	};

	return (
		<button
			type="button"
			onClick={handleCopy}
			className="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors shrink-0"
		>
			{copied ? (
				<>
					<Check className="w-4 h-4" />
					已复制
				</>
			) : (
				<>
					<Copy className="w-4 h-4" />
					复制
				</>
			)}
		</button>
	);
}
