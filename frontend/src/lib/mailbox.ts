// 两个来源共用的数据模型。组件只依赖这里的类型，不直接碰任何一家的原始 JSON。

export type Provider = "mailtm" | "tempmailedu";

export interface MailAddress {
	address: string;
	name: string;
}

export interface MailMessage {
	id: string;
	subject: string;
	intro: string;
	seen: boolean;
	createdAt: string;
	from: MailAddress;
}

export interface MailMessageDetail extends MailMessage {
	text?: string;
	html?: string[];
}

// 域名选项带来源信息，但界面上只展示域名本身 —— 用户不需要知道背后是哪家。
export interface DomainOption {
	value: string;
	provider: Provider;
}

// mail.tm 用地址+密码换 token；tempmail.id.vn 的邮箱挂在服务端账号下，只需要地址。
export interface MailboxSession {
	provider: Provider;
	address: string;
	password?: string;
}
