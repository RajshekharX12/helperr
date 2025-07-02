
import logging
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import asyncio

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


def check_fragment_batch_selenium(numbers):
    results = []
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=chrome_options)

        for num in numbers:
            try:
                driver.get(f"https://fragment.com/number/{num}")
                content = driver.page_source
                if 'class="NotFound"' in content or "This number is not available" in content:
                    results.append((num, "🔒 Restricted"))
                else:
                    results.append((num, "✅ Free"))
            except Exception:
                results.append((num, "⚠️ Error"))

        driver.quit()
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

    results = await asyncio.to_thread(check_fragment_batch_selenium, numbers)
    date_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    result_text = f"📋 Fragment Check Result ({date_str}):\n\n"
    for idx, (number, status) in enumerate(sorted(results), 1):
        result_text += f"{idx}. {number}: {status}\n"

    if update.message:
        await update.message.reply_text(result_text)
    elif update.callback_query:
        await update.callback_query.message.reply_text(result_text)


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
    elif data == "gift":
        await query.message.reply_text("🖕")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == '__main__':
    main()
