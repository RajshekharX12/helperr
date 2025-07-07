from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from uuid import uuid4
import re

LANGS = {
    "en": "English",
    "ru": "Russian",
    "zh": "Chinese",
    "ko": "Korean"
}

RULES_TEXTS = {
    "en": "❫ Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n❗ Ending rental early = no refund",
    "ru": "❫ Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
    "zh": "❫ 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开箱、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
    "ko": "❫ 엄격히 금지됩니다:\n• 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 제한이 발생할 경우 환불 없이 회수됩니다.\n❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 종료 = 환불 불가"
}

def get_rules_keyboard(lang, username=None):
    texts = {
        "en": "Accept rules",
        "ru": "Принять правила",
        "zh": "接受规则",
        "ko": "규칙 수락"
    }
    btn_text = f"✅ Rules accepted by {username}" if username else texts[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(btn_text, callback_data=f"accept_rules_{lang}")]
    ])

def normalize_fragment_number(query: str) -> str | None:
    digits = re.sub(r"\D", "", query)
    if digits.startswith("888") and len(digits) == 12:
        return digits
    nums = re.findall(r"\d+", query)
    combined = "".join(nums)
    if 7 <= len(combined) <= 9:
        return "888" + combined.zfill(9)
    return None

async def inline_query_handler(update, context):
    query = update.inline_query.query.strip()
    results = []

    if query.lower() == "rules" or query.lower() == "@checker_888_bot rules":
        buttons = [
            [InlineKeyboardButton("🇬🇧 English", switch_inline_query_current_chat="rules_en")],
            [InlineKeyboardButton("🇷🇺 Russian", switch_inline_query_current_chat="rules_ru")],
            [InlineKeyboardButton("🇨🇳 Chinese", switch_inline_query_current_chat="rules_zh")],
            [InlineKeyboardButton("🇰🇷 Korean", switch_inline_query_current_chat="rules_ko")],
        ]
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="📜 Select Language to View Rules",
                input_message_content=InputTextMessageContent("Please choose a language below to view the rules."),
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        )
    elif query.lower().startswith("rules_"):
        lang = query.lower().split("_")[1]
        text = RULES_TEXTS.get(lang, "Unknown language")
        keyboard = get_rules_keyboard(lang)
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"📜 Rules ({LANGS[lang]})",
                input_message_content=InputTextMessageContent(text),
                reply_markup=keyboard
            )
        )
    else:
        number = normalize_fragment_number(query)
        if number and len(number) == 12 and number.startswith("888"):
            url = f"https://fragment.com/number/{number}/code"
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid4()),
                    title=f"Fragment: {number}",
                    input_message_content=InputTextMessageContent(url),
                    description=f"Link to fragment.com/number for {number}",
                    url=url,
                )
            )

    await update.inline_query.answer(results)

async def handle_rules_button(update, context):
    query = update.callback_query
    user = query.from_user
    display_name = user.full_name or user.username or "Unknown"
    lang = query.data.split("_")[-1]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Rules accepted by {display_name}", callback_data=f"accept_rules_{lang}")]
    ])
    text = f"✅ Rules accepted by {display_name}"

    if query.message:
        await query.message.edit_text(text, reply_markup=keyboard)
    await query.answer()
