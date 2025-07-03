
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ContextTypes
from uuid import uuid4
import re

# Rules in 4 languages
RULES_TEXT = {
    "chinese": "🚫 严禁行为:\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被回回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
    "russian": "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Передача номера третьим лицам\n\n❗ Если номер получает ограничение — он изымается без возврата\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
    "english": "🚫 Strictly Prohibited:\n• Fraud, scam, drugs, carding, hacking\n• Account/chat/channel bans\n• Blackmail, doxxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Reselling number to others\n\n❗ Number restriction = no refund\n❗ Violation = permanent ban + no refund\n❗ Early rental end = no refund",
    "korean": "🚫 엄격히 금지됩니다:\n• 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 제한 발생 시 환불 없이 회수\n❗ 규칙 위반 = 영구 정지 + 환불 없음\n❗ 조기 종료 = 환불 없음"
}

ACCEPTED_TEXT = {
    "chinese": "✅ 已接受规则：{name}",
    "russian": "✅ Принято: {name}",
    "english": "✅ Accepted by: {name}",
    "korean": "✅ 규칙 수락: {name}"
}

async def send_initial_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=RULES_TEXT["english"],
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Accept Rules", callback_data="accept_english")
        ]])
    )

async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data.startswith("accept_"):
        lang = query.data.split("_")[1]
        user_name = query.from_user.full_name or query.from_user.username or "User"
        accepted_text = ACCEPTED_TEXT.get(lang, "✅ Accepted by: {name}").format(name=user_name)

        if query.message:
            await query.edit_message_text(text=accepted_text)
        else:
            await context.bot.send_message(chat_id=query.from_user.id, text=accepted_text)

# Inline query handler for 888 link generation
async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

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

# Exported name
accept_rules_handler = rules_handler
