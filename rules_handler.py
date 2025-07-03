from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent, Update
from telegram.ext import ContextTypes
from datetime import datetime
import uuid

RULES = {
    "🇨🇳 Chinese": "🚫 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
    "🇷🇺 Russian": "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
    "🇺🇸 English": "🚫 Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n❗ Ending rental early = no refund",
    "🇰🇷 Korean": "🚫 엄격히 금지됩니다:\n• 사기, 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 사용 인원 제한이 발생할 경우 환불 없이 회수됩니다.\n❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 대여 종료 = 환불 불가"
}

async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip().lower()
    results = []

    if query == "rules":
        for lang, rules in RULES.items():
            accept_button = InlineKeyboardButton(text="✅ Accept Rules", callback_data=f"accept_rules:{lang}")
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title=f"{lang} Rules",
                    input_message_content=InputTextMessageContent(rules),
                    reply_markup=InlineKeyboardMarkup([[accept_button]])
                )
            )
    elif query.replace("+", "").isdigit():
        number = query.replace("+", "")
        if not number.startswith("888"):
            number = "888" + number
        url = f"https://fragment.com/number/{number}/code"
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title=f"Generate Link for {number}",
                input_message_content=InputTextMessageContent(url),
                description="Click to copy fragment code link"
            )
        )

    await update.inline_query.answer(results, cache_time=1)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer("✅ Accepted", show_alert=False)  # early reply to Telegram
        data = query.data
        user = update.effective_user.full_name
        lang = data.split(":")[1] if ":" in data else ""

        if data.startswith("accept_rules:"):
            try:
                await query.edit_message_text(f"✅ {user} accepted rules", reply_markup=None)
            except Exception as e:
                print(f"Edit failed: {e}")
            with open("rules_accept_log.txt", "a", encoding="utf-8") as log_file:
                log_file.write(f"{datetime.now().isoformat()} - Accepted by: {user} ({lang})\n")

    except Exception as e:
        print(f"[ERROR] In button_handler: {e}")
