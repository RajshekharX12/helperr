
import logging, os
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes
from datetime import datetime
from uuid import uuid4
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "numbers.txt"
MAX_NUMBERS = 1000

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Save numbers to file
def save_numbers(numbers):
    numbers = sorted(set(numbers))
    with open(DATA_FILE, "w") as f:
        for num in numbers[:MAX_NUMBERS]:
            f.write(f"{num}\n")

# Load numbers from file
def load_numbers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]

# Clear all saved numbers
def clear_numbers():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# Accept rules text translations
RULES_TRANSLATIONS = {
    "en": "✅ Accepted by: {name}",
    "ru": "✅ Принято: {name}",
    "zh": "✅ 接受者: {name}",
    "kr": "✅ 수락자: {name}"
}

# Inline language selection handler
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    results = []

    if query == "rules":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇨🇳 Chinese", callback_data="rules_zh")],
            [InlineKeyboardButton("🇷🇺 Russian", callback_data="rules_ru")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="rules_en")],
            [InlineKeyboardButton("🇰🇷 Korean", callback_data="rules_kr")]
        ])
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title="📜 Select Your Language",
            input_message_content=InputTextMessageContent("Please select a language to view rules."),
            reply_markup=keyboard
        ))

    elif query.strip().replace("+", "").isdigit():
        number = query.strip().replace("+", "")
        if not number.startswith("888"):
            number = "888" + number
        url = f"https://fragment.com/number/{number}/code"
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title=f"🔗 Generate Link for {number}",
            input_message_content=InputTextMessageContent(url)
        ))

    await update.inline_query.answer(results, cache_time=1)

# Rules handler
async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data.split("_")[1]
    user = update.callback_query.from_user
    await update.callback_query.answer()

    messages = {
        "en": "🚫 Strictly forbidden: ...",
        "ru": "🚫 Строго запрещено: ...",
        "zh": "🚫 严禁行为: ...",
        "kr": "🚫 엄격히 금지됩니다: ..."
    }

    accept_button = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept Rules", callback_data=f"accept_{lang}")]
    ])

    await update.callback_query.message.reply_text(messages[lang], reply_markup=accept_button)

# Accept rules
async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = update.callback_query.data.split("_")[1]
    user_name = update.callback_query.from_user.first_name
    msg = RULES_TRANSLATIONS.get(lang, "✅ Accepted by: {name}").format(name=user_name)
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    await update.callback_query.message.reply_text(msg)

# Command handlers
async def set_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = context.args
    save_numbers(numbers)
    await update.message.reply_text("✅ Numbers saved.")

async def chk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        await update.message.reply_text("No numbers saved.")
        return

    status_dict = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for num in numbers[:MAX_NUMBERS]:
            url = f"https://fragment.com/number/{num}/code"
            await page.goto(url)
            content = await page.content()
            status = "Restricted" if "Number not found" in content else "Free"
            status_dict[num] = status

        await browser.close()

    sorted_results = sorted(status_dict.items())
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"fragment_result_{now}.txt"

    with open(filename, "w") as f:
        for num, status in sorted_results:
            f.write(f"{num}	{status}\n")

    with open(filename, "rb") as f:
        await update.message.reply_document(f, filename=filename)

async def clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    await update.message.reply_text("🧹 All numbers cleared.")

# Main
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.add_handler(CallbackQueryHandler(rules_handler, pattern="^rules_"))
    app.add_handler(CallbackQueryHandler(accept_rules_handler, pattern="^accept_"))
    app.add_handler(CommandHandler("set", set_handler))
    app.add_handler(CommandHandler("chk", chk_handler))
    app.add_handler(CommandHandler("clear", clear_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
