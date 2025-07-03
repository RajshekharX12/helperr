
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

def get_inline_buttons(lang):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🇨🇳", callback_data="rules_chinese"),
        InlineKeyboardButton("🇷🇺", callback_data="rules_russian"),
        InlineKeyboardButton("🇺🇸", callback_data="rules_english"),
        InlineKeyboardButton("🇰🇷", callback_data="rules_korean"),
        InlineKeyboardButton("✅ Accept", callback_data=f"accept_{lang}")
    ]])

async def send_initial_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Send default rules in English
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=RULES_TEXT["english"],
        reply_markup=get_inline_buttons("english")
    )

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data.startswith("rules_"):
        lang = query.data.split("_")[1]
        await query.edit_message_text(
            text=RULES_TEXT.get(lang, "Rules not found."),
            reply_markup=get_inline_buttons(lang)
        )
    elif query.data.startswith("accept_"):
        lang = query.data.split("_")[1]
        user_name = query.from_user.full_name or query.from_user.username or "User"
        accepted_text = ACCEPTED_TEXT.get(lang, "✅ Accepted by: {name}").format(name=user_name)

        if query.message:
            await query.edit_message_text(text=accepted_text)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text=accepted_text)


from telegram.ext import InlineQueryHandler
from telegram import InlineQueryResultArticle, InputTextMessageContent
import re

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    # Must be 8 digits, starting from 1020 to 7020 concatenated
    if re.fullmatch(r"\d{4}\d{4}", query):
        part1 = int(query[:4])
        part2 = int(query[4:])
        if 1020 <= part1 <= 7020 and 1020 <= part2 <= 7020:
            number = f"888{query}"
            link = f"https://fragment.com/number/{number}/code"
            results = [
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"🔗 Link for {number}",
                    input_message_content=InputTextMessageContent(link),
                    description="Click to open fragment link"
                )
            ]
            await update.inline_query.answer(results, cache_time=0)


accept_rules_handler = rules_handler
