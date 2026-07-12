import { Bot, Code2, ShieldCheck, Sparkles, Timer, Zap } from "lucide-react";

const FEATURES = [
	{
		icon: Zap,
		title: "即时创建",
		description: "无需注册，打开即用，一键生成随机临时邮箱地址",
	},
	{
		icon: ShieldCheck,
		title: "隐私保护",
		description: "保护你的真实邮箱地址，远离垃圾邮件和信息泄露",
	},
	{
		icon: Sparkles,
		title: "完全免费",
		description: "永久免费使用，无隐藏费用，无广告干扰",
	},
	{
		icon: Bot,
		title: "支持 Telegram 机器人",
		description: "除了网页，也可以通过 @smonetempbot 随时随地查收邮件",
		href: "https://t.me/smonetempbot",
	},
	{
		icon: Timer,
		title: "自动刷新",
		description: "收件箱每 10 秒自动刷新，新邮件到达无需手动操作",
	},
	{
		icon: Code2,
		title: "开源自建",
		description: "完整代码开源，支持 Docker 一键部署到你自己的服务器",
	},
];

export function Features() {
	return (
		<section id="features" className="py-16 scroll-mt-16">
			<h2 className="text-2xl font-bold text-center text-slate-800 dark:text-slate-100 mb-2">
				为什么用它？
			</h2>
			<p className="text-center text-slate-500 dark:text-slate-400 text-sm mb-10">
				一个干净、透明、可自行部署的临时邮箱工具
			</p>
			<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
				{FEATURES.map((f) => {
					const Card = (
						<>
							<div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 mb-3">
								<f.icon className="w-5 h-5" />
							</div>
							<h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-1">
								{f.title}
							</h3>
							<p className="text-sm text-slate-500 dark:text-slate-400">
								{f.description}
							</p>
						</>
					);

					const className =
						"rounded-2xl bg-white/50 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 p-5 hover:shadow-lg hover:shadow-blue-900/5 transition-shadow";

					return f.href ? (
						<a
							key={f.title}
							href={f.href}
							target="_blank"
							rel="noopener noreferrer"
							className={`${className} block`}
						>
							{Card}
						</a>
					) : (
						<div key={f.title} className={className}>
							{Card}
						</div>
					);
				})}
			</div>
		</section>
	);
}
