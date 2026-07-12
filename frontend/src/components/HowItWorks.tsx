const STEPS = [
	{
		step: "1",
		title: "打开页面",
		description: "访问网站，系统会自动为你生成一个随机临时邮箱地址",
	},
	{
		step: "2",
		title: "复制地址",
		description: "点击复制按钮，将邮箱地址填入需要验证的网站或服务",
	},
	{
		step: "3",
		title: "查收邮件",
		description: "收件箱每 10 秒自动刷新，点击邮件即可查看完整内容",
	},
];

export function HowItWorks() {
	return (
		<section id="how-it-works" className="py-16 scroll-mt-16">
			<h2 className="text-2xl font-bold text-center text-slate-800 dark:text-slate-100 mb-10">
				使用步骤
			</h2>
			<div className="grid grid-cols-1 md:grid-cols-3 gap-8">
				{STEPS.map((s) => (
					<div key={s.step} className="text-center">
						<div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 text-white flex items-center justify-center mx-auto mb-4 text-lg font-bold shadow-lg shadow-blue-600/20">
							{s.step}
						</div>
						<h3 className="font-semibold text-slate-800 dark:text-slate-100 mb-1">
							{s.title}
						</h3>
						<p className="text-sm text-slate-500 dark:text-slate-400">
							{s.description}
						</p>
					</div>
				))}
			</div>
		</section>
	);
}
