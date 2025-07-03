from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from uuid import uuid4

# Rules text in different languages
RULES_TEXTS = {
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
        "• 사기, 사기, 마약, 카드 사용, 해킹\n"
        "• 계정/채팅/채널 차단\n"
        "• 협박, 신상 털기, 스와팅, 테러\n"
        "• 봇넷, 데이터 유출, 증오 표현\n"
        "• 타인에게 재대여\n\n"
        "❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.\n"
        "❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n"
        "❗ 조기 대여 종료 = 환불 불가"
    ),
}

ACCEPT_LABELS = {
    "🇨🇳 Chinese": "✅ 接受规则",
    "🇷🇺 Russian": "✅ Принять правила",
    "🇺🇸 English": "✅ Accept Rules",
    "🇰🇷 Korean": "✅ 규칙 수락"
}

CONFIRMATION_MESSAGES = {
    "🇨🇳 Chinese": "✅ 已接受规则：{name}",
    "🇷🇺 Russian": "✅ Правила приняты: {name}",
    "🇺🇸 English": "✅ Rules accepted by: {name}",
    "🇰🇷 Korean": "✅ 규칙을 수락함: {name}"
}

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    if "rules" in query:
        result = InlineQueryResultArticle(
            id=str(uuid4()),
            title="📜 View +888 Rules",
            description="Choose your language to view the rules",
            input_message_content=InputTextMessageContent("📜 Select your language:"),
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🇨🇳 Chinese", callback_data="rules_chinese"),
                    InlineKeyboardButton("🇷🇺 Russian", callback_data="rules_russian")
                ],
                [
                    InlineKeyboardButton("🇺🇸 English", callback_data="rules_english"),
                    InlineKeyboardButton("🇰🇷 Korean", callback_data="rules_korean")
                ]
            ])
        )
        await update.inline_query.answer([result], cache_time=0)

async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    lang_map = {
        "rules_chinese": "🇨🇳 Chinese",
        "rules_russian": "🇷🇺 Russian",
        "rules_english": "🇺🇸 English",
        "rules_korean": "🇰🇷 Korean"
    }
    if query.data not in lang_map:
        return
    language = lang_map[query.data]
    rules_text = RULES_TEXTS[language]
    accept_label = ACCEPT_LABELS[language]

    await query.message.reply_text(
        f"{rules_text}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(accept_label, callback_data=f"accept_{query.data}")]
        ])
    )
    await query.answer()

async def confirm_accept_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_name = query.from_user.full_name
    lang_key = query.data.replace("accept_", "")
    language = {
        "rules_chinese": "🇨🇳 Chinese",
        "rules_russian": "🇷🇺 Russian",
        "rules_english": "🇺🇸 English",
        "rules_korean": "🇰🇷 Korean"
    }.get(lang_key, "🇺🇸 English")
    confirmation = CONFIRMATION_MESSAGES[language].format(name=user_name)

    await query.message.reply_text(confirmation)
    await query.answer()
