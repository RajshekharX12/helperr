
import logging
import os
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
)
from dotenv import load_dotenv
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
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for number in numbers:
            try:
                url = f"https://fragment.com/number/{number}"
                await page.goto(url, timeout=60000)
                content = await page.content()
                status = "Free" if "This number is available" in content else "Restricted"
            except:
                status = "Error"
            results.append((number, status))
        await browser.close()
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
        [InlineKeyboardButton("🎁", callback_data="gift")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔥 Fragment +888 Checker Bot",
        reply_markup=reply_markup
    )

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Provide numbers: /set 888xxxx,888yyyy")
        return
    numbers = [x.strip() for x in " ".join(context.args).replace(",", " ").split()]
    save_numbers(numbers)
    await update.message.reply_text(f"✅ Saved {len(numbers)} numbers.")

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
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=InputFile(filepath)
    )

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    await update.message.reply_text("🧹 All numbers cleared.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data == "set":
        await query.message.reply_text("Send /set 888xxxx,888yyyy")
    elif data == "chk":
        await chk_command(update, context)
    elif data == "clear":
        await clear_command(update, context)
    elif data == "gift":
        await query.message.reply_text("🖕")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()
