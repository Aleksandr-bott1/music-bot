import telebot
import subprocess
import os
import re
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

active_search = set()
user_results = {}

PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
]

TIKTOK_REGEX = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Музичний бот\n\n"
        "✍️ Напиши назву пісні\n"
        "🔗 Або встав TikTok-посилання"
    )

# ---------- ПОШУК ----------
def search_youtube(query, limit=5):
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "title",
        "--print", "webpage_url",
        f"ytsearch{limit}:{query}"
    ]
    out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
    lines = out.strip().split("\n")
    return list(zip(lines[0::2], lines[1::2]))

# ---------- ЗАВАНТАЖЕННЯ ----------
def download_audio(chat_id, url):
    try:
        # очистити папку
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

        subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",
                "--no-playlist",
                "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
                url
            ],
            check=True
        )

        time.sleep(1)

        files = os.listdir(DOWNLOAD_DIR)
        if not files:
            bot.send_message(chat_id, "❌ Аудіо не знайдено")
            return

        path = os.path.join(DOWNLOAD_DIR, files[0])
        with open(path, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(path)

    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# ---------- ТЕКСТ ----------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in active_search:
        bot.send_message(chat_id, "⏳ Зачекай, я ще шукаю…")
        return

    active_search.add(chat_id)

    # TikTok
    if TIKTOK_REGEX.search(text):
        bot.send_message(chat_id, "🎶 Дістаю звук з TikTok…")
        download_audio(chat_id, text)
        active_search.remove(chat_id)
        return

    bot.send_message(chat_id, "🔍 Шукаю…")

    try:
        results = search_youtube(text, 5)
    except:
        bot.send_message(chat_id, "❌ Помилка пошуку")
        active_search.remove(chat_id)
        return

    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        active_search.remove(chat_id)
        return

    user_results[chat_id] = results

    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, (title, _) in enumerate(results):
        keyboard.add(
            InlineKeyboardButton(
                text=f"🎵 {title[:50]}",
                callback_data=str(i)
            )
        )

    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        caption="🎶 Обери трек:",
        reply_markup=keyboard
    )

    active_search.remove(chat_id)

# ---------- КНОПКИ ----------
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    chat_id = c.message.chat.id
    idx = int(c.data)

    if chat_id not in user_results:
        bot.answer_callback_query(c.id, "❌ Список застарів")
        return

    _, url = user_results[chat_id][idx]
    bot.answer_callback_query(c.id, "⏳ Завантажую…")
    download_audio(chat_id, url)
    del user_results[chat_id]

print("BOT STARTED — HEALTHY VERSION")
bot.infinity_polling(skip_pending=True, none_stop=True)

