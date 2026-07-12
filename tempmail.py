# Author (C) @theSmartBisnu
# Channel : https://t.me/itsSmartDev

import os
import re
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
    welcome_message = (
        "**欢迎使用临时邮箱机器人！** 🎉\n\n"
        "你可以使用以下命令来管理临时邮箱地址：\n\n"
        "➢ `/tmail` - 随机生成一个临时邮箱和密码。\n"
        "➢ `/tmail [用户名]:[密码]` - 使用指定的用户名和密码生成邮箱。\n"
        "➢ `/cmail [邮箱令牌]` - 使用令牌查看最近的 10 封邮件。\n\n"
        "✨ **提示：** 生成邮箱和密码后，你会获得一个邮箱令牌（token）。"
        "该令牌可用于查看该临时邮箱收到的最近 10 封邮件。"
        "每个邮箱的令牌都不同，请妥善保管，不要泄露给他人。🛡️"
    )
    await message.reply(welcome_message)


@bot.on_message(filters.command('tmail'))
async def generate_mail(client, message):
    if message.chat.type != ChatType.PRIVATE:
        await message.reply("**请在私聊中使用此机器人。**")
        return

    loading_msg = await message.reply("**正在生成临时邮箱...**")

    args_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    args = args_text.split()
    if len(args) == 1 and ':' in args[0]:
        username, password = args[0].split(':')
    else:
        username = generate_random_username()
        password = generate_random_password()

    domain = get_domain()
    if not domain:
        await message.reply("**获取域名失败，请重试**")
        await bot.delete_messages(message.chat.id, [loading_msg.message_id])
        return

    email = f"{username}@{domain}"
    account = create_account(email, password)
    if not account:
        await message.reply("**用户名已被占用，请换一个。**")
        await bot.delete_messages(message.chat.id, [loading_msg.message_id])
        return

    time.sleep(2)

    token = get_token(email, password)
    if not token:
        await message.reply("**获取令牌失败。**")
        await bot.delete_messages(message.chat.id, [loading_msg.message_id])
        return

    short_id = short_id_generator(email)
    token_map[short_id] = token

    output_message = (
        "**📧 智能邮箱详情 📧**\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"**📧 邮箱：** `{email}`\n"
        f"**🔑 密码：** `{password}`\n"
        f"**🔒 令牌：** `{token}`\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "**提示：请保管好令牌，用于查看邮件**"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton("查看邮件", callback_data=f"check_{short_id}")]])

    await message.reply(output_message, reply_markup=keyboard)
    await bot.delete_messages(message.chat.id, [loading_msg.id])

@bot.on_callback_query(filters.regex(r'^check_'))
async def check_mail(client, callback_query):
    short_id = callback_query.data.split('_')[1]
    token = token_map.get(short_id)
    if not token:
        await callback_query.message.reply("**会话已过期，请使用 /cmail 命令并提供你的令牌。**")
        return

    user_tokens[callback_query.from_user.id] = token

    messages = list_messages(token)
    if not messages:
        await callback_query.answer("暂无邮件 ❌", show_alert=True)
        return

    loading_msg = await callback_query.message.reply("**⏳ 正在查看邮件，请稍候。**")

    output = "**📧 你的智能邮箱消息 📧**\n"
    output += "**━━━━━━━━━━━━━━━━━━**\n"

    buttons = []
    for idx, msg in enumerate(messages[:10], 1):
        output += f"{idx}. 发件人：`{msg['from']['address']}` - 主题：{msg['subject']}\n"
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
    message_id = callback_query.data.split('_')[1]
    token = user_tokens.get(callback_query.from_user.id)

    if not token:
        await callback_query.message.reply("**未找到令牌，请重新使用 /cmail 命令并提供你的令牌。**")
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
            message_text = "暂无可显示的内容。"

        # Truncate the message if it's too long
        if len(message_text) > MAX_MESSAGE_LENGTH:
            message_text = message_text[:MAX_MESSAGE_LENGTH - 100] + "...【内容已截断】"

        output = f"**发件人：** `{details['from']['address']}`\n**主题：** `{details['subject']}`\n━━━━━━━━━━━━━━━━━━\n{message_text}"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("关闭", callback_data="close_message")]
        ])

        sent_message = await callback_query.message.reply(output, disable_web_page_preview=True, reply_markup=keyboard)

    else:
        await callback_query.message.reply("**获取邮件详情失败。**")


@bot.on_message(filters.command('cmail'))
async def manual_check_mail(client, message):
    if message.chat.type != ChatType.PRIVATE:
        await message.reply("**请在私聊中使用此机器人。**")
        return

    loading_msg = await message.reply("**⏳ 正在查看邮件，请稍候。**")

    token = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""
    if not token:
        await message.reply("**请在 /cmail 命令后提供令牌。**")
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    user_tokens[message.from_user.id] = token
    messages = list_messages(token)
    if not messages:
        await message.reply("**❌ 未找到邮件，或令牌错误**")
        await bot.delete_messages(message.chat.id, [loading_msg.id])
        return

    output = "**📧 你的智能邮箱消息 📧**\n"
    output += "**━━━━━━━━━━━━━━━━━━**\n"

    buttons = []
    for idx, msg in enumerate(messages[:10], 1):
        output += f"{idx}. 发件人：{msg['from']['address']} - 主题：{msg['subject']}\n"
        button = InlineKeyboardButton(f"{idx}", callback_data=f"read_{msg['id']}")
        buttons.append(button)

    keyboard = []
    for i in range(0, len(buttons), 5):
        keyboard.append(buttons[i:i+5])

    await message.reply(output, reply_markup=InlineKeyboardMarkup(keyboard))
    await bot.delete_messages(message.chat.id, [loading_msg.id])

bot.run()
