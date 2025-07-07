import logging
import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime

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

from playwright.sync_api import sync_playwright
from uuid import uuid4

from rules_handler import inline_query_handler, get_rules_keyboard, handle_rules_button

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "numbers.txt"
MAX_NUMBERS = 1000
# Telegram allows ~30 messages/sec per bot, but we use much much less for safety
CHECK_DELAY_SEC = 0.7    # 0.7s between number checks = ~1.4 per sec

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

def check_fragment_batch_playwright(numbers, limit=40):
    """Check numbers using Playwright, with delays to avoid rate limits.
    Limit default: 40 numbers per request (polite to Fragment and Telegram)"""
    results = []
    # Only check up to limit at once
    to_check = numbers[:limit]
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            for num in to_check:
                try:
                    page.goto(f"https://fragment.com/number/{num}", timeout=10000)
                    content = page.content()
                    if "This phone number is restricted on Telegram" in content:
                        results.append((num, "🔒 Restricted"))
                    elif "This number is not available" in content or 'class="NotFound"' in content:
                        results.append((num, "🔒 Not Found"))
                    else:
                        results.append((num, "✅ Free"))
                except Exception:
                    results.append((num, "⚠️ Error"))
                # Delay to avoid hammering either endpoint
                import time
                time.sleep(CHECK_DELAY_SEC)
            browser.close()
    except Exception:
        for num in to_check:
            results.append((num, "⚠️ Error"))
    return results

async def delete_later(context, chat_id, message_id, delay=5):
    await asyncio.sleep(delay)
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass

async def send_and_auto_delete(ctx, txt, reply_markup=None, delay=5):
    msg = await ctx.message.reply_text(txt, reply_markup=reply_markup)
    asyncio.create_task(delete_later(ctx, ctx.message.chat_id, msg.message_id, delay=delay))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data='set')],
        [InlineKeyboardButton("🔍 Check", callback_data='chk')],
        [InlineKeyboardButton("🧹 Clear", callback_data='clear')],
        [InlineKeyboardButton("🎁", callback_data='gift')]
        # No "Rules" button here!
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = "🔥 Fragment +888 Checker Bot"
    try:
        sent = await update.message.reply_text(msg, reply_markup=reply_markup)
        asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
    except Exception as ex:
        logger.warning(f"start error: {ex}")

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        try:
            sent = await update.message.reply_text("Send /set 888xxxxxxx,888yyyyyyy")
            asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
        except Exception:
            pass
        return
    numbers = [x.strip() for x in ','.join(context.args).split(',') if x.strip().isdigit()]
    if not numbers:
        try:
            sent = await update.message.reply_text("No valid numbers found.")
            asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
        except Exception:
            pass
        return
    save_numbers(numbers)
    try:
        sent = await update.message.reply_text(f"✅ {len(numbers)} numbers saved.")
        asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
    except Exception:
        pass

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    try:
        sent = await update.message.reply_text("🧹 All numbers cleared!")
        asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
    except Exception:
        pass

def format_numbers_result(results):
    lines = []
    for i, (num, status) in enumerate(results, 1):
        lines.append(f"{i}. {num} {status}")
    return "\n".join(lines)

def filter_restricted(results):
    return [(num, status) for num, status in results if "Restricted" in status]

async def checknum_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        try:
            sent = await update.message.reply_text("🚫 No numbers to check.")
            asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
        except Exception:
            pass
        return
    try:
        wait_msg = await update.message.reply_text("Checking numbers, please wait...")
    except Exception:
        wait_msg = None
    # Limit to 40 per check to avoid API ban
    results = check_fragment_batch_playwright(numbers)
    context.user_data["last_check_results"] = results
    res_txt = format_numbers_result(results)
    keyboard = [
        [InlineKeyboardButton("Show Restricted Only", callback_data="show_restricted")]
    ]
    try:
        sent = await update.message.reply_text(res_txt, reply_markup=InlineKeyboardMarkup(keyboard))
        if wait_msg:
            asyncio.create_task(delete_later(context, update.message.chat_id, wait_msg.message_id, delay=0))
        # Don't delete the result message!
    except Exception as ex:
        logger.warning(f"checknum_command error: {ex}")

async def check1_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        try:
            sent = await update.message.reply_text("Usage: /check1 888xxxxxxx")
            asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
        except Exception:
            pass
        return
    num = context.args[0].strip()
    if not num.isdigit():
        try:
            sent = await update.message.reply_text("Enter a valid number.")
            asyncio.create_task(delete_later(context, update.message.chat_id, sent.message_id))
        except Exception:
            pass
        return
    results = check_fragment_batch_playwright([num])
    context.user_data["last_check_results"] = results
    res_txt = format_numbers_result(results)
    try:
        sent = await update.message.reply_text(res_txt)
        # Don't delete result
    except Exception:
        pass

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    try:
        if data == "chk":
            await checknum_command(query, context)
        elif data == "clear":
            await clear_command(query, context)
        elif data == "show_restricted":
            results = context.user_data.get("last_check_results", [])
            only_restricted = filter_restricted(results)
            res_txt = format_numbers_result(only_restricted) if only_restricted else "No restricted numbers found."
            await query.message.edit_text(res_txt)
        elif data.startswith("accept_rules_"):
            await handle_rules_button(update, context)
        else:
            sent = await query.message.reply_text("Unknown action.")
            asyncio.create_task(delete_later(context, query.message.chat_id, sent.message_id))
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
