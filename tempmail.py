# Author (C) @theSmartBisnu
# Channel : https://t.me/itsSmartDev

import os
import re
import json
import time
import random
import string
import hashlib
import requests
from bs4 import BeautifulSoup
from pyrogram.enums import ParseMode, ChatType
from pyrogram import Client, filters

from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN
)

import tempmailedu
import vnpool
import luuvan

# tempmail.id.vn 是可选来源：没配 key 时 /tmail vn 会明确提示未启用，
# 主流程（mail.tm）完全不受影响。多 key 调度、满了删最旧都在 vnpool 里。
#
# luuvan.site 不一样：它的地址本身就是读信凭证（服务端 catch-all），
# 所以不需要存任何映射，/cmail 直接给地址就能读 —— 发卡密正是走这条路。

# Initialize the bot client
bot = Client(
    "bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=1000,
    parse_mode=ParseMode.MARKDOWN,
    workdir=os.environ.get("SESSION_DIR", ".")
)

user_data = {}

token_map = {}

user_tokens = {}
MAX_MESSAGE_LENGTH = 4000

BASE_URL = "https://api.mail.tm"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# ---------------------------------------------------------------------------
# i18n
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = [
    ("zh-CN", "🇨🇳 简体中文"),
    ("zh-TW", "🇹🇼 繁體中文"),
    ("en-US", "🇺🇸 English"),
]

DEFAULT_LOCALE = "zh-CN"

# 语言偏好持久化，跟 session 文件放同一目录，bot 重启后仍然有效
LOCALES_FILE = os.path.join(os.environ.get("SESSION_DIR", "."), "user_locales.json")

STRINGS = {
    "zh-CN": {
        "choose_language": "🌐 请选择语言 / Please select your language:",
        "language_saved": "✅ 语言已切换为 {lang}",
        "welcome": (
            "**欢迎使用临时邮箱机器人！** 🎉\n\n"
            "你可以使用以下命令来管理临时邮箱地址：\n\n"
            "➢ `/tmail` - 随机生成一个临时邮箱和密码。\n"
            "➢ `/tmail [用户名]:[密码]` - 使用指定的用户名和密码生成邮箱。\n"
            "➢ `/cmail [邮箱令牌]` - 使用令牌查看最近的 10 封邮件。\n"
            "➢ `/lang` - 切换语言。\n\n"
            "✨ **提示：** 生成邮箱和密码后，你会获得一个邮箱令牌（token）。"
            "该令牌可用于查看该临时邮箱收到的最近 10 封邮件。"
            "每个邮箱的令牌都不同，请妥善保管，不要泄露给他人。🛡️"
        ),
        "private_only": "**请在私聊中使用此机器人。**",
        "generating": "**正在生成临时邮箱...**",
        "domain_failed": "**获取域名失败，请重试**",
        "username_taken": "**用户名已被占用，请换一个。**",
        "token_failed": "**获取令牌失败。**",
        "mail_details": (
            "**📧 智能邮箱详情 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 邮箱：** `{email}`\n"
            "**🔑 密码：** `{password}`\n"
            "**🔒 令牌：** `{token}`\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**提示：请保管好令牌，用于查看邮件**"
        ),
        "btn_check_mail": "查看邮件",
        "session_expired": "**会话已过期，请使用 /cmail 命令并提供你的令牌。**",
        "no_mail_alert": "暂无邮件 ❌",
        "loading_mail": "**⏳ 正在查看邮件，请稍候。**",
        "inbox_header": "**📧 你的智能邮箱消息 📧**\n**━━━━━━━━━━━━━━━━━━**\n",
        "inbox_line": "{idx}. 发件人：`{address}` - 主题：{subject}\n",
        "token_not_found": "**未找到令牌，请重新使用 /cmail 命令并提供你的令牌。**",
        "no_content": "暂无可显示的内容。",
        "truncated": "...【内容已截断】",
        "detail_from": "发件人",
        "detail_subject": "主题",
        "btn_close": "关闭",
        "detail_failed": "**获取邮件详情失败。**",
        "provide_token": "**请在 /cmail 命令后提供令牌。**",
        "no_messages_or_bad_token": "**❌ 未找到邮件，或令牌错误**",
        "vn_not_configured": "**该来源暂未启用。**",
        "vn_create_failed": "**创建邮箱失败：** {error}",
        "vn_read_failed": "**读取邮件失败：** {error}",
        "vn_quota_exhausted": (
            "**⚠️ 这个邮箱暂时读不了了**\n\n"
            "当前来源的读取额度已经用完。\n\n"
            "**你可以：**\n"
            "➢ 等几分钟再试（如果是短时间内刷得太频繁）\n"
            "➢ 直接发 `/tmail` 重新生成一个（会自动换到可用的来源）\n"
            "➢ 稍后再试，可能已经分配到其他账号上"
        ),
        "vn_mailbox_gone": "**该邮箱已被回收（长期未使用会被清理），请发 `/tmail` 重新生成。**",
        "vn_mail_details": (
            "**📧 智能邮箱详情 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 邮箱：** `{email}`\n"
            "**🔑 密码：** 无（不需要密码）\n"
            "**🔒 令牌：** 无\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**提示：直接点下方按钮查看邮件；之后可用 `/cmail 邮箱地址` 重新打开**"
        ),
        "vn_evicted_notice": "\n\n⚠️ 账号邮箱已满，已自动清理 {count} 个最旧的邮箱。",
        "lv_create_failed": "**创建邮箱失败：** {error}",
        "lv_read_failed": "**读取邮件失败：** {error}",
        "lv_mail_details": (
            "**📧 智能邮箱详情 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 邮箱：** `{email}`\n"
            "**🔑 密码：** 无（不需要密码）\n"
            "**🔒 令牌：** 无（地址本身就是凭证）\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**提示：直接点下方按钮查看邮件；之后可用 `/cmail {email}` 重新打开**"
        ),
        "lv_expiry_notice": "\n\n⚠️ 当前未配置 API key，邮箱将在 {hours} 小时后过期。",
    },
    "zh-TW": {
        "choose_language": "🌐 請選擇語言 / Please select your language:",
        "language_saved": "✅ 語言已切換為 {lang}",
        "welcome": (
            "**歡迎使用臨時信箱機器人！** 🎉\n\n"
            "你可以使用以下指令來管理臨時信箱地址：\n\n"
            "➢ `/tmail` - 隨機產生一個臨時信箱和密碼。\n"
            "➢ `/tmail [使用者名稱]:[密碼]` - 使用指定的使用者名稱和密碼產生信箱。\n"
            "➢ `/cmail [信箱權杖]` - 使用權杖查看最近的 10 封郵件。\n"
            "➢ `/lang` - 切換語言。\n\n"
            "✨ **提示：** 產生信箱和密碼後，你會獲得一個信箱權杖（token）。"
            "該權杖可用於查看該臨時信箱收到的最近 10 封郵件。"
            "每個信箱的權杖都不同，請妥善保管，不要洩露給他人。🛡️"
        ),
        "private_only": "**請在私聊中使用此機器人。**",
        "generating": "**正在產生臨時信箱...**",
        "domain_failed": "**取得網域失敗，請重試**",
        "username_taken": "**使用者名稱已被佔用，請換一個。**",
        "token_failed": "**取得權杖失敗。**",
        "mail_details": (
            "**📧 智慧信箱詳情 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 信箱：** `{email}`\n"
            "**🔑 密碼：** `{password}`\n"
            "**🔒 權杖：** `{token}`\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**提示：請保管好權杖，用於查看郵件**"
        ),
        "btn_check_mail": "查看郵件",
        "session_expired": "**工作階段已過期，請使用 /cmail 指令並提供你的權杖。**",
        "no_mail_alert": "暫無郵件 ❌",
        "loading_mail": "**⏳ 正在查看郵件，請稍候。**",
        "inbox_header": "**📧 你的智慧信箱訊息 📧**\n**━━━━━━━━━━━━━━━━━━**\n",
        "inbox_line": "{idx}. 寄件者：`{address}` - 主旨：{subject}\n",
        "token_not_found": "**未找到權杖，請重新使用 /cmail 指令並提供你的權杖。**",
        "no_content": "暫無可顯示的內容。",
        "truncated": "...【內容已截斷】",
        "detail_from": "寄件者",
        "detail_subject": "主旨",
        "btn_close": "關閉",
        "detail_failed": "**取得郵件詳情失敗。**",
        "provide_token": "**請在 /cmail 指令後提供權杖。**",
        "no_messages_or_bad_token": "**❌ 未找到郵件，或權杖錯誤**",
        "vn_not_configured": "**該來源暫未啟用。**",
        "vn_create_failed": "**建立信箱失敗：** {error}",
        "vn_read_failed": "**讀取信件失敗：** {error}",
        "vn_quota_exhausted": (
            "**⚠️ 這個信箱暫時讀不了了**\n\n"
            "目前來源的讀取額度已經用完。\n\n"
            "**你可以：**\n"
            "➢ 等幾分鐘再試（如果是短時間內刷得太頻繁）\n"
            "➢ 直接發 `/tmail` 重新產生一個（會自動換到可用的來源）\n"
            "➢ 稍後再試，可能已經分配到其他帳號上"
        ),
        "vn_mailbox_gone": "**該信箱已被回收（長期未使用會被清理），請發 `/tmail` 重新產生。**",
        "vn_mail_details": (
            "**📧 智慧信箱詳情 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 信箱：** `{email}`\n"
            "**🔑 密碼：** 無（不需要密碼）\n"
            "**🔒 權杖：** 無\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**提示：直接點下方按鈕查看信件；之後可用 `/cmail 信箱地址` 重新開啟**"
        ),
        "vn_evicted_notice": "\n\n⚠️ 帳號信箱已滿，已自動清理 {count} 個最舊的信箱。",
        "lv_create_failed": "**建立信箱失敗：** {error}",
        "lv_read_failed": "**讀取信件失敗：** {error}",
        "lv_mail_details": (
            "**📧 智慧信箱詳情 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 信箱：** `{email}`\n"
            "**🔑 密碼：** 無（不需要密碼）\n"
            "**🔒 權杖：** 無（地址本身就是憑證）\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**提示：直接點下方按鈕查看信件；之後可用 `/cmail {email}` 重新開啟**"
        ),
        "lv_expiry_notice": "\n\n⚠️ 目前未設定 API key，信箱將於 {hours} 小時後過期。",
    },
    "en-US": {
        "choose_language": "🌐 Please select your language:",
        "language_saved": "✅ Language switched to {lang}",
        "welcome": (
            "**Welcome to the Temp Mail Bot!** 🎉\n\n"
            "You can manage temporary email addresses with these commands:\n\n"
            "➢ `/tmail` - Generate a random temporary email and password.\n"
            "➢ `/tmail [username]:[password]` - Create an email with your own username and password.\n"
            "➢ `/cmail [token]` - View the 10 most recent messages using a token.\n"
            "➢ `/lang` - Change language.\n\n"
            "✨ **Tip:** After creating an email you will receive a mailbox token. "
            "Use it to view the 10 most recent messages of that mailbox. "
            "Each mailbox has its own token — keep it safe and never share it. 🛡️"
        ),
        "private_only": "**Please use this bot in a private chat.**",
        "generating": "**Generating a temporary email...**",
        "domain_failed": "**Failed to fetch a domain, please try again.**",
        "username_taken": "**That username is taken, please try another.**",
        "token_failed": "**Failed to get the token.**",
        "mail_details": (
            "**📧 Smart Mail Details 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 Email:** `{email}`\n"
            "**🔑 Password:** `{password}`\n"
            "**🔒 Token:** `{token}`\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**Tip: keep the token safe — you need it to read mail**"
        ),
        "btn_check_mail": "Check Mail",
        "session_expired": "**Session expired. Please use /cmail with your token.**",
        "no_mail_alert": "No mail yet ❌",
        "loading_mail": "**⏳ Checking mail, please wait.**",
        "inbox_header": "**📧 Your Smart Mail Messages 📧**\n**━━━━━━━━━━━━━━━━━━**\n",
        "inbox_line": "{idx}. From: `{address}` - Subject: {subject}\n",
        "token_not_found": "**Token not found. Please use /cmail with your token again.**",
        "no_content": "No content to display.",
        "truncated": "...[Content truncated]",
        "detail_from": "From",
        "detail_subject": "Subject",
        "btn_close": "Close",
        "detail_failed": "**Failed to fetch message details.**",
        "provide_token": "**Please provide a token after the /cmail command.**",
        "no_messages_or_bad_token": "**❌ No messages found, or the token is invalid.**",
        "vn_not_configured": "**That source is not enabled.**",
        "vn_create_failed": "**Failed to create mailbox:** {error}",
        "vn_read_failed": "**Failed to read messages:** {error}",
        "vn_quota_exhausted": (
            "**⚠️ This mailbox can't be read right now**\n\n"
            "The current source has used up its read quota.\n\n"
            "**What you can do:**\n"
            "➢ Wait a few minutes and retry (if you just refreshed too often)\n"
            "➢ Send `/tmail` to create a new mailbox (it picks a working source automatically)\n"
            "➢ Try again later — it may have moved to another account"
        ),
        "vn_mailbox_gone": "**This mailbox has been recycled (unused ones are cleaned up). Send `/tmail` to create a new one.**",
        "vn_mail_details": (
            "**📧 Mailbox details 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 Address:** `{email}`\n"
            "**🔑 Password:** none (this source uses no password)\n"
            "**🔒 Token:** none (the mailbox is bound to the server-side account)\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**Tip: use the button below to read messages**"
        ),
        "vn_evicted_notice": "\n\n⚠️ The account was full, so {count} of the oldest mailboxes were cleaned up.",
        "lv_create_failed": "**Failed to create mailbox:** {error}",
        "lv_read_failed": "**Failed to read messages:** {error}",
        "lv_mail_details": (
            "**📧 Mailbox details 📧**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**📧 Address:** `{email}`\n"
            "**🔑 Password:** none (this source uses no password)\n"
            "**🔒 Token:** none (the address itself is the credential)\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "**Tip: use the button below to read messages; later reopen with `/cmail {email}`**"
        ),
        "lv_expiry_notice": "\n\n⚠️ No API key configured, so this mailbox expires in {hours} hours.",
    },
}


def load_user_locales():
    try:
        with open(LOCALES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_user_locales():
    try:
        with open(LOCALES_FILE, "w", encoding="utf-8") as f:
            json.dump(user_locales, f, ensure_ascii=False)
    except OSError as e:
        print(f"Failed to save locales: {e}")


user_locales = load_user_locales()


def t(user_id, key, **kwargs):
    locale = user_locales.get(str(user_id), DEFAULT_LOCALE)
    text = STRINGS.get(locale, STRINGS[DEFAULT_LOCALE]).get(key) or STRINGS[DEFAULT_LOCALE][key]
    return text.format(**kwargs) if kwargs else text


def language_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(name, callback_data=f"setlang_{code}")]
        for code, name in SUPPORTED_LANGUAGES
    ])


def short_id_generator(email):
    unique_string = email + str(time.time())
    return hashlib.md5(unique_string.encode()).hexdigest()[:10]

def generate_random_username(length=8):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))

def get_domain():
    response = requests.get(f"{BASE_URL}/domains", headers=HEADERS)
    data = response.json()
    if isinstance(data, list) and data:
        return data[0]['domain']
    elif 'hydra:member' in data and data['hydra:member']:
        return data['hydra:member'][0]['domain']
    return None


def pick_backend():
    """
    随机挑一个可用的后端，返回 'mailtm'、'tempmailedu' 或 'luuvan'。

    用户不该关心邮箱是从哪来的——/tmail 默认就是随机一个。
    未配置的 key 或调用失败时一律回落到 mail.tm（它没有额度限制，更稳）。
    """
    # luuvan 不需要 key 也能建号（游客 5 个/天），所以始终参与分摊。
    roll = random.random()
    if vnpool.available():
        # 有第三个来源时给 mail.tm 40%，另外两个各 30%。
        if roll < 0.4:
            return "mailtm"
        return "tempmailedu" if roll < 0.7 else "luuvan"
    # 没有 vn 时两个来源各一半。
    return "mailtm" if roll < 0.5 else "luuvan"

def create_account(email, password):
    data = {
        "address": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/accounts", headers=HEADERS, json=data)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Error Code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_token(email, password):
    data = {
        "address": email,
        "password": password
    }
    response = requests.post(f"{BASE_URL}/token", headers=HEADERS, json=data)
    if response.status_code == 200:
        return response.json().get('token')
    else:
        print(f"Token Error Code: {response.status_code}")
        print(f"Token Response: {response.text}")
        return None

def get_text_from_html(html_content_list):
    html_content = ''.join(html_content_list)
    soup = BeautifulSoup(html_content, 'html.parser')

    for a_tag in soup.find_all('a', href=True):
        url = a_tag['href']
        new_content = f"{a_tag.text} [{url}]"
        a_tag.string = new_content

    text_content = soup.get_text()
    cleaned_content = re.sub(r'\s+', ' ', text_content).strip()
    return cleaned_content

def list_messages(token):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/messages", headers=headers)
    data = response.json()
    if isinstance(data, list):
        return data
    elif 'hydra:member' in data:
        return data['hydra:member']
    else:
        return []


@bot.on_message(filters.command('start'))
async def start(client, message):
    user_id = message.from_user.id
    # 首次使用先选语言，选过之后直接显示欢迎信息
    if str(user_id) not in user_locales:
        await message.reply(
            STRINGS[DEFAULT_LOCALE]["choose_language"],
            reply_markup=language_keyboard()
        )
        return
    await message.reply(t(user_id, "welcome"))


@bot.on_message(filters.command('lang'))
async def change_language(client, message):
    await message.reply(
        t(message.from_user.id, "choose_language"),
        reply_markup=language_keyboard()
    )


@bot.on_callback_query(filters.regex(r'^setlang_'))
async def set_language(client, callback_query):
    locale = callback_query.data.split('_', 1)[1]
    if locale not in STRINGS:
        locale = DEFAULT_LOCALE

    user_id = callback_query.from_user.id
    first_time = str(user_id) not in user_locales
    user_locales[str(user_id)] = locale
    save_user_locales()

    lang_name = dict(SUPPORTED_LANGUAGES).get(locale, locale)
    await callback_query.answer(t(user_id, "language_saved", lang=lang_name))

    # 首次选完语言直接展示欢迎信息，切换语言时用编辑消息给出确认
    if first_time:
        await callback_query.message.edit_text(t(user_id, "welcome"))
    else:
        await callback_query.message.edit_text(
            t(user_id, "language_saved", lang=lang_name) + "\n\n" + t(user_id, "welcome")
        )


@bot.on_message(filters.command('tmail'))
async def generate_mail(client, message):
    user_id = message.from_user.id
    if message.chat.type != ChatType.PRIVATE:
        await message.reply(t(user_id, "private_only"))
        return

    loading_msg = await message.reply(t(user_id, "generating"))

    args_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    args = args_text.split()

    # 显式指定 tempmail.id.vn（`/tmail vn ...`）时直接走它，方便需要 edu 域名的场景。
    if args and args[0].lower() in ("vn", "edu"):
        await generate_mail_vn(user_id, message, loading_msg, args[1:])
        return

    # `/tmail lv [前缀][@域名]` 走 luuvan：地址本身就是凭证，最适合发卡密。
    if args and args[0].lower() in ("lv", "luuvan"):
        await generate_mail_luuvan(user_id, message, loading_msg, args[1:])
        return

    if len(args) == 1 and ':' in args[0]:
        username, password = args[0].split(':')
    else:
        username = generate_random_username()
        password = generate_random_password()

    # 不带参数时在两个来源之间随机，用户不需要知道邮箱从哪来。
    if not args and pick_backend() == "tempmailedu":
        if await generate_mail_vn(user_id, message, loading_msg, []):
            return
        # vn 不可用时继续走 mail.tm，别让用户拿到一个报错。

    domain = get_domain()
    if not domain:
        await message.reply(t(user_id, "domain_failed"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    email = f"{username}@{domain}"
    account = create_account(email, password)
    if not account:
        await message.reply(t(user_id, "username_taken"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    # 服务端会规范化地址（例如把 local part 里的点号去掉），
    # 必须用它返回的地址换 token，否则会一直取不到令牌。
    email = account.get("address") or email

    time.sleep(2)

    token = get_token(email, password)
    if not token:
        await message.reply(t(user_id, "token_failed"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    short_id = short_id_generator(email)
    token_map[short_id] = {"provider": "mailtm", "token": token}

    output_message = t(user_id, "mail_details", email=email, password=password, token=token)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(t(user_id, "btn_check_mail"), callback_data=f"check_{short_id}")]])

    await message.reply(output_message, reply_markup=keyboard)
    await bot.delete_messages(message.chat.id, [loading_msg.id])


async def generate_mail_vn(user_id, message, loading_msg, args):
    """
    tempmail.id.vn 建号。没有密码和 token，只有地址。

    多个 key 的分摊、以及账号满了删最旧邮箱，都在 vnpool.create 里做；
    这里只关心把结果告诉用户。

    返回 True 表示已经处理完（无论成功还是已向用户报错）；
    False 表示这个来源当前不可用，调用方可以回落到 mail.tm。
    """
    if not vnpool.available():
        return False

    prefix = None
    domain = None
    if args:
        raw = args[0]
        if '@' in raw:
            prefix, domain = raw.split('@', 1)
        else:
            prefix = raw

    try:
        slot, created = vnpool.create(prefix or None, domain or None)
    except tempmailedu.TempMailEduError as exc:
        await message.reply(t(user_id, "vn_create_failed", error=exc))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return True

    email = created["address"]
    short_id = short_id_generator(email)
    # 只存地址和 slot：mail_id 会因为「删最旧」而失效，读信前用 vnpool.resolve 重新解析。
    token_map[short_id] = {
        "provider": "tempmailedu",
        "address": email,
        "slot": slot,
    }

    output_message = t(user_id, "vn_mail_details", email=email)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(t(user_id, "btn_check_mail"), callback_data=f"check_{short_id}")]])

    await message.reply(output_message, reply_markup=keyboard)
    await bot.delete_messages(message.chat.id, [loading_msg.id])
    return True


async def generate_mail_luuvan(user_id, message, loading_msg, args):
    """
    luuvan.site 建号。

    带 key 建的邮箱是永久的；没配 key 只能走游客接口（5 个/天/IP、24 小时过期），
    这种情况要明确告诉用户，否则他会以为邮箱一直能用。
    """
    prefix = None
    domain = None
    if args:
        raw = args[0]
        if '@' in raw:
            prefix, domain = raw.split('@', 1)
        else:
            prefix = raw
        prefix = prefix.strip() or None
        domain = (domain or "").strip() or None

    try:
        created = luuvan.create(prefix, domain)
    except luuvan.LuuvanError as exc:
        await message.reply(t(user_id, "lv_create_failed", error=exc))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    email = created["address"]
    short_id = short_id_generator(email)
    # 只存地址：luuvan 的读信接口只要地址，不需要 token/slot。
    token_map[short_id] = {"provider": "luuvan", "address": email}

    output_message = t(user_id, "lv_mail_details", email=email)
    if not created["via_key"]:
        output_message += t(user_id, "lv_expiry_notice", hours=24)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(t(user_id, "btn_check_mail"), callback_data=f"check_{short_id}")]])

    await message.reply(output_message, reply_markup=keyboard)
    await bot.delete_messages(message.chat.id, [loading_msg.id])
async def check_mail(client, callback_query):
    user_id = callback_query.from_user.id
    short_id = callback_query.data.split('_')[1]
    session = token_map.get(short_id)
    if not session:
        await callback_query.message.reply(t(user_id, "session_expired"))
        return

    user_tokens[user_id] = session

    if session["provider"] == "tempmailedu":
        fetched = await fetch_vn_messages(user_id, session, callback_query)
        if fetched is None:
            return
    elif session["provider"] == "luuvan":
        try:
            fetched = luuvan.list_messages(session["address"])
        except luuvan.LuuvanError as exc:
            await callback_query.message.reply(t(user_id, "lv_read_failed", error=exc))
            return
    else:
        fetched = list_messages(session["token"])

    if not fetched:
        await callback_query.answer(t(user_id, "no_mail_alert"), show_alert=True)
        return

    loading_msg = await callback_query.message.reply(t(user_id, "loading_mail"))

    output = t(user_id, "inbox_header")

    buttons = []
    for idx, msg in enumerate(fetched[:10], 1):
        if session["provider"] == "tempmailedu":
            address = tempmailedu.sender_address(msg)
            subject = tempmailedu.subject(msg)
        elif session["provider"] == "luuvan":
            address = luuvan.sender_address(msg)
            subject = luuvan.subject(msg)
        else:
            address = msg['from']['address']
            subject = msg['subject']
        output += t(user_id, "inbox_line", idx=idx, address=address, subject=subject)
        button = InlineKeyboardButton(f"{idx}", callback_data=f"read_{msg['id']}")
        buttons.append(button)

    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:i+5])

    await callback_query.message.reply(output, reply_markup=InlineKeyboardMarkup(keyboard))
    await bot.delete_messages(callback_query.message.chat.id, [loading_msg.id])


async def fetch_vn_messages(user_id, session, callback_query):
    """
    按地址重新解析 mail_id 再读信。

    不能缓存 mail_id：账号满 50 个时会删最旧的邮箱，删掉重建的同名地址
    会拿到新的 id，旧 id 直接失效。
    失败返回 None（已向用户提示）。
    """
    slot, mail_id = vnpool.resolve(session["address"])
    if slot is None:
        await callback_query.message.reply(t(user_id, "vn_mailbox_gone"))
        return None

    api_key = vnpool.key_for(slot)
    if not api_key:
        await callback_query.message.reply(t(user_id, "vn_not_configured"))
        return None

    try:
        return tempmailedu.list_messages(api_key, mail_id)
    except tempmailedu.TempMailEduError as exc:
        await callback_query.message.reply(t(user_id, vn_error_key(exc)))
        return None


def vn_error_key(exc):
    """
    把上游错误翻成用户能看懂的提示。

    额度类错误最要紧：这时这个邮箱在当前账号下已经读不了了，
    但换个来源（mail.tm）或重新建一个仍然可用，所以提示里要让用户知道下一步做什么。
    """
    kind = getattr(exc, "kind", "other")
    if kind == "quota":
        return "vn_quota_exhausted"
    if kind == "notfound":
        return "vn_mailbox_gone"
    if kind == "auth":
        return "vn_not_configured"
    return "vn_read_failed"

@bot.on_callback_query(filters.regex(r"^close_message"))
async def close_message(client, callback_query):
    await callback_query.message.delete()

@bot.on_callback_query(filters.regex(r"^read_"))
async def read_message(client, callback_query):
    user_id = callback_query.from_user.id
    message_id = callback_query.data.split('_')[1]
    session = user_tokens.get(user_id)

    if not session:
        await callback_query.message.reply(t(user_id, "token_not_found"))
        return

    if session["provider"] == "tempmailedu":
        await read_message_vn(user_id, callback_query, session, message_id)
        return

    if session["provider"] == "luuvan":
        await read_message_luuvan(user_id, callback_query, session, message_id)
        return

    token = session["token"]
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(f"{BASE_URL}/messages/{message_id}", headers=headers)

    if response.status_code == 200:
        details = response.json()
        if 'html' in details:
            message_text = get_text_from_html(details['html'])
        elif 'text' in details:
            message_text = details['text']
        else:
            message_text = t(user_id, "no_content")

        # Truncate the message if it's too long
        if len(message_text) > MAX_MESSAGE_LENGTH:
            message_text = message_text[:MAX_MESSAGE_LENGTH - 100] + t(user_id, "truncated")

        output = f"**{t(user_id, 'detail_from')}：** `{details['from']['address']}`\n**{t(user_id, 'detail_subject')}：** `{details['subject']}`\n━━━━━━━━━━━━━━━━━━\n{message_text}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(t(user_id, "btn_close"), callback_data="close_message")]
        ])

        sent_message = await callback_query.message.reply(output, disable_web_page_preview=True, reply_markup=keyboard)

    else:
        await callback_query.message.reply(t(user_id, "detail_failed"))


async def read_message_luuvan(user_id, callback_query, session, message_id):
    """
    luuvan.site 读信。正文在 html / text 两个字段里，html 优先。

    详情接口要求同时带 address —— 服务端用它校验这封信属于该邮箱，
    所以地址必须跟列表接口用的是同一个。
    """
    try:
        details = luuvan.get_message(session["address"], message_id)
    except luuvan.LuuvanError as exc:
        await callback_query.message.reply(t(user_id, "lv_read_failed", error=exc))
        return

    html = details.get("html") or ""
    if html.strip():
        message_text = get_text_from_html([html])
    else:
        message_text = details.get("text") or ""

    if not message_text.strip():
        message_text = t(user_id, "no_content")

    if len(message_text) > MAX_MESSAGE_LENGTH:
        message_text = message_text[:MAX_MESSAGE_LENGTH - 100] + t(user_id, "truncated")

    output = (
        f"**{t(user_id, 'detail_from')}：** `{details.get('from') or ''}`\n"
        f"**{t(user_id, 'detail_subject')}：** `{details.get('subject') or ''}`\n"
        f"━━━━━━━━━━━━━━━━━━\n{message_text}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "btn_close"), callback_data="close_message")]
    ])

    await callback_query.message.reply(output, disable_web_page_preview=True, reply_markup=keyboard)


async def read_message_vn(user_id, callback_query, session, message_id):
    """tempmail.id.vn 读信。body 可能是 HTML，也可能是纯文本。"""
    slot, _mail_id = vnpool.resolve(session["address"])
    if slot is None:
        await callback_query.message.reply(t(user_id, "vn_mailbox_gone"))
        return

    api_key = vnpool.key_for(slot)
    if not api_key:
        await callback_query.message.reply(t(user_id, "vn_not_configured"))
        return

    try:
        details = tempmailedu.get_message(api_key, message_id)
    except tempmailedu.TempMailEduError as exc:
        await callback_query.message.reply(t(user_id, vn_error_key(exc)))
        return

    body = details.get("body") or ""
    # 带标签就按 HTML 处理，否则当纯文本直接用。
    if re.search(r"<[a-z][\s\S]*>", body, re.IGNORECASE):
        message_text = get_text_from_html([body])
    else:
        message_text = body

    if not message_text.strip():
        message_text = t(user_id, "no_content")

    if len(message_text) > MAX_MESSAGE_LENGTH:
        message_text = message_text[:MAX_MESSAGE_LENGTH - 100] + t(user_id, "truncated")

    output = (
        f"**{t(user_id, 'detail_from')}：** `{tempmailedu.sender_address(details)}`\n"
        f"**{t(user_id, 'detail_subject')}：** `{tempmailedu.subject(details)}`\n"
        f"━━━━━━━━━━━━━━━━━━\n{message_text}"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(t(user_id, "btn_close"), callback_data="close_message")]
    ])

    await callback_query.message.reply(output, disable_web_page_preview=True, reply_markup=keyboard)


@bot.on_message(filters.command('cmail'))
async def manual_check_mail(client, message):
    user_id = message.from_user.id
    if message.chat.type != ChatType.PRIVATE:
        await message.reply(t(user_id, "private_only"))
        return

    loading_msg = await message.reply(t(user_id, "loading_mail"))

    arg = message.text.split(maxsplit=1)[1].strip() if len(message.text.split()) > 1 else ""
    if not arg:
        await message.reply(t(user_id, "provide_token"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    # 带 @ 的按邮箱地址处理（这部分来源没有令牌，地址本身就是凭证）；
    # 否则沿用原来的令牌方式。
    if "@" in arg:
        address = arg.strip()
        if is_luuvan_address(address):
            await manual_check_luuvan(user_id, message, loading_msg, address)
        else:
            await manual_check_vn(user_id, message, loading_msg, address)
        return

    token = arg
    user_tokens[user_id] = {"provider": "mailtm", "token": token}
    messages = list_messages(token)
    if not messages:
        await message.reply(t(user_id, "no_messages_or_bad_token"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    output = t(user_id, "inbox_header")

    buttons = []
    for idx, msg in enumerate(messages[:10], 1):
        output += t(user_id, "inbox_line", idx=idx, address=msg['from']['address'], subject=msg['subject'])
        button = InlineKeyboardButton(f"{idx}", callback_data=f"read_{msg['id']}")
        buttons.append(button)

    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:i+5])

    await message.reply(output, reply_markup=InlineKeyboardMarkup(keyboard))
    await bot.delete_messages(message.chat.id, [loading_msg.id])


# luuvan 的域名表；用来判断 /cmail 给的地址该交给哪个来源。
# 读不到时退回一份静态快照，保证离线/上游故障时也能判断。
_LUUVAN_FALLBACK_DOMAINS = {
    "n0ai.cloud",
    "animee.tokyo",
    "vibecoder.io.vn",
    "luuvan.site",
    "luuvan.online",
    "lhuniverse.io.vn",
    "locpnv.click",
    "edu.luuvan.site",
    "edu.animee.tokyo",
    "edu.chotroi.site",
}


def is_luuvan_address(address):
    """地址的域名是不是 luuvan 的（含 edu.* 那一整套子域）。"""
    domain = address.rsplit("@", 1)[-1].strip().lower()
    if not domain:
        return False
    known = set(luuvan.domains()) or _LUUVAN_FALLBACK_DOMAINS
    if domain in known:
        return True
    # k01.edu.animee.tokyo 这类子域按后缀匹配。
    return any(domain.endswith("." + d) for d in known)


async def manual_check_luuvan(user_id, message, loading_msg, address):
    """
    luuvan 按地址读信。

    不需要事先建号，也不需要 token —— 地址本身就是凭证，服务端是 catch-all。
    这正是发卡密要的路径：买家把卡密里的地址发进来就能读。
    """
    try:
        messages = luuvan.list_messages(address)
    except luuvan.LuuvanError as exc:
        await message.reply(t(user_id, "lv_read_failed", error=exc))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    user_tokens[user_id] = {"provider": "luuvan", "address": address}

    if not messages:
        await message.reply(t(user_id, "no_mail_alert"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    output = t(user_id, "inbox_header")

    buttons = []
    for idx, msg in enumerate(messages[:10], 1):
        output += t(
            user_id,
            "inbox_line",
            idx=idx,
            address=luuvan.sender_address(msg),
            subject=luuvan.subject(msg),
        )
        button = InlineKeyboardButton(f"{idx}", callback_data=f"read_{msg['id']}")
        buttons.append(button)

    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:i+5])

    await message.reply(output, reply_markup=InlineKeyboardMarkup(keyboard))
    await bot.delete_messages(message.chat.id, [loading_msg.id])


async def manual_check_vn(user_id, message, loading_msg, address):
    """
    按邮箱地址恢复读取（这个来源没有令牌，地址就是凭证）。
    地址不在账号池里时说明邮箱已被回收，直接告诉用户重新生成。
    """
    if not vnpool.available():
        await message.reply(t(user_id, "vn_not_configured"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    slot, mail_id = vnpool.resolve(address)
    if slot is None:
        await message.reply(t(user_id, "vn_mailbox_gone"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    api_key = vnpool.key_for(slot)
    if not api_key:
        await message.reply(t(user_id, "vn_not_configured"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    try:
        messages = tempmailedu.list_messages(api_key, mail_id)
    except tempmailedu.TempMailEduError as exc:
        await message.reply(t(user_id, vn_error_key(exc)))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    # 记进会话，后面点「1」「2」读信时才知道去哪儿取。
    user_tokens[user_id] = {
        "provider": "tempmailedu",
        "address": address,
        "slot": slot,
    }

    if not messages:
        await message.reply(t(user_id, "no_mail_alert"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    output = t(user_id, "inbox_header")

    buttons = []
    for idx, msg in enumerate(messages[:10], 1):
        output += t(
            user_id,
            "inbox_line",
            idx=idx,
            address=tempmailedu.sender_address(msg),
            subject=tempmailedu.subject(msg),
        )
        button = InlineKeyboardButton(f"{idx}", callback_data=f"read_{msg['id']}")
        buttons.append(button)

    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:i+5])

    await message.reply(output, reply_markup=InlineKeyboardMarkup(keyboard))
    await bot.delete_messages(message.chat.id, [loading_msg.id])

bot.run()
