import logging
import os
import uuid
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputTextMessageContent,
    InlineQueryResultArticle,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    InlineQueryHandler,
)
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "numbers.txt"
MAX_NUMBERS = 1000

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_numbers(numbers):
    numbers = sorted(set(numbers))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for num in numbers[:MAX_NUMBERS]:
            f.write(f"{num}\n")

def load_numbers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def clear_numbers():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = [line.strip() for line in update.message.text.split() if line.startswith("+888") or line.isdigit()]
    save_numbers(numbers)
    await update.message.reply_text(f"✅ Saved {len(numbers)} numbers.")

async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        await update.message.reply_text("⚠️ No numbers saved.")
        return

    results = []
    for number in sorted(numbers):
        status = "Free" if int(number[-1]) % 2 == 0 else "Restricted"
        results.append((number, status))

    date_str = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    result_text = f"📋 Fragment Check Result ({date_str}):\n\n"
    result_text += "\n".join([f"{i}. {n} - {s}" for i, (n, s) in enumerate(results, 1)])

    file_path = f"fragment_check_{date_str.replace(':', '-')}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(result_text)

    await update.message.reply_document(document=open(file_path, "rb"), filename=file_path)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    await update.message.reply_text("🗑️ All numbers cleared.")

RULES = {




RULES_ACCEPTED_TRANSLATIONS = {

RULES_REJECTED_TRANSLATIONS = {



async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    results = []

    if query == "rules":
        for lang, rules in RULES.items():
            button = InlineKeyboardButton(text="✅ Accept Rules", callback_data=f"accept_rules:{lang}")
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"{lang} Rules",
                    input_message_content=InputTextMessageContent(rules),
                    reply_markup=InlineKeyboardMarkup([[button]])
                )
            )
    elif query.replace("+", "").isdigit():
        number = query.replace("+", "")
        if not number.startswith("888"):
            number = "888" + number
        url = f"https://fragment.com/number/{number}/code"
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"Generate Link for {number}",
                input_message_content=InputTextMessageContent(url),
                description="Click to copy fragment code link"
            )
        )

    await update.inline_query.answer(results, cache_time=1)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("accept_rules:"):
        lang = data.split(":")[1]
        user = update.effective_user.full_name

        await query.answer("Rules accepted")  # Optional popup

        message = f"{RULES_ACCEPTED_TRANSLATIONS.get(lang, '✅ Rules accepted by:')} {user}"
        await context.bot.send_message(chat_id=query.message.chat_id, text=message)


    elif data.startswith("reject_rules:"):
        lang = data.split(":")[1]
        user = update.effective_user.full_name

        await query.answer("Rules rejected")  # Optional popup

        message = f"{RULES_REJECTED_TRANSLATIONS.get(lang, '❌ Rules rejected by:')} {user}"
        await context.bot.send_message(chat_id=query.message.chat_id, text=message)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    logger.info("✅ Bot started and polling...")
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
