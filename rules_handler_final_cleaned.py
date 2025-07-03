
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from uuid import uuid4

# Language-specific rules
RULES = {
    "chinese": {
        "text": "🚫 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
        "accepted": "✅ 规则已被 {name} 接受"
    },
    "russian": {
        "text": "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
        "accepted": "✅ Правила приняты: {name}"
    },
    "english": {
        "text": "🚫 Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n❗ Ending rental early = no refund",
        "accepted": "✅ Rules accepted by {name}"
    },
    "korean": {
        "text": "🚫 엄격히 금지됩니다:\n• 사기, 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.\n❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 대여 종료 = 환불 불가",
        "accepted": "✅ 규칙이 {name}에 의해 수락되었습니다"
    }
}

# Handler for inline query
async def handle_inline_query(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()

    if "rules" in query:
        results = [
            InlineQueryResultArticle(
                id=uuid4(),
                title="🇨🇳 Chinese",
                input_message_content=InputTextMessageContent(RULES["chinese"]["text"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ 接受规则", callback_data="accept_chinese")]])
            ),
            InlineQueryResultArticle(
                id=uuid4(),
                title="🇷🇺 Russian",
                input_message_content=InputTextMessageContent(RULES["russian"]["text"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Принять правила", callback_data="accept_russian")]])
            ),
            InlineQueryResultArticle(
                id=uuid4(),
                title="🇺🇸 English",
                input_message_content=InputTextMessageContent(RULES["english"]["text"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ Accept Rules", callback_data="accept_english")]])
            ),
            InlineQueryResultArticle(
                id=uuid4(),
                title="🇰🇷 Korean",
                input_message_content=InputTextMessageContent(RULES["korean"]["text"]),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✅ 규칙 수락", callback_data="accept_korean")]])
            )
        ]
        await update.inline_query.answer(results, cache_time=0)

# Callback handler when rules are accepted
async def accept_rules_handler(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.replace("accept_", "")
    name = query.from_user.full_name
    accepted_text = RULES[lang]["accepted"].format(name=name)

    await query.message.reply_text(accepted_text)
