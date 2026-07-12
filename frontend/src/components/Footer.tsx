import { Code2, Mail, Send } from "lucide-react";

const FRIEND_LINKS = [
	{ label: "SM ONE DIGITAL STORE", href: "https://web.sm-one.com/" },
];

const CONTACT_LINKS = [
	{ label: "交流群", href: "https://t.me/smoneme" },
	{ label: "频道", href: "https://t.me/smoneinfo" },
];

export function Footer() {
	return (
		<footer className="border-t border-white/60 dark:border-white/10 py-10 mt-8">
			<div className="container mx-auto px-4 max-w-5xl">
				<div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-8">
					<div>
						<div className="flex items-center gap-2 mb-2">
							<div className="bg-gradient-to-br from-blue-600 to-cyan-500 rounded-lg p-1.5">
								<Mail className="w-4 h-4 text-white" />
							</div>
							<span className="font-semibold text-slate-800 dark:text-slate-100">
								临时邮箱
							</span>
						</div>
						<p className="text-sm text-slate-500 dark:text-slate-400 max-w-xs">
							免费、开源、无需注册的临时邮箱工具，同时提供网页和 Telegram 机器人两种使用方式。
						</p>
						<div className="flex items-center gap-4 mt-4">
							<a
								href="https://github.com/SzeMeng76/TempMail-Bot"
								target="_blank"
								rel="noopener noreferrer"
								className="text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
								aria-label="GitHub"
							>
								<Code2 className="w-5 h-5" />
							</a>
							<a
								href="https://t.me/csmmy90"
								target="_blank"
								rel="noopener noreferrer"
								className="text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
								aria-label="Telegram"
							>
								<Send className="w-5 h-5" />
							</a>
						</div>
					</div>

					<div>
						<h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
							联系我们
						</h4>
						<ul className="space-y-2">
							{CONTACT_LINKS.map((link) => (
								<li key={link.href}>
									<a
										href={link.href}
										target="_blank"
										rel="noopener noreferrer"
										className="text-sm text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
									>
										{link.label}
									</a>
								</li>
							))}
						</ul>
					</div>

					<div>
						<h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
							友情链接
						</h4>
						<ul className="space-y-2">
							{FRIEND_LINKS.map((link) => (
								<li key={link.href}>
									<a
										href={link.href}
										target="_blank"
										rel="noopener noreferrer"
										className="text-sm text-slate-500 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
									>
										{link.label}
									</a>
								</li>
							))}
						</ul>
					</div>
				</div>

				<div className="border-t border-white/60 dark:border-white/10 mt-8 pt-6 text-center text-xs text-slate-400 dark:text-slate-500">
					免费 · 安全 · 隐私保护
				</div>
			</div>
		</footer>
	);
}
