import os
import asyncio
import requests
import difflib
import random
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HISTORY_FILE = "history.txt"
MAX_HISTORY = 90

def is_similar(new_post, old_post, threshold=0.9):
    return difflib.SequenceMatcher(None, new_post, old_post).ratio() > threshold

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_to_history(post):
    history = load_history()
    history.append(post)
    history = history[-MAX_HISTORY:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        for p in history:
            f.write(p.replace('\n', ' ') + "\n")

def choose_tone():
    tones = {
        "шуточный": "Пиши с лёгкой иронией, местами шуточно, как будто рассказываешь другу.",
        "дерзкий": "Пиши уверенно, по делу, не церемонясь. Как будто у тебя опыт, а читатель — ленивый.",
        "деловой": "Пиши как эксперт. Чётко, структурно, по фактам — будто это бизнес-доклад."
    }
    name = random.choice(list(tones.keys()))
    return name, tones[name]

def generate_post():
    tone_key, tone_instruction = choose_tone()

    prompt = (
        "Сгенерируй пост для Telegram-канала в формате:\n\n"
        "1. 📌 Идея заработка — название\n"
        "2. 💡 Суть — коротко и понятно\n"
        "3. 🛠 Шаги для старта (3-5 шагов)\n"
        "4. 💰 Пример расчёта дохода\n"
        "5. 🔗 Полезные ссылки или ресурсы\n"
        "6. 👤 Подходит тем, у кого: (перечисли навыки или стартовые условия)\n\n"
        f"{tone_instruction} Без инфоцыганщины. Старайся быть живым и понятным."
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://t.me/a_kak_zarabotat",
        "Content-Type": "application/json"
    }

    for attempt in range(5):
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "Ты — специалист по идеям заработка для Telegram-канала."},
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload)
        data = response.json()

        if "choices" in data:
            post = data["choices"][0]["message"]["content"].strip()
            if all(not is_similar(post, old) for old in load_history()):
                return post
        else:
            print("❌ Ошибка:", data)
            break
    return None

async def post_to_telegram(message):
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode="HTML")

if __name__ == "__main__":
    post = generate_post()
    if post:
        print("📤 Сгенерировано:\n", post)
        asyncio.run(post_to_telegram(post))
        save_to_history(post)
        print("✅ Отправлено и сохранено!")
    else:
        print("⚠️ Не удалось сгенерировать уникальный пост.")
