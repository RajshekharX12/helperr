import logging
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from playwright.async_api import async_playwright
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
            f.write(num.strip() + "\n")

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
                    if "This number is not available" in content:
                        results.append((num, "Restricted"))
                    else:
                        results.append((num, "Free"))
                except Exception:
                    results.append((num, "Error"))
            await browser.close()
    except Exception:
        for num in numbers:
            results.append((num, "Error"))
    return results

def create_sheet(results):
    df = pd.DataFrame(results, columns=["Number", "Status"])
    df = df.sort_values("Number", ascending=True)
    filename = f"FragmentCheck_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    filepath = f"/tmp/{filename}"
    df.to_excel(filepath, index=False)
    return filepath

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data="set")],
        [InlineKeyboardButton("🔍 Check", callback_data="chk")],
        [InlineKeyboardButton("🧹 Clear", callback_data="clear")],
        [InlineKeyboardButton("🎁", callback_data="gift")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "🔥 Fragment +888 Checker Bot"
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=reply_markup)

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and context.args:
        numbers = ",".join(context.args).split(",")
        save_numbers(numbers)
        await update.message.reply_text("✅ Numbers saved.")
    elif update.callback_query:
        await update.callback_query.message.reply_text("Send /set 888xxxx,888yyyy")

async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    msg = f"🔍 Checking {len(numbers)} numbers..."
    if update.message:
        await update.message.reply_text(msg)
    elif update.callback_query:
        await update.callback_query.message.reply_text(msg)
    if not numbers:
        return
    results = await check_fragment_batch(numbers)
    filepath = create_sheet(results)
    if update.message:
        await update.message.reply_document(InputFile(filepath))
    elif update.callback_query:
        await update.callback_query.message.reply_document(InputFile(filepath))

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    await update.message.reply_text("🧹 All numbers cleared.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data == "set":
        await set_command(update, context)
    elif data == "chk":
        await chk_command(update, context)
    elif data == "clear":
        await clear_command(update, context)
    elif data == "gift":
        await query.message.reply_text("🎁 Gift feature coming soon!")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()