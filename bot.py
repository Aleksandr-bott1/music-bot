import telebot
import requests
import subprocess
import os
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"
bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}

PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
]

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(m):
    bot.send_message(
        m.chat.id,
        "🎵 Музичний бот\n\n"
        "✍️ Напиши назву пісні"
    )

# ---------- МЕГА ШВИДКИЙ ПОШУК ----------
def search_itunes(query):
    r = requests.get(
        "https://itunes.apple.com/search",
        params={"term": query, "media": "music", "limit": 10},
        timeout=5
    )
    data = r.json()
    results = []

    for item in data.get("results", []):
        title = f"{item['artistName']} – {item['trackName']}"
        yt_query = f"{item['artistName']} {item['trackName']}"
        results.append((title, yt_query))

    return results

# ---------- ЗАВАНТАЖЕННЯ ----------
def download_audio(chat_id, query):
    try:
        subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",
                "--no-playlist",
                "--no-warnings",
                "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
                f"ytsearch1:{query}"
            ],
            check=True,
            timeout=45
        )

        files = os.listdir(DOWNLOAD_DIR)
        if not files:
            bot.send_message(chat_id, "❌ Не вдалося завантажити")
            return

        path = os.path.join(DOWNLOAD_DIR, files[0])
        with open(path, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(path)

    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# ---------- ТЕКСТ ----------
@bot.message_handler(func=lambda m: True)
def text(m):
    chat_id = m.chat.id

    results = search_itunes(m.text)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    user_results[chat_id] = results

    kb = InlineKeyboardMarkup(row_width=1)
    for i, (title, _) in enumerate(results):
        icon = "🎵" if i < 3 else "🔥"
        kb.add(
            InlineKeyboardButton(
                text=f"{icon} {title[:60]}",
                callback_data=str(i)
            )
        )

    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        caption="🎶 Обери трек:",
        reply_markup=kb
    )

# ---------- КНОПКИ ----------
@bot.callback_query_handler(func=lambda c: True)
def cb(c):
    chat_id = c.message.chat.id
    idx = int(c.data)

    title, query = user_results[chat_id][idx]
    bot.answer_callback_query(c.id, "⏳ Завантажую…")
    download_audio(chat_id, query)

    del user_results[chat_id]

print("BOT STARTED — FAST MODE")
bot.infinity_polling()
