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
    if len(args) == 1 and ':' in args[0]:
        username, password = args[0].split(':')
    else:
        username = generate_random_username()
        password = generate_random_password()

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

    time.sleep(2)

    token = get_token(email, password)
    if not token:
        await message.reply(t(user_id, "token_failed"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    short_id = short_id_generator(email)
    token_map[short_id] = token

    output_message = t(user_id, "mail_details", email=email, password=password, token=token)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(t(user_id, "btn_check_mail"), callback_data=f"check_{short_id}")]])

    await message.reply(output_message, reply_markup=keyboard)
    await bot.delete_messages(message.chat.id, [loading_msg.id])

@bot.on_callback_query(filters.regex(r'^check_'))
async def check_mail(client, callback_query):
    user_id = callback_query.from_user.id
    short_id = callback_query.data.split('_')[1]
    token = token_map.get(short_id)
    if not token:
        await callback_query.message.reply(t(user_id, "session_expired"))
        return

    user_tokens[user_id] = token

    messages = list_messages(token)
    if not messages:
        await callback_query.answer(t(user_id, "no_mail_alert"), show_alert=True)
        return

    loading_msg = await callback_query.message.reply(t(user_id, "loading_mail"))

    output = t(user_id, "inbox_header")

    buttons = []
    for idx, msg in enumerate(messages[:10], 1):
        output += t(user_id, "inbox_line", idx=idx, address=msg['from']['address'], subject=msg['subject'])
        button = InlineKeyboardButton(f"{idx}", callback_data=f"read_{msg['id']}")
        buttons.append(button)

    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:i+5])

    await callback_query.message.reply(output, reply_markup=InlineKeyboardMarkup(keyboard))
    await bot.delete_messages(callback_query.message.chat.id, [loading_msg.id])

@bot.on_callback_query(filters.regex(r"^close_message"))
async def close_message(client, callback_query):
    await callback_query.message.delete()

@bot.on_callback_query(filters.regex(r"^read_"))
async def read_message(client, callback_query):
    user_id = callback_query.from_user.id
    message_id = callback_query.data.split('_')[1]
    token = user_tokens.get(user_id)

    if not token:
        await callback_query.message.reply(t(user_id, "token_not_found"))
        return

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


@bot.on_message(filters.command('cmail'))
async def manual_check_mail(client, message):
    user_id = message.from_user.id
    if message.chat.type != ChatType.PRIVATE:
        await message.reply(t(user_id, "private_only"))
        return

    loading_msg = await message.reply(t(user_id, "loading_mail"))

    token = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not token:
        await message.reply(t(user_id, "provide_token"))
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    user_tokens[user_id] = token
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

bot.run()
