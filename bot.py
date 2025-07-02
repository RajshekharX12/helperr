import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          CallbackQueryHandler)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from threading import Thread
from dotenv import load_dotenv

# Load .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Data persistence file
DATA_FILE = "data.json"

# Global storage
tracked_numbers = {}
notifications_enabled = {}
last_check_results = {}

# Load saved data
def load_data():
    global tracked_numbers, notifications_enabled
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            tracked_numbers = data.get("tracked_numbers", {})
            notifications_enabled = data.get("notifications_enabled", {})

# Save current data
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"tracked_numbers": tracked_numbers,
                   "notifications_enabled": notifications_enabled}, f)

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
    keyboard = [[
        InlineKeyboardButton("📍 Check Now", callback_data='check_now'),
        InlineKeyboardButton("🔄 Update Bot", callback_data='update_bot'),
        InlineKeyboardButton("🗑️ Clear All", callback_data='clear_all')
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to Fragment +888 Checker Bot!\n\nUse /setnumbers to save your numbers.\n/checknum to manually check your list.",
        reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'check_now':
        await check_now(update, context)
    elif query.data == 'update_bot':
        await update_bot(update, context)
    elif query.data == 'clear_all':
        await clear_all(update, context)

async def set_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    input_line = " ".join(context.args)
    clean = input_line.replace(" ", "").replace("\n", ",")
    numbers = list(set([x.strip() for x in clean.split(",") if x.strip().isdigit()]))
    if not numbers:
        await update.message.reply_text("❌ No valid numbers found.")
        return
    tracked_numbers[user_id] = list(set(tracked_numbers.get(user_id, []) + numbers))
    save_data()
    await update.message.reply_text(f"✅ Saved {len(numbers)} numbers.")

async def remove_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /removenum 888xxxx")
        return
    num = context.args[0]
    if user_id in tracked_numbers and num in tracked_numbers[user_id]:
        tracked_numbers[user_id].remove(num)
        save_data()
        await update.message.reply_text(f"❌ Removed {num} from your list.")
    else:
        await update.message.reply_text("❌ Number not found.")

async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    user_id = str(update.effective_user.id)
    nums = tracked_numbers.get(user_id, [])
    if not nums:
        await update.effective_message.reply_text("❌ No numbers to check. Use /setnumbers.")
        return
    await update.effective_message.reply_text(f"🔎 Checking {len(nums)} numbers...")
    msg = ""
    for num in nums:
        result = check_fragment_number(num)
        msg += f"{num} → {result}\n"
        if len(msg) > 3500:
            await update.effective_message.reply_text(msg)
            msg = ""
    if msg:
        await update.effective_message.reply_text(msg)

async def check_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check1 888xxxx")
        return
    num = context.args[0]
    result = check_fragment_number(num)
    await update.message.reply_text(f"🔍 {num} → {result}")

async def notify_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    notifications_enabled[user_id] = True
    save_data()
    await update.message.reply_text("🔔 Auto-notifications enabled.")

async def notify_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    notifications_enabled[user_id] = False
    save_data()
    await update.message.reply_text("🔕 Auto-notifications disabled.")

async def update_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subprocess.run(["git", "pull"])
    await update.effective_message.reply_text("✅ Bot updated from GitHub.")

async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    user_id = str(update.effective_user.id)
    tracked_numbers[user_id] = []
    notifications_enabled[user_id] = False
    save_data()
    await update.effective_message.reply_text("🗑️ All your tracked numbers cleared.")

async def my_status(update: Update, context: ContextTypes.DEFAULT_TYPE, query=None):
    user_id = str(update.effective_user.id)
    nums = tracked_numbers.get(user_id, [])
    notify = notifications_enabled.get(user_id, False)
    msg = f"📊 You have {len(nums)} numbers tracked.\n🔔 Notifications: {'ON' if notify else 'OFF'}"
    await update.effective_message.reply_text(msg)

# Main launcher
def main():
    load_data()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setnumbers", set_numbers))
    app.add_handler(CommandHandler("removenum", remove_number))
    app.add_handler(CommandHandler("checknum", check_now))
    app.add_handler(CommandHandler("check1", check_single))
    app.add_handler(CommandHandler("notifyon", notify_on))
    app.add_handler(CommandHandler("notifyoff", notify_off))
    app.add_handler(CommandHandler("updatebot", update_bot))
    app.add_handler(CommandHandler("mystatus", my_status))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == '__main__':
    main()
