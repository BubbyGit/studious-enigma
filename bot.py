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
history_by_chat_id = defaultdict(list)

print("config loaded")
