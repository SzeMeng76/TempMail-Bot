import { Code2, Mail } from "lucide-react";

export function Navbar() {
	return (
		<header className="sticky top-0 z-50 backdrop-blur-xl bg-white/60 dark:bg-slate-950/50 border-b border-white/60 dark:border-white/10">
			<div className="container mx-auto px-4 py-3 max-w-5xl flex items-center justify-between">
				<a href="#top" className="flex items-center gap-2">
					<div className="bg-gradient-to-br from-blue-600 to-cyan-500 rounded-lg p-1.5">
						<Mail className="w-4 h-4 text-white" />
					</div>
					<span className="font-semibold text-slate-800 dark:text-slate-100">
						临时邮箱
					</span>
				</a>
				<nav className="flex items-center gap-4 sm:gap-6 text-sm text-slate-600 dark:text-slate-300">
					<a href="#features" className="hidden sm:inline hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
						功能
					</a>
					<a href="#how-it-works" className="hidden sm:inline hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
						使用步骤
					</a>
					<a href="#faq" className="hidden sm:inline hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
						常见问题
					</a>
					<a
						href="https://github.com/SzeMeng76/TempMail-Bot"
						target="_blank"
						rel="noopener noreferrer"
						className="flex items-center gap-1.5 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
					>
						<Code2 className="w-4 h-4" />
						<span className="hidden sm:inline">GitHub</span>
					</a>
				</nav>
			</div>
		</header>
	);
}
