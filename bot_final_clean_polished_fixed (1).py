import logging
import os
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv
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
from playwright.async_api import async_playwright

# Load environment
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "numbers.txt"
MAX_NUMBERS = 1000

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helpers for storing numbers ---
def save_numbers(numbers):
    nums = sorted(set(numbers))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        for n in nums[:MAX_NUMBERS]:
            f.write(f"{n}\n")

def load_numbers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def clear_numbers():
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)

# --- Bot commands ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Set", callback_data="set")],
        [InlineKeyboardButton("🔍 Check", callback_data="chk")],
        [InlineKeyboardButton("🧹 Clear", callback_data="clear")],
        [InlineKeyboardButton("🎁 Gift", callback_data="gift")],
    ]
    await (update.message or update.callback_query.message).reply_text(
        "🔥 Fragment +888 Checker Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # parse numbers from message text
    parts = update.message.text.split()
    numbers = []
    for p in parts[1:]:
        p = p.replace("+", "")
        if p.isdigit():
            if not p.startswith("888"):
                p = "888" + p.lstrip("0")
            numbers.append(p)
    if not numbers:
        await update.message.reply_text("❌ No valid numbers provided.")
    else:
        save_numbers(numbers)
        await update.message.reply_text(f"✅ Saved {len(numbers)} numbers.")

async def chk_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = load_numbers()
    if not numbers:
        await update.message.reply_text("⚠️ No numbers saved.")
        return

    status_msg = await update.message.reply_text(f"🔍 Checking {len(numbers)} numbers...")
    await asyncio.sleep(5)
    await status_msg.delete()

    # perform checks
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for num in numbers:
            try:
                await page.goto(f"https://fragment.com/number/{num}")
                await page.wait_for_timeout(1000)
                html = await page.content()
                if "This phone number is restricted on Telegram" in html:
                    results.append((num, "🔒 Restricted"))
                else:
                    results.append((num, "✅ Free"))
            except:
                results.append((num, "⚠️ Error"))
        await browser.close()

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f"📋 Fragment Check Result ({date_str}):\n\n"
    text += "\n".join([f"{i}. {n}: {s}" for i,(n,s) in enumerate(results,1)])
    keyboard = [[InlineKeyboardButton("🔒 Get Restricted", callback_data="get_restricted")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_numbers()
    await update.message.reply_text("🗑️ All numbers cleared.")

# --- Inline query: rules and link generator ---
RULES = {
    "🇨🇳 Chinese": (
        "🚫 严禁行为：\n"
        "• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n"
        "• 封禁账户/聊天/频道\n"
        "• 敲诈、开盒、恶作剧报警、恐怖活动\n"
        "• 僵尸网络、数据泄露、仇恨言论\n"
        "• 转租号码给他人\n\n"
        "❗ 如果号码在网站上被限制，将被收回且不予退款\n"
        "❗ 违反规定 = 永久封禁 + 不退款\n"
        "❗ 提前终止租用 = 不退款"
    ),
    "🇷🇺 Russian": (
        "🚫 Строго запрещено:\n"
        "• Мошенничество, обман, наркотики, кардинг, взлом\n"
        "• Блокировка аккаунтов/чатов/каналов\n"
        "• Шантаж, деанон, сваттинг, терроризм\n"
        "• Ботнеты, утечки данных, разжигание ненависти\n"
        "• Пересдача номера третьим лицам\n\n"
        "❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n"
        "❗ Нарушение правил = бан навсегда + без возврата\n"
        "❗ Досрочное окончание аренды = без возврата"
    ),
    "🇺🇸 English": (
        "🚫 Strictly forbidden:\n"
        "• Scam, fraud, drugs, carding, hacking\n"
        "• Blocking accounts/chats/channels\n"
        "• Blackmail, doxing, swatting, terrorism\n"
        "• Botnets, data leaks, hate speech\n"
        "• Re-renting to others\n\n"
        "❗ If the number gets restricted on the website, it will be taken back without refund\n"
        "❗ Breaking rules = instant ban + no refund\n"
        "❗ Ending rental early = no refund"
    ),
    "🇰🇷 Korean": (
        "🚫 엄격히 금지됩니다:\n"
        "• 사기, 마약, 카드 사용, 해킹\n"
        "• 계정/채팅/채널 차단\n"
        "• 협박, 신상 털기, 스와팅, 테러\n"
        "• 봇넷, 데이터 유출, 증오 표현\n"
        "• 타인에게 재대여\n\n"
        "❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불없이 회수됩니다.\n"
        "❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n"
        "❗ 조기 대여 종료 = 환불 불가"
    ),
}

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.inline_query.query.strip().lower()
    results = []
    # rules
    if q == "rules":
        for lang,text in RULES.items():
            btn = InlineKeyboardButton("✅ Accept Rules", callback_data=f"accept_rules:{lang}")
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"{lang} Rules",
                    input_message_content=InputTextMessageContent(text),
                    reply_markup=InlineKeyboardMarkup([[btn]])
                )
            )
    # number link
    elif q.replace("+","").isdigit():
        d = q.replace("+","")
        if not d.startswith("888"):
            d = "888"+d.lstrip("0")
        url = f"https://fragment.com/number/{d}/code"
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"Link for {d}",
                input_message_content=InputTextMessageContent(url),
                description="Tap to copy code link"
            )
        )
    await update.inline_query.answer(results, cache_time=1)

# --- Callback for rules acceptance ---
async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split(":",1)[1]
    user = update.effective_user.full_name
    msg_map = {
        "🇨🇳 Chinese": f"✅ 已接受规则：{user}",
        "🇷🇺 Russian":   f"✅ Правила приняты: {user}",
        "🇺🇸 English":   f"✅ Accepted by: {user}",
        "🇰🇷 Korean":    f"✅ 규칙 동의됨: {user}",
    }
    await query.message.reply_text(msg_map.get(lang, f"✅ Accepted by: {user}"))

# Extra button handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cmd = query.data
    fake_update = Update(update.update_id, message=query.message)
    if cmd == "set":
        await set_command(fake_update, context)
    elif cmd == "chk":
        await chk_command(fake_update, context)
    elif cmd == "clear":
        await clear_command(fake_update, context)
    elif cmd == "gift":
        await query.message.reply_text("🎁 Gift feature coming soon!")
    elif cmd == "get_restricted":
        numbers = load_numbers()
        restricted = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            for num in numbers:
                await page.goto(f"https://fragment.com/number/{num}")
                await page.wait_for_timeout(1000)
                html = await page.content()
                if "This phone number is restricted on Telegram" in html:
                    restricted.append(num)
            await browser.close()
        if restricted:
            await query.message.reply_text("🔒 Restricted Numbers:
" + "
".join(restricted))
        else:
            await query.message.reply_text("✅ No restricted numbers found.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set", set_command))
    app.add_handler(CommandHandler("chk", chk_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CallbackQueryHandler(accept_rules_handler, pattern="^accept_rules:"))
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(set|chk|clear|get_restricted|gift)$"))
    app.add_handler(InlineQueryHandler(inline_query_handler))
    app.run_polling()

if __name__ == "__main__":
    main()
