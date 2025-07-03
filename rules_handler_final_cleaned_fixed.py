
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from uuid import uuid4

# Rules in 4 languages
RULES_TEXT = {
    "chinese": """🚫 严禁行为:

• 诈骗、欺诈、毒品、卡片欺诈、黑客行为
• 封禁账户/聊天/频道
• 敲诈、开盒、恶作剧报警、恐怖活动
• 僵尸网络、数据泄露、仇恨言论
• 转租号码给他人

❗ 如果号码在网站上被限制，将被回回且不予退款
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

• Fraud, scam, drugs, carding, hacking
• Account/chat/channel bans
• Blackmail, doxxing, swatting, terrorism
• Botnets, data leaks, hate speech
• Reselling number to others

❗ Number restriction = no refund
❗ Violation = permanent ban + no refund
❗ Early rental end = no refund""",
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

ACCEPTED_TEXT = {
    "chinese": "✅ 已接受规则：{name}",
    "russian": "✅ Принято: {name}",
    "english": "✅ Accepted by: {name}",
    "korean": "✅ 규칙 수락: {name}"
}

LANGUAGE_BUTTONS = [
    [InlineKeyboardButton("🇨🇳 Chinese", callback_data="rules_chinese")],
    [InlineKeyboardButton("🇷🇺 Russian", callback_data="rules_russian")],
    [InlineKeyboardButton("🇺🇸 English", callback_data="rules_english")],
    [InlineKeyboardButton("🇰🇷 Korean", callback_data="rules_korean")]
]


async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    if query.lower() == "rules":
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="View Rules in Multiple Languages",
                input_message_content=InputTextMessageContent("🌐 Choose your language below:"),
                reply_markup=InlineKeyboardMarkup(LANGUAGE_BUTTONS)
            )
        ]
        await update.inline_query.answer(results, cache_time=0)
    elif query.isdigit() or (query.startswith("888") and query[3:].isdigit()):
        number = query if query.startswith("888") else f"888{query}"
        link = f"https://fragment.com/number/{number}/code"
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="🔗 Generated Link",
                input_message_content=InputTextMessageContent(link),
                description="Tap to open fragment link"
            )
        ]
        await update.inline_query.answer(results, cache_time=0)


async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data.startswith("rules_"):
        lang = query.data.split("_")[1]
        rules_text = RULES_TEXT.get(lang, "Rules not found.")
        await query.message.reply_text(rules_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Accept Rules", callback_data=f"accept_{lang}")]
        ]))
    elif query.data.startswith("accept_"):
        lang = query.data.split("_")[1]
        user_name = query.from_user.full_name or query.from_user.username or "User"
        accepted_text = ACCEPTED_TEXT.get(lang, "✅ Accepted by: {name}").format(name=user_name)

        if query.message:
            await query.message.reply_text(accepted_text)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text=accepted_text)
