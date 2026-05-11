import os
from collections import defaultdict

from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))

SYSTEM_PROMPT = (
    "Тебя зовут Змей. Ты простой ИИ-собеседник в Telegram. "
    "Отвечай по-русски, коротко, немного глуповато, но дружелюбно. "
    "Не пиши большие тексты. Обычно 1-3 коротких предложения. "
    "Без сложных слов и без списков, если пользователь прямо не попросил. "
    "Если не уверен, честно скажи простыми словами."
)

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Нет TELEGRAM_BOT_TOKEN в .env")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("Нет DEEPSEEK_API_KEY в .env")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
history_by_chat_id: dict[int, list[dict[str, str]]] = defaultdict(list)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("привет, я Змей. пиши че-нибудь, я отвечу")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history_by_chat_id.pop(update.effective_chat.id, None)
    await update.message.reply_text("память стер, я чистый змей")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

    history_by_chat_id[chat_id].append({"role": "user", "content": user_text})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history_by_chat_id[chat_id][-MAX_HISTORY_MESSAGES:]

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=messages,
            temperature=0.9,
            max_tokens=250,
            extra_body={"thinking": {"type": "disabled"}},
        )
        answer = (response.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"DeepSeek error: {exc}")
        answer = "ой, у меня ошибка в голове"

    if not answer:
        answer = "я чето завис, змеиный мозг пустой"

    history_by_chat_id[chat_id].append({"role": "assistant", "content": answer})
    await update.message.reply_text(answer[:4096])


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
