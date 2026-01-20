import telebot
import requests
import subprocess
import os
import random
import json
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "ТУТ_ТВІЙ_ТОКЕН"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "music")
STATS_FILE = os.path.join(BASE_DIR, "stats.json")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}

PHOTOS = [
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
    "https://images.unsplash.com/photo-1470225620780-dba8ba36b745",
]

# ================= STATS =================
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_stats(data):
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def register_user(chat_id):
    stats = load_stats()
    month = datetime.now().strftime("%Y-%m")
    stats.setdefault(month, [])
    if chat_id not in stats[month]:
        stats[month].append(chat_id)
        save_stats(stats)

def get_month_users():
    stats = load_stats()
    return len(stats.get(datetime.now().strftime("%Y-%m"), []))

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.chat.id)
    bot.send_message(
        message.chat.id,
        "🎵 *OnlineMyzik — музичний бот*\n\n"
        f"👥 *Користувачів за місяць:* {get_month_users()}\n\n"
        "✍️ Напиши назву пісні\n"
        "🎵 1–3 — оригінали\n"
        "🔥 далі — ремікси",
        parse_mode="Markdown"
    )

# ================= SEARCH =================
def search_music(query):
    data = requests.get(
        "https://itunes.apple.com/search",
        params={"term": query, "media": "music", "limit": 30},
        timeout=6
    ).json()

    originals, remixes, seen = [], [], set()
    remix_words = ["remix", "phonk", "sped", "slowed", "bass", "edit", "mix"]

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

        q = f"{artist} {track}"
        if len(originals) < 3 and not any(w in key for w in remix_words):
            originals.append((title, q))
        else:
            remixes.append((title, q))

    return (originals + remixes)[:10]

# ================= DOWNLOAD =================
def download_mp3(chat_id, query):
    filename = query.replace(" ", "_")[:60] + ".mp3"
    path = os.path.join(DOWNLOAD_DIR, filename)

    # кеш
    if os.path.exists(path):
        with open(path, "rb") as audio:
            bot.send_audio(chat_id, audio)
        return

    try:
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--no-playlist",
                "--no-warnings",
                "-o", path,
                f"ytsearch1:{query} official audio"
            ],
            check=True,
            timeout=60
        )
    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")
        return

    if not os.path.exists(path):
        bot.send_message(chat_id, "❌ Не вдалося завантажити")
        return

    with open(path, "rb") as audio:
        bot.send_audio(chat_id, audio)

# ================= TEXT =================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    register_user(chat_id)
    bot.send_message(chat_id, "🔍 Шукаю…")

    results = search_music(message.text)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    user_results[chat_id] = results
    kb = InlineKeyboardMarkup(row_width=1)

    for i, (title, _) in enumerate(results):
        icon = "🎵" if i < 3 else "🔥"
        kb.add(
            InlineKeyboardButton(
                f"{icon} {title[:45]}",
                callback_data=str(i)
            )
        )

    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        "🎶 Обери трек:",
        reply_markup=kb
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    chat_id = c.message.chat.id

    if chat_id not in user_results:
        bot.answer_callback_query(c.id, "⏳ Спробуй ще раз")
        return

    try:
        idx = int(c.data)
        _, query = user_results[chat_id][idx]
    except:
        bot.answer_callback_query(c.id, "⏳ Спробуй ще раз")
        return

    bot.answer_callback_query(c.id, "📥 Завантажую…")
    download_mp3(chat_id, query)
    user_results.pop(chat_id, None)

# ================= RUN =================
print("BOT STARTED — STABLE")
bot.infinity_polling(skip_pending=True)









