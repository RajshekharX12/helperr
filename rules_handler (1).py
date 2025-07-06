
from telegram import InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from uuid import uuid4
import re

def extract_888_number(user_input: str) -> str:
    digits_only = re.sub(r'\D', '', user_input)
    if digits_only.startswith("888"):
        return digits_only
    return f"888{digits_only}"

async def handle_inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    results = []

    if query.lower() == "rules":
        buttons = [
            [InlineKeyboardButton("🇨🇳 Chinese", switch_inline_query_current_chat="rules_zh")],
            [InlineKeyboardButton("🇷🇺 Russian", switch_inline_query_current_chat="rules_ru")],
            [InlineKeyboardButton("🇺🇸 English", switch_inline_query_current_chat="rules_en")],
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
        lang_texts = {
            "zh": "🚫 严禁行为：\n• 诈骗、欺诈、毒品、卡片欺诈、黑客行为\n• 封禁账户/聊天/频道\n• 敲诈、开盒、恶作剧报警、恐怖活动\n• 僵尸网络、数据泄露、仇恨言论\n• 转租号码给他人\n\n❗ 如果号码在网站上被限制，将被收回且不予退款\n❗ 违反规定 = 永久封禁 + 不退款\n❗ 提前终止租用 = 不退款",
            "ru": "🚫 Строго запрещено:\n• Мошенничество, обман, наркотики, кардинг, взлом\n• Блокировка аккаунтов/чатов/каналов\n• Шантаж, деанон, сваттинг, терроризм\n• Ботнеты, утечки данных, разжигание ненависти\n• Пересдача номера третьим лицам\n\n❗ Если номер получает ограничение на сайте — он изымается без возврата средств\n❗ Нарушение правил = бан навсегда + без возврата\n❗ Досрочное окончание аренды = без возврата",
            "en": "🚫 Strictly forbidden:\n• Scam, fraud, drugs, carding, hacking\n• Blocking accounts/chats/channels\n• Blackmail, doxing, swatting, terrorism\n• Botnets, data leaks, hate speech\n• Re-renting to others\n\n❗ If the number gets restricted on the website, it will be taken back without refund\n❗ Breaking rules = instant ban + no refund\n❗ Ending rental early = no refund",
            "ko": "🚫 엄격히 금지됩니다:\n• 사기, 마약, 카드 사용, 해킹\n• 계정/채팅/채널 차단\n• 협박, 신상 털기, 스와팅, 테러\n• 봇넷, 데이터 유출, 증오 표현\n• 타인에게 재대여\n\n❗ 웹사이트에서 제한이 발생할 경우 환불 없이 회수됩니다.\n❗ 규칙 위반 = 즉시 사용 금지 + 환불 불가\n❗ 조기 종료 = 환불 불가"
        }
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="📜 Rules (" + lang.upper() + ")",
                input_message_content=InputTextMessageContent(lang_texts.get(lang, "Unknown language")),
            )
        )
    elif re.search(r"\d{4,}", query):
        number = extract_888_number(query)
        link = f"https://fragment.com/number/{number}/code"
        results.append(
            InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"🔗 Generate Link for {number}",
                input_message_content=InputTextMessageContent(link),
                description="Click to get the Fragment code link.",
            )
        )

    await update.inline_query.answer(results[:10])
