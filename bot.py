import logging
import time
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Global storage
tracked_numbers = {}
notifications_enabled = {}

# Selenium driver setup
def get_driver():
    options = Options()
    options.headless = True
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def check_fragment_number(number):
    url = f"https://fragment.com/number/{number}"
    driver = get_driver()
    try:
        driver.get(url)
        time.sleep(2)
        if "restricted on Telegram" in driver.page_source:
            result = "❌ Restricted"
        elif "Anonymous Number" in driver.page_source:
            result = "✅ Free"
        else:
            result = "⚠️ Unknown / Not Found"
    except Exception as e:
        result = f"⚠️ Error: {str(e)}"
    finally:
        driver.quit()
    return result

# Bot Commands
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Fragment +888 Checker Bot!\n\nCommands:\n"
        "/setnumbers 888xxxx,888yyyy\n/removenum 888xxx\n/checknum\n/check1 888xxx\n/notifyon\n/notifyoff"
    )

async def set_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    input_line = " ".join(context.args)
    clean = input_line.replace(" ", "").replace("\n", ",")
    numbers = list(set([x.strip() for x in clean.split(",") if x.strip().isdigit()]))
    if not numbers:
        await update.message.reply_text("❌ No valid numbers found.")
        return
    tracked_numbers[user_id] = list(set(tracked_numbers.get(user_id, []) + numbers))
    notifications_enabled[user_id] = True
    await update.message.reply_text(f"✅ Added {len(numbers)} numbers to your tracking list.")

async def remove_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not context.args:
        await update.message.reply_text("Usage: /removenum 888xxxx")
        return
    num = context.args[0]
    if user_id in tracked_numbers and num in tracked_numbers[user_id]:
        tracked_numbers[user_id].remove(num)
        await update.message.reply_text(f"❌ Removed {num} from your list.")
    else:
        await update.message.reply_text("❌ Number not found.")

async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    nums = tracked_numbers.get(user_id, [])
    if not nums:
        await update.message.reply_text("You have no numbers. Use /setnumbers first.")
        return
    await update.message.reply_text(f"🔎 Checking {len(nums)} numbers...")
    msg = ""
    for num in nums:
        result = check_fragment_number(num)
        msg += f"{num} → {result}\n"
        if len(msg) > 3500:
            await update.message.reply_text(msg)
            msg = ""
    if msg:
        await update.message.reply_text(msg)

async def check_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check1 888xxxx")
        return
    num = context.args[0]
    result = check_fragment_number(num)
    await update.message.reply_text(f"🔍 {num} → {result}")

async def notify_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    notifications_enabled[user_id] = True
    await update.message.reply_text("🔔 Auto-notifications enabled.")
async def notify_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    notifications_enabled[user_id] = False
    await update.message.reply_text("🔕 Auto-notifications disabled.")

# Background checker
def periodic_checker(application):
    while True:
        logging.info("[AUTO CHECK] Running...")
        for user_id, nums in tracked_numbers.items():
            if not notifications_enabled.get(user_id, True):
                continue
            msg = "🔔 Auto Check:\n"
            for num in nums:
                result = check_fragment_number(num)
                msg += f"{num} → {result}\n"
            try:
                application.bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                logging.warning(f"[ERROR] Failed to notify {user_id}: {e}")
        time.sleep(3 * 60 * 60)

# Main launcher
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setnumbers", set_numbers))
    app.add_handler(CommandHandler("removenum", remove_number))
    app.add_handler(CommandHandler("checknum", check_now))
    app.add_handler(CommandHandler("check1", check_single))
    app.add_handler(CommandHandler("notifyon", notify_on))
    app.add_handler(CommandHandler("notifyoff", notify_off))

    thread = Thread(target=periodic_checker, args=(app,), daemon=True)
    thread.start()

    app.run_polling()

# 🚨 Yeh galat tha: if name == 'main'
if name == 'main':
    main()
