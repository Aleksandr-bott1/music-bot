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
active_users = set()

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
    month = datetime.now().strftime("%Y-%m")
    return len(stats.get(month, []))

# ================= START =================
@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.chat.id)
    count = get_month_users()

    bot.send_message(
        message.chat.id,
        "🎵 *OnlineMyzik — музичний бот*\n\n"
        f"👥 *Користувачів цього місяця:* {count}\n\n"
        "✍️ Напиши назву пісні з TikTok / YouTube\n"
        "🎵 Перші — оригінали\n"
        "🔥 Далі — ремікси\n"
        "📥 Можна завантажити mp3",
        parse_mode="Markdown"
    )

# ================= SEARCH: SoundCloud =================
def search_soundcloud(query, limit=10):
    try:
        output = subprocess.check_output(
            [
                "yt-dlp",
                "--print", "title",
                "--print", "webpage_url",
                f"scsearch{limit}:{query}"
            ],
            text=True,
            timeout=8
        )
        lines = output.strip().split("\n")
        results = []
        for i in range(0, len(lines), 2):
            title = lines[i]
            results.append((title, title))
        return results
    except:
        return []

# ================= SEARCH: iTunes + SoundCloud =================
def search_music(query):
    originals, others = [], []
    remix_words = ["remix", "phonk", "sped", "slowed", "bass", "edit", "mix"]
    seen = set()

    # ---------- iTunes ----------
    try:
        url = "https://itunes.apple.com/search"
        params = {"term": query, "media": "music", "limit": 30}
        r = requests.get(url, params=params, timeout=6)
        data = r.json()
    except:
        data = {}

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

        if len(originals) < 3 and not any(w in key for w in remix_words):
            originals.append((title, yt_query))
        else:
            others.append((title, yt_query))

    while len(originals) < 3 and others:
        originals.append(others.pop(0))

    final = originals + others

    # ---------- SoundCloud fallback ----------
    if len(final) < 3:
        try:
            sc_results = search_soundcloud(query, limit=10)
            for title, yt_query in sc_results:
                if title.lower() not in seen:
                    final.append((title, yt_query))
                if len(final) >= 10:
                    break
        except:
            pass

    return final[:10]

# ================= DOWNLOAD =================
def download_audio(chat_id, query):
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

        subprocess.run(
            [
                "yt-dlp",
                "-x", "--audio-format", "mp3",
                "--no-playlist",
                "--no-warnings",
                "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
                f"ytsearch1:{query}"
            ],
            check=True,
            timeout=40
        )

        files = os.listdir(DOWNLOAD_DIR)
        if not files:
            bot.send_message(chat_id, "❌ Не вдалося завантажити")
            return

        with open(os.path.join(DOWNLOAD_DIR, files[0]), "rb") as audio:
            bot.send_audio(chat_id, audio)

    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# ================= TEXT =================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in active_users:
        bot.send_message(chat_id, "⏳ Зачекай…")
        return

    active_users.add(chat_id)
    register_user(chat_id)
    bot.send_message(chat_id, "🔍 Шукаю…")

    try:
        results = search_music(text)
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
    finally:
        active_users.discard(chat_id)

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    chat_id = c.message.chat.id
    idx = int(c.data)

    if chat_id not in user_results:
        bot.answer_callback_query(c.id, "❌ Список застарів")
        return

    _, query = user_results[chat_id][idx]
    bot.answer_callback_query(c.id, "⏳ Завантажую…")
    download_audio(chat_id, query)

# ================= RUN =================
print("BOT STARTED — FINAL + SOUNDCLOUD")
bot.infinity_polling(skip_pending=True)










