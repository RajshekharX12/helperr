import logging
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from uuid import uuid4
import asyncio

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    InlineQueryHandler
)

from playwright.async_api import async_playwright

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "numbers.txt"
MAX_NUMBERS = 1000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_numbers(numbers):
    numbers = sorted(set(numbers))
    with open(DATA_FILE, "w") as f:
        for num in numbers[:MAX_NUMBERS]:
            f.write(f"{num}\n")


def load_numbers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def clear_numbers():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)


async def check_fragment_batch(numbers):
    results = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            for num in numbers:
                try:
                    await page.goto(f"https://fragment.com/number/{num}")
                    await page.wait_for_timeout(1000)
                    content = await page.content()
                    if "This phone number is restricted on Telegram" in content:
                        results.append((num, "🔒"))
                    else:
                        results.append((num, "✅"))
                except Exception:
                    results.append((num, "⚠️"))
            await browser.close()
    except Exception:
        for num in numbers:
            results.append((num, "⚠️"))
    return results


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data="set")],
        [InlineKeyboardButton("🔍 Check", callback_data="chk")],
        [InlineKeyboardButton("🧹 Clear", callback_data="clear")],
        [InlineKeyboardButton("🎁 Gift", callback_data="gift")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "🔥 Fragment +888 Checker Bot"
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)


async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Send /set 888xxxxxxx,888yyyyyyy")
        return
    numbers = [x.strip().replace("+", "") for x in ','.join(context.args).split(',') if x.strip().isdigit()]
    if not numbers:
        await update.message.reply_text("No valid numbers found.")
        return
    save_numbers(numbers)
    await update.message.reply_text(f"✅ {len(numbers)} numbers saved.")


async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        await update.message.reply_text("❌ No numbers to check.")
        return

    msg = await update.message.reply_text(f"🔍 Checking {len(numbers)} numbers...")
    await asyncio.sleep(5)
    await msg.delete()

    results = await check_fragment_batch(numbers)
    date_str = datetime.now().strftime("%d-%m-%Y %H:%M")
    result_text = f"📋 Fragment Check Result ({date_str}):\n\n"

    for idx, (number, status) in enumerate(sorted(results), 1):
        result_text += f"{idx}. {number}: {status}\n"

    keyboard = [[InlineKeyboardButton("🔒 Get Restricted Numbers", callback_data="get_restricted")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(result_text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "set":
        await query.message.reply_text("Send /set 888xxxxxxx,888yyyyyyy")
    elif data == "chk":
        await chk_command(update, context)
    elif data == "clear":
        clear_numbers()
        await query.message.reply_text("🧹 All numbers cleared.")
    elif data == "get_restricted":
        numbers = load_numbers()
        results = await check_fragment_batch(numbers)
        restricted = [num for num, status in results if status == "🔒"]
        if not restricted:
            await query.message.reply_text("✅ No restricted numbers.")
        else:
            await query.message.reply_text("🔒 Restricted Numbers:\n" + "\n".join(restricted))


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    if query.lower() == "rules":
        await show_rules(update)
        return

    digits = ''.join(filter(str.isdigit, query))
    if len(digits) >= 7:
        if not digits.startswith("888"):
            digits = "888" + digits
        link = f"https://fragment.com/number/{digits}/code"
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"Generate Link for {digits}",
            input_message_content=InputTextMessageContent(link)
        )
        await update.inline_query.answer([result])
    else:
        await update.inline_query.answer([])


async def show_rules(update: Update):
    rules = {
        "🇨🇳 中文": (
            "🚫 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n"
            "• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n"
            "❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款", "接受规则")
        ,
        "🇷🇺 Russian": (
            "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n"
            "• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n"
            "❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n"
            "❗ Досрочное окончание аренды = без возврата", "Принять правила")
        ,
        "🇺🇸 English": (
            "🚫 Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n"
            "• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n"
            "❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n"
            "❗ Ending rental early = no refund", "Accept Rules")
        ,
        "🇰🇷 Korean": (
            "🚫 엄격히 금지됩니다:\n• 사기, 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n"
            "• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.\n"
            "❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 대여 종료 = 환불 불가", "규칙 동의")
    }

    for lang, (text, btn_label) in rules.items():
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(btn_label, callback_data=f"accepted_{lang}")]
        ])
        await update.inline_query.from_user.send_message(text=lang + "\n" + text, reply_markup=keyboard)


async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang = query.data.split("_", 1)[1]
    name = query.from_user.first_name
    await query.answer(f"{name} accepted the rules.")
    await query.edit_message_reply_markup(
        InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ Accepted by: {name}", callback_data="none")]])
    )


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(set|chk|clear|get_restricted|gift)$"))
    app.add_handler(CallbackQueryHandler(accept_rules_handler, pattern="^accepted_"))
    app.add_handler(InlineQueryHandler(inline_query_handler))

    app.run_polling()


if __name__ == "__main__":
    main()