from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram import Update
from uuid import uuid4

# Rules in all 4 languages
RULES_TEXT = {
    "chinese": """🚫 严禁行为：
• 诈骗、欺诈、毒品、卡片欺诈、黑客行为
• 封禁账户/聊天/频道
• 敲诈、开盒、恶作剧报警、恐怖活动
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
• Пересдача номера третьим лицам

❗ Если номер получает ограничение на сайте — он изымается без возврата средств
❗ Нарушение правил = бан навсегда + без возврата
❗ Досрочное окончание аренды = без возврата""",

    "english": """🚫 Strictly forbidden:
• Scam, fraud, drugs, carding, hacking
• Blocking accounts/chats/channels
• Blackmail, doxing, swatting, terrorism
• Botnets, data leaks, hate speech
• Re-renting to others

❗ If the number gets restricted on the website, it will be taken back without refund
❗ Breaking rules = instant ban + no refund
❗ Ending rental early = no refund""",

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
    "chinese": "✅ 规则已被 {name} 接受",
    "russian": "✅ Правила приняты: {name}",
    "english": "✅ Rules accepted by {name}",
    "korean": "✅ 규칙을 수락함: {name}"
}

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower()
    if "rules" in query:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇨🇳 Chinese", callback_data="lang_chinese")],
            [InlineKeyboardButton("🇷🇺 Russian", callback_data="lang_russian")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_english")],
            [InlineKeyboardButton("🇰🇷 Korean", callback_data="lang_korean")]
        ])
        await update.inline_query.answer([
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="📜 View Rules",
                input_message_content=InputTextMessageContent("Please select your language:"),
                reply_markup=keyboard
            )
        ])

async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    lang_key = data.split("_")[1]

    rules_text = RULES_TEXT.get(lang_key)
    accepted_text = ACCEPTED_TEXT.get(lang_key).format(name=user.full_name)

    if rules_text:
        await query.message.reply_text(f"{rules_text}

{accepted_text}")
        await query.answer()
