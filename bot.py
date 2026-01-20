import telebot
import requests
import subprocess
import os
import random
import json
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "music")
STATS_FILE = os.path.join(BASE_DIR, "stats.json")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}
active_downloads = set()

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
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

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
        "🎵 Перші — оригінали\n"
        "🔥 Далі — ремікси\n"
        "🎧 Є швидкий режим",
        parse_mode="Markdown"
    )

# ================= SEARCH =================
def search_music(query):
    r = requests.get(
        "https://itunes.apple.com/search",
        params={"term": query, "media": "music", "limit": 30},
        timeout=6
    ).json()

    originals, remixes, seen = [], [], set()
    remix_words = ["remix", "phonk", "sped", "slowed", "bass", "edit", "mix"]

    for item in r.get("results", []):
        title = f"{item.get('artistName')} – {item.get('trackName')}"
        if not item.get("artistName") or not item.get("trackName"):
            continue
        if title.lower() in seen:
            continue
        seen.add(title.lower())

        q = f"{item['artistName']} {item['trackName']}"
        if len(originals) < 3 and not any(w in title.lower() for w in remix_words):
            originals.append((title, q))
        else:
            remixes.append((title, q))

    return (originals + remixes)[:10]

# ================= DOWNLOAD =================
def download_mp3(chat_id, query):
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

        # YouTube → якщо не вийшло, SoundCloud
        for source in [f"ytsearch1:{query} official audio", f"scsearch1:{query}"]:
            try:
                subprocess.run(
                    [
                        "yt-dlp",
                        "-x",
                        "--audio-format", "mp3",
                        "--audio-quality", "0",
                        "--no-playlist",
                        "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
                        source
                    ],
                    check=True,
                    timeout=60
                )
                break
            except:
                continue

        files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".mp3")]
        if not files:
            bot.send_message(chat_id, "❌ Не вдалося завантажити")
            return

        with open(os.path.join(DOWNLOAD_DIR, files[0]), "rb") as audio:bot.send_audio(chat_id, audio)

        os.remove(os.path.join(DOWNLOAD_DIR, files[0]))

    finally:
        active_downloads.discard(chat_id)

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
    kb = InlineKeyboardMarkup(row_width=2)

    for i, (title, _) in enumerate(results):
        icon = "🎵" if i < 3 else "🔥"
        kb.add(
            InlineKeyboardButton(f"{icon} {title[:40]}", callback_data=f"dl_{i}"),
            InlineKeyboardButton("🎧 Швидко", callback_data=f"fast_{i}")
        )

    bot.send_photo(chat_id, random.choice(PHOTOS), "🎶 Обери:", reply_markup=kb)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    chat_id = c.message.chat.id
    if chat_id not in user_results:
        bot.answer_callback_query(c.id, "⏳ Спробуй ще раз")
        return

    action, idx = c.data.split("_")
    title, query = user_results[chat_id][int(idx)]

    if action == "fast":
        bot.answer_callback_query(c.id)
        bot.send_message(chat_id, f"🎧 {title}\n🔗 https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
        return

    if chat_id in active_downloads:
        bot.answer_callback_query(c.id, "⏳ Уже завантажую")
        return

    active_downloads.add(chat_id)
    bot.answer_callback_query(c.id, "📥 Завантажую MP3…")
    download_mp3(chat_id, query)
    user_results.pop(chat_id, None)

# ================= RUN =================
print("BOT STARTED — FINAL STABLE")
bot.infinity_polling(skip_pending=True)








