import logging
import os
import asyncio
import random
from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    InlineQueryHandler,
)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from rules_handler import inline_query_handler, get_rules_keyboard, handle_rules_button

# --- Setup ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "numbers.txt"
MAX_NUMBERS = 1000
CHECK_DELAY_SEC = 2.0  # 2–2.5s per number, safe for fragment.com

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helpers for storage ---
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

def split_results(results, chars_limit=4000):
    parts = []
    chunk = []
    total = 0
    for line in results:
        if total + len(line) + 1 > chars_limit and chunk:
            parts.append('\n'.join(chunk))
            chunk = []
            total = 0
        chunk.append(line)
        total += len(line) + 1
    if chunk:
        parts.append('\n'.join(chunk))
    return parts

# --- Selenium checker ---
def check_fragment_batch_selenium(numbers):
    """Check all numbers, with retry and safe delay. Dumps HTML for single number 'Error'."""
    results = []
    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    for num in numbers:
        for attempt in range(3):  # Retry up to 3 times if error
            try:
                driver.get(f"https://fragment.com/number/{num}")
                content = driver.page_source
                if "This phone number is restricted on Telegram" in content:
                    results.append((num, "🔒 Restricted"))
                elif "This number is not available" in content or 'class="NotFound"' in content:
                    results.append((num, "🔒 Not Found"))
                else:
                    results.append((num, "✅ Free"))
                # Debug HTML dump if only one number and error
                if len(numbers) == 1:
                    with open("debug_fragment.html", "w", encoding="utf-8") as f:
                        f.write(content)
                break
            except Exception as ex:
                if attempt == 2:
                    results.append((num, "⚠️ Error"))
                else:
                    import time; time.sleep(CHECK_DELAY_SEC + random.uniform(0.3, 0.7))
                    continue
        # Always sleep a bit between requests for safety
        import time; time.sleep(CHECK_DELAY_SEC + random.uniform(0.3, 0.7))
    driver.quit()
    return results

# --- Async message deletion ---
async def delete_message(message):
    try:
        await message.delete()
    except Exception:
        pass

# --- Bot commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data='set')],
        [InlineKeyboardButton("🔍 Check", callback_data='chk')],
        [InlineKeyboardButton("🧹 Clear", callback_data='clear')],
        [InlineKeyboardButton("❌ Delete", callback_data='delete')],
        [InlineKeyboardButton("🎁", callback_data='gift')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "🔥 Fragment +888 Checker Bot"
    try:
        await update.message.reply_text(msg, reply_markup=reply_markup)
        # Menu is never auto-deleted!
    except Exception as ex:
        logger.warning(f"start error: {ex}")

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        try:
            sent = await update.message.reply_text("Send /set 888xxxxxxx,888yyyyyyy")
        except Exception:
            return
        await delete_message(sent)
        await delete_message(update.message)
        return
    numbers = [x.strip() for x in ','.join(context.args).split(',') if x.strip().isdigit()]
    if not numbers:
        try:
            sent = await update.message.reply_text("No valid numbers found.")
        except Exception:
            return
        await delete_message(sent)
        await delete_message(update.message)
        return
    save_numbers(numbers)
    try:
        sent = await update.message.reply_text(f"✅ {len(numbers)} numbers saved.")
    except Exception:
        return
    await delete_message(sent)
    await delete_message(update.message)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    try:
        sent = await update.message.reply_text("🧹 All numbers cleared!")
    except Exception:
        return
    await delete_message(sent)
    await delete_message(update.message)

def format_numbers_result(results):
    lines = []
    for i, (num, status) in enumerate(results, 1):
        lines.append(f"{i}. {num} {status}")
    return lines

def filter_restricted(results):
    return [(num, status) for num, status in results if "Restricted" in status]

async def checknum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        try:
            sent = await update.message.reply_text("🚫 No numbers to check.")
        except Exception:
            return
        await delete_message(sent)
        await delete_message(update.message)
        return
    try:
        wait_msg = await update.message.reply_text("Checking numbers, please wait... This may take a while for large lists.")
    except Exception:
        wait_msg = None
    await delete_message(update.message)
    # Check ALL numbers, with batching/protection
    results = await asyncio.get_event_loop().run_in_executor(None, check_fragment_batch_selenium, numbers)
    context.user_data["last_check_results"] = results
    res_lines = format_numbers_result(results)
    parts = split_results(res_lines, chars_limit=3900)
    keyboard = [[InlineKeyboardButton("Show Restricted Only", callback_data="show_restricted")]]
    try:
        for idx, part in enumerate(parts):
            if idx == 0:
                await wait_msg.edit_text(part, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await wait_msg.reply_text(part)
    except Exception as ex:
        logger.warning(f"checknum_command error: {ex}")

async def check1_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        try:
            sent = await update.message.reply_text("Usage: /check1 888xxxxxxx")
        except Exception:
            return
        await delete_message(sent)
        await delete_message(update.message)
        return
    num = context.args[0].strip()
    if not num.isdigit():
        try:
            sent = await update.message.reply_text("Enter a valid number.")
        except Exception:
            return
        await delete_message(sent)
        await delete_message(update.message)
        return
    results = await asyncio.get_event_loop().run_in_executor(None, check_fragment_batch_selenium, [num])
    context.user_data["last_check_results"] = results
    res_lines = format_numbers_result(results)
    try:
        msg = await update.message.reply_text('\n'.join(res_lines))
    except Exception:
        return
    await delete_message(update.message)

# --- Callback handler ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    try:
        if data == "chk":
            await checknum_command(query, context)
        elif data == "clear":
            await clear_command(query, context)
        elif data == "delete":
            try:
                await query.message.delete()
            except Exception:
                pass
        elif data == "show_restricted":
            results = context.user_data.get("last_check_results", [])
            only_restricted = filter_restricted(results)
            res_lines = format_numbers_result(only_restricted) if only_restricted else ["No restricted numbers found."]
            parts = split_results(res_lines, chars_limit=3900)
            for idx, part in enumerate(parts):
                if idx == 0:
                    await query.message.edit_text(part)
                else:
                    await query.message.reply_text(part)
        elif data.startswith("accept_rules_"):
            await handle_rules_button(update, context)
        else:
            sent = await query.message.reply_text("Unknown action.")
            await delete_message(sent)
    except Exception as ex:
        logger.warning(f"button_callback error: {ex}")

async def error_handler(update, context):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("checknum", checknum_command))
    app.add_handler(CommandHandler("check1", check1_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_error_handler(error_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
