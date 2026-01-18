import telebot
import requests
import subprocess
import os
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "music")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}
active_users = set()

# 🔥 КРАСИВІ ФОТО
PHOTOS = [
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
    "https://images.unsplash.com/photo-1470225620780-dba8ba36b745",
]

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 **Музичний бот**\n\n"
        "✍️ Напиши назву пісні\n"
        "🎧 1–3 оригінали, далі ремікси",
        parse_mode="Markdown"
    )

# ================= ПОШУК (ДУЖЕ ШВИДКИЙ) =================
def search_music(query):
    url = "https://itunes.apple.com/search"
    params = {
        "term": query,
        "media": "music",
        "limit": 30
    }

    r = requests.get(url, params=params, timeout=6)
    data = r.json()

    originals = []
    others = []

    remix_words = [
        "remix", "phonk", "sped", "slowed",
        "bass", "edit", "rework", "mix", "version"
    ]

    seen = set()

    for item in data.get("results", []):
        artist = item.get("artistName")
        track = item.get("trackName")
        if not artist or not track:
            continue

        title = f"{artist} – {track}"
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)

        yt_query = f"{artist} {track}"
        lower = title.lower()

        # ПЕРШІ 3 — СТРОГО ОРИГІНАЛИ
        if len(originals) < 3 and not any(w in lower for w in remix_words):
            originals.append((title, yt_query))
        else:
            others.append((title, yt_query))

    # якщо оригіналів менше 3 — добираємо
    while len(originals) < 3 and others:
        originals.append(others.pop(0))

    final = originals + others

    # гарантуємо 10 результатів
    while len(final) < 10:
        final.append((query, query))

    return final[:10]

# ================= ЗАВАНТАЖЕННЯ =================
def download_audio(chat_id, query):
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

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

# ================= ТЕКСТ =================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in active_users:
        bot.send_message(chat_id, "⏳ Зачекай…")
        return

    active_users.add(chat_id)
    bot.send_message(chat_id, "🔍 Шукаю…")

    try:
        results = search_music(text)
    except:
        bot.send_message(chat_id, "❌ Помилка пошуку")
        active_users.remove(chat_id)
        return

    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        active_users.remove(chat_id)
        return

    user_results[chat_id] = results

    kb = InlineKeyboardMarkup(row_width=1)
    for i, (title, _) in enumerate(results):
        icon = "🎵" if i < 3 else "🔥"
        kb.add(
            InlineKeyboardButton(
                text=f"{icon} {title[:60]}",
                callback_data=str(i))
        )

    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        caption="🎶 Обери трек:",
        reply_markup=kb
    )

    active_users.remove(chat_id)

# ================= КНОПКИ =================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    chat_id = c.message.chat.id
    idx = int(c.data)

    if chat_id not in user_results:
        bot.answer_callback_query(c.id, "❌ Список застарів")
        return

    title, query = user_results[chat_id][idx]
    bot.answer_callback_query(c.id, "⏳ Завантажую…")
    download_audio(chat_id, query)

    user_results.pop(chat_id, None)

print("BOT STARTED — FINAL STABLE VERSION")
bot.infinity_polling(skip_pending=True)

