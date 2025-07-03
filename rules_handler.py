from telegram import InlineQueryResultArticle, InputTextMessageContent, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from uuid import uuid4

# Rules in all 4 languages
RULES_TEXT = {
    "chinese": """🚫 严禁行为:
• 诈骗、欺诈、毒品、卡片欺诈、黑客行为
• 封禁账户/聊天/频道
• 欺诈、开盒、恶作剧报警、恐怖活动
• 僵尸网络、数据泄露、仇恨言论
• 转租号码给他人

❗ 如果号码在网站上被限制，将被收回且不予退款
❗ 违反规定 = 永久封禁 + 不退款
❗ 提前终止租用 = 不退款""",

    "russian": """🚫 Строго запрещено:
• Мошенничество, обман, наркотики, кардинг, взлом
• Блокировка аккаунтов/чатов/каналов
• Шантаж, деанон, сваттинг, терроризм
• Ботнеты, утечки данных, разжигание ненависти
• Передача номера третьим лицам

❗ Если номер получает ограничение на сайте — он изымается без возврата средств
❗ Нарушение правил = бан навсегда + без возврата
❗ Досрочное окончание аренды = без возврата""",

    "english": """🚫 Strictly Prohibited:
• Fraud, scams, drugs, carding, hacking
• Banned accounts/chats/channels
• Blackmail, doxxing, swatting, terrorism
• Botnets, data leaks, hate speech
• Reselling numbers to others

❗ If the number is restricted on the site, it is revoked with no refund
❗ Rule violation = permanent ban + no refund
❗ Early termination of rental = no refund""",

    "korean": """🚫 엄격히 금지됩니다:
• 사기, 사기, 마약, 카드 사용, 해킹
• 계정/채팅/채널 차단
• 협박, 신상 털기, 스와팅, 테러
• 봇넷, 데이터 유출, 증오 표현
• 타인에게 재대여

❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.
❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가
❗ 조기 대여 종료 = 환불 불가"""
}

LANG_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("🇨🇳 Chinese", callback_data="rules_chinese")],
    [InlineKeyboardButton("🇷🇺 Russian", callback_data="rules_russian")],
    [InlineKeyboardButton("🇺🇸 English", callback_data="rules_english")],
    [InlineKeyboardButton("🇰🇷 Korean", callback_data="rules_korean")],
])

ACCEPT_BUTTONS = {
    "chinese": InlineKeyboardMarkup([[InlineKeyboardButton("✅ 接受规则", callback_data="accept_chinese")]]),
    "russian": InlineKeyboardMarkup([[InlineKeyboardButton("✅ Принять правила", callback_data="accept_russian")]]),
    "english": InlineKeyboardMarkup([[InlineKeyboardButton("✅ Accept Rules", callback_data="accept_english")]]),
    "korean": InlineKeyboardMarkup([[InlineKeyboardButton("✅ 규칙 수락", callback_data="accept_korean")]]),
}

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title="📘 View Rules in Multiple Languages",
            input_message_content=InputTextMessageContent("🌐 Choose your language below:"),
            reply_markup=LANG_BUTTONS
        )
    ]
    await update.inline_query.answer(results)

async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    language = query.data.split("_")[1]
    user_name = query.from_user.full_name or query.from_user.username or "a user"
    await query.message.reply_text(f"✅ Rules accepted by: {user_name}")
