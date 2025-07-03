
import logging
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, InlineQueryHandler

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import uuid
import asyncio
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
                        results.append((num, "🔒 Restricted"))
                    else:
                        results.append((num, "✅"))
                except Exception:
                    results.append((num, "⚠️ Error"))
            await browser.close()
    except Exception:
        for num in numbers:
            results.append((num, "⚠️ Error"))
    return results


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data='set')],
        [InlineKeyboardButton("🔍 Check", callback_data='chk')],
        [InlineKeyboardButton("🧹 Clear", callback_data='clear')],
        [InlineKeyboardButton("🎁", callback_data='gift')]
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

    numbers = [x.strip() for x in ','.join(context.args).split(',') if x.strip().isdigit()]
    if not numbers:
        await update.message.reply_text("No valid numbers found.")
        return

    save_numbers(numbers)
    await update.message.reply_text(f"✅ {len(numbers)} numbers saved.")


async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    msg = f"🔍 Checking {len(numbers)} numbers..."

    if update.message:
        status_msg = await update.message.reply_text(msg)
    elif update.callback_query:
        status_msg = await update.callback_query.message.reply_text(msg)
    else:
        return

    await asyncio.sleep(5)
    try:
        await status_msg.delete()
    except:
        pass

    if not numbers:
        return

    results = await check_fragment_batch(numbers)
    date_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
result_text = f"📋 Fragment Check Result ({date_str}):\n\n"

    for idx, (number, status) in enumerate(sorted(results), 1):
        result_text += f"{idx}. {number}: {status}

    keyboard = [[InlineKeyboardButton("🔒 Get Restricted Numbers", callback_data="get_restricted")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(result_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(result_text, reply_markup=reply_markup)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()

    msg_target = update.message or update.callback_query.message
    if msg_target:
        await msg_target.reply_text("🧹 All numbers cleared.")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "set":
        await query.message.reply_text("Send /set 888xxxxxxx,888yyyyyyy")
    elif data == "chk":
        await chk_command(update, context)
    elif data == "clear":
        await clear_command(update, context)
    elif data == "get_restricted":
        numbers = load_numbers()
        results = await check_fragment_batch(numbers)
        restricted = [f"{i+1}. {n}: {s}" for i, (n, s) in enumerate(sorted(results)) if "Restricted" in s]
        msg = "🔒 Restricted Numbers:

" + "
".join(restricted) if restricted else "✅ No restricted numbers found."
        await query.message.reply_text(msg)
    elif data.startswith("accept_rules:"):
        name = update.effective_user.full_name
        await query.message.edit_text(f"✅ Accepted by: {name}")
    elif data == "gift":
        await query.message.reply_text("🖕")


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    results = []

    if query == "rules":
        rules_data = [
            ("🇨🇳 Chinese Rules", "🚫 严禁行为：
• 诈骗、欺诈、毒品...
❗ 如果号码在网站上被限制，将被收回且不予退款", "接受规则"),
            ("🇷🇺 Russian Rules", "🚫 Строго запрещено:
• Мошенничество...
❗ Нарушение правил = бан навсегда", "Принять правила"),
            ("🇬🇧 English Rules", "🚫 Strictly forbidden:
• Scam, fraud...
❗ Breaking rules = instant ban + no refund", "Accept Rules"),
            ("🇰🇷 Korean Rules", "🚫 엄격히 금지됩니다:
• 사기, 마약...
❗ 조기 대여 종료 = 환불 불가", "규칙 동의"),
        ]
        for title, text, button_label in rules_data:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=title,
                    input_message_content=InputTextMessageContent(text),
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f"✅ {button_label}", callback_data=f"accept_rules:{title}")]])
                )
            )

    elif query:
        query = query.replace("+", "").replace(" ", "")
        if not query.startswith("888"):
            query = "888" + query.lstrip("0")
        url = f"https://fragment.com/number/{query}/code"
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"Code Link for {query}",
                input_message_content=InputTextMessageContent(url),
                description="Click to send fragment.com code link",
            )
        )

    await update.inline_query.answer(results, cache_time=1)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.run_polling()


if __name__ == '__main__':
    main()