
import logging
import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from playwright.sync_api import sync_playwright

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
        return sorted(set(line.strip() for line in f if line.strip()))

def clear_numbers():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

def check_fragment_batch(numbers):
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        for num in numbers:
            try:
                page.goto(f"https://fragment.com/number/{num}", timeout=10000)
                content = page.content()
                if "currently restricted" in content.lower():
                    results.append((num, "Restricted"))
                else:
                    results.append((num, "Free"))
            except Exception as e:
                results.append((num, "Error"))
        browser.close()
    return results

def create_sheet(results):
    df = pd.DataFrame(results, columns=["Number", "Status"])
    df = df.sort_values("Number", ascending=True)
    filename = f"FragmentCheck_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    filepath = f"/tmp/{filename}"
    df.to_excel(filepath, index=False)
    return filepath

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data='set')],
        [InlineKeyboardButton("🔍 Check", callback_data='chk')],
        [InlineKeyboardButton("🧹 Clear", callback_data='clear')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Fragment +888 Checker Bot\n\n"
        "Commands:\n"
        "/set 888xxxx,888yyyy\n"
        "/chk\n"
        "/clear",
        reply_markup=reply_markup
    )

# /set
async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Provide numbers: /set 888xxxx,888yyyy")
        return
    numbers = [x.strip() for x in " ".join(context.args).replace(",", " ").split()]
    if len(numbers) > MAX_NUMBERS:
        await update.message.reply_text(f"⚠️ Max {MAX_NUMBERS} numbers allowed.")
        return
    save_numbers(numbers)
    await update.message.reply_text(f"✅ Saved {len(numbers)} numbers.")

# /chk
async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        await update.message.reply_text("⚠️ No numbers saved. Use /set first.")
        return
    await update.message.reply_text(f"🔍 Checking {len(numbers)} numbers...")

    results = check_fragment_batch(numbers)
    filepath = create_sheet(results)
    await update.message.reply_document(InputFile(filepath))

# /clear
async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    await update.message.reply_text("🧹 All numbers cleared.")

# inline button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "set":
        await query.message.reply_text("Use /set 888xxxx,888yyyy to add numbers.")
    elif query.data == "chk":
        await chk_command(update, context)
    elif query.data == "clear":
        await clear_command(update, context)

# bot setup
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("set", set_command))
app.add_handler(CommandHandler("chk", chk_command))
app.add_handler(CommandHandler("clear", clear_command))
app.add_handler(CallbackQueryHandler(button_handler))

if __name__ == "__main__":
    app.run_polling()
