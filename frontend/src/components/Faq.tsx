import { ChevronDown } from "lucide-react";
import { useState } from "react";

const FAQS = [
	{
		question: "什么是临时邮箱？",
		answer:
			"临时邮箱是一种短期使用的电子邮件地址，通常用于注册网站、验证服务或保护你的主邮箱不受垃圾邮件侵扰，一段时间后会自动失效。",
	},
	{
		question: "这个服务免费吗？",
		answer: "完全免费，代码开源，不收取任何费用，也没有广告。",
	},
	{
		question: "邮箱地址和邮件会保存多久？",
		answer:
			"邮箱地址和收到的邮件由上游公共服务托管，具体保留时长以其平台策略为准，且长时间不使用的邮箱可能被回收。建议只用于临时验证，不要用于长期重要用途。",
	},
	{
		question: "可以自定义邮箱前缀吗？",
		answer:
			"可以。在地址框下方填写前缀，再选一个域名即可。填相同的前缀和域名能重新打开之前建过的同一个地址。",
	},
	{
		question: "支持发送邮件吗？",
		answer: "不支持，本服务仅用于接收邮件，无法用临时邮箱发送邮件。",
	},
	{
		question: "刷新页面后邮箱会变吗？",
		answer:
			"不会，邮箱地址和密码会保存在浏览器本地存储中，刷新页面会自动恢复同一个邮箱。如果清除了浏览器数据，或换了设备/浏览器，则需要重新生成或手动恢复。",
	},
	{
		question: "可以在其他设备上查看同一个邮箱吗？",
		answer:
			"可以，在生成邮箱时展示的密码就是登录凭证，在其他设备打开页面后点击“恢复已有邮箱”，输入相同的邮箱地址和密码即可。",
	},
];

export function Faq() {
	const [openIndex, setOpenIndex] = useState<number | null>(null);

	return (
		<section id="faq" className="py-16 scroll-mt-16">
			<h2 className="text-2xl font-bold text-center text-slate-800 dark:text-slate-100 mb-10">
				常见问题
			</h2>
			<div className="max-w-2xl mx-auto space-y-3">
				{FAQS.map((faq, i) => {
					const open = openIndex === i;
					return (
						<div
							key={faq.question}
							className="rounded-xl bg-white/50 dark:bg-white/5 backdrop-blur-xl border border-white/60 dark:border-white/10 overflow-hidden"
						>
							<button
								type="button"
								onClick={() => setOpenIndex(open ? null : i)}
								className="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left"
							>
								<span className="text-sm font-medium text-slate-800 dark:text-slate-100">
									{faq.question}
								</span>
								<ChevronDown
									className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${
										open ? "rotate-180" : ""
									}`}
								/>
							</button>
							{open && (
								<div className="px-4 pb-4 text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
									{faq.answer}
								</div>
							)}
						</div>
					);
				})}
			</div>
		</section>
	);
}
