# Zmey Telegram AI Bot

Простой Telegram-бот, который отвечает через DeepSeek API.

## Что умеет

- `/start` — приветствие
- `/reset` — очистить память текущего чата
- обычный текст — отправляется в DeepSeek
- стиль ассистента задан в `SYSTEM_PROMPT` внутри `bot.py`

## Запуск локально

```bash
git clone https://github.com/BubbyGit/studious-enigma.git
cd studious-enigma
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Открой `.env` и вставь свои ключи:

```env
TELEGRAM_BOT_TOKEN=сюда_токен_бота
DEEPSEEK_API_KEY=сюда_ключ_deepseek
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
MAX_HISTORY_MESSAGES=12
```

Потом запуск:

```bash
python bot.py
```

## Важно

Не коммить `.env` в GitHub. В нём лежат секретные ключи.

По умолчанию используется `deepseek-v4-flash` и выключенный thinking mode.
