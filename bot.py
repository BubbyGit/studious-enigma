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
DEEPSEEK_THINKING = os.getenv("DEEPSEEK_THINKING", "disabled")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "250"))

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


def deepseek_options() -> dict:
    options = {
        "model": DEEPSEEK_MODEL,
        "max_tokens": MAX_OUTPUT_TOKENS,
    }

    # deepseek-v4-flash / deepseek-v4-pro по умолчанию думают.
    # Для простого дешевого бота выключаем thinking через extra_body.
    if DEEPSEEK_MODEL in {"deepseek-v4-flash", "deepseek-v4-pro"}:
        options["extra_body"] = {"thinking": {"type": DEEPSEEK_THINKING}}

    # Temperature имеет смысл только в non-thinking режиме.
    if DEEPSEEK_THINKING == "disabled" or DEEPSEEK_MODEL == "deepseek-chat":
        options["temperature"] = 0.9

    return options


def safe_error(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}"
    if DEEPSEEK_API_KEY:
        text = text.replace(DEEPSEEK_API_KEY, "***")
    return text[:800]


def ask_deepseek(messages: list[dict[str, str]]) -> str:
    response = client.chat.completions.create(
        messages=messages,
        **deepseek_options(),
    )
    return (response.choices[0].message.content or "").strip()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("привет, я Змей. пиши че-нибудь, я отвечу")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    history_by_chat_id.pop(update.effective_chat.id, None)
    await update.message.reply_text("память стер, я чистый змей")


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        answer = ask_deepseek([{"role": "user", "content": "Ответь одним словом: ок"}])
        await update.message.reply_text(
            f"DeepSeek работает.\nmodel={DEEPSEEK_MODEL}\nthinking={DEEPSEEK_THINKING}\nanswer={answer}"
        )
    except Exception as exc:
        print(f"DeepSeek health error: {safe_error(exc)}")
        await update.message.reply_text(f"DeepSeek не работает:\n{safe_error(exc)}")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_text = update.message.text.strip()

    history_by_chat_id[chat_id].append({"role": "user", "content": user_text})
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history_by_chat_id[chat_id][-MAX_HISTORY_MESSAGES:]

    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        answer = ask_deepseek(messages)
    except Exception as exc:
        print(f"DeepSeek error: {safe_error(exc)}")
        answer = f"ой, DeepSeek упал:\n{safe_error(exc)}"

    if not answer:
        answer = "я чето завис, змеиный мозг пустой"

    history_by_chat_id[chat_id].append({"role": "assistant", "content": answer})
    await update.message.reply_text(answer[:4096])


def main() -> None:
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("health", health))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
