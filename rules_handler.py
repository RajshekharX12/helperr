from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from uuid import uuid4

rules_data = {
    "cn": {
        "text": "🚫 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
        "accept": "✅ 接受规则",
        "accepted_by": "✅ 规则已被 {name} 接受"
    },
    "ru": {
        "text": "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
        "accept": "✅ Принять правила",
        "accepted_by": "✅ Правила приняты {name}"
    },
    "en": {
        "text": "🚫 Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n❗ Ending rental early = no refund",
        "accept": "✅ Accept Rules",
        "accepted_by": "✅ Rules accepted by {name}"
    },
    "kr": {
        "text": "🚫 엄격히 금지됩니다:\n• 사기, 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.\n❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 대여 종료 = 환불 불가",
        "accept": "✅ 규칙 동의",
        "accepted_by": "✅ {name} 님이 규칙에 동의했습니다"
    }
}

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.lower().strip()

    if query == "rules":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇨🇳 Chinese", callback_data="lang_cn"),
             InlineKeyboardButton("🇷🇺 Russian", callback_data="lang_ru")],
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
             InlineKeyboardButton("🇰🇷 Korean", callback_data="lang_kr")]
        ])
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="📘 Select Rules Language",
                input_message_content=InputTextMessageContent("Please select your preferred language for rules:"),
                reply_markup=keyboard
            )
        ]
        await update.inline_query.answer(results, cache_time=0)

async def accept_rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data.startswith("lang_"):
        return

    lang_code = data.split("_")[1]
    user_name = query.from_user.full_name

    if lang_code in rules_data:
        rules_text = rules_data[lang_code]["text"]
        accept_label = rules_data[lang_code]["accept"]
        accepted_by_text = rules_data[lang_code]["accepted_by"].format(name=user_name)

        keyboard = InlineKeyboardMarkup.from_button(
            InlineKeyboardButton(accept_label, callback_data=f"accept_{lang_code}_{query.from_user.id}")
        )

        await query.message.reply_text(rules_text, reply_markup=keyboard)

    elif data.startswith("accept_"):
        _, lang_code, uid = data.split("_")
        if lang_code in rules_data:
            user_name = query.from_user.full_name
            accepted_by_text = rules_data[lang_code]["accepted_by"].format(name=user_name)
            await query.message.reply_text(accepted_by_text)
