
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import InlineQueryHandler, CallbackQueryHandler
from uuid import uuid4

accepted_users = {
    "cn": [],
    "ru": [],
    "en": [],
    "kr": []
}

rules_texts = {
    "cn": "🚫 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
    "ru": "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
    "en": "🚫 Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n❗ Ending rental early = no refund",
    "kr": "🚫 엄격히 금지됩니다:\n• 사기, 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.\n❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 대여 종료 = 환불 불가"
}

accepted_by_texts = {
    "cn": "✅ 已接受规则：{}",
    "ru": "✅ Правила приняты: {}",
    "en": "✅ Rules accepted by: {}",
    "kr": "✅ 규칙을 수락한 사용자: {}"
}

def rules_inline_query(update, context):
    query = update.inline_query.query.lower()
    if "rules" in query:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇨🇳 Chinese", callback_data="rules_cn")],
            [InlineKeyboardButton("🇷🇺 Russian", callback_data="rules_ru")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="rules_en")],
            [InlineKeyboardButton("🇰🇷 Korean", callback_data="rules_kr")]
        ])
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="📜 View Rules",
                input_message_content=InputTextMessageContent("Select your language to view the rules:"),
                reply_markup=keyboard
            )
        ]
        update.inline_query.answer(results)

def rules_callback(update, context):
    query = update.callback_query
    lang_code = query.data.split("_")[1]
    user_name = query.from_user.full_name
    rules = rules_texts.get(lang_code)
    accept_text = {
        "cn": "✅ 接受规则",
        "ru": "✅ Принять правила",
        "en": "✅ Accept Rules",
        "kr": "✅ 규칙 수락"
    }[lang_code]
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(accept_text, callback_data=f"accept_{lang_code}")]
    ])
    query.message.reply_text(rules, reply_markup=keyboard)

def rules_accept_callback(update, context):
    query = update.callback_query
    lang_code = query.data.split("_")[1]
    user_name = query.from_user.full_name
    accepted_text = accepted_by_texts.get(lang_code, "Rules accepted by: {}").format(user_name)
    query.message.reply_text(accepted_text)
