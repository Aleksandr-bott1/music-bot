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
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

BAD_WORDS = ["karaoke", "live", "cover", "instrumental", "acoustic"]
REMIX_TAGS = ["remix", "phonk", "bass boosted", "sped up"]
TIKTOK_REGEX = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")

# ---------- ПОШУК ----------
def search(query, limit):
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

def bad(title):
    t = title.lower()
    return any(w in t for w in BAD_WORDS)

# ---------- ЗАВАНТАЖЕННЯ ----------
def download_audio(chat_id, url):
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "-f", "bestaudio",
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

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎶 Музичний бот\n\n"
        "✍️ Напиши назву пісні\n"
        "🔗 Або встав TikTok-посилання"
    )

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

    results = []
    used = set()

    # ОРИГІНАЛИ (1–3)
    try:
        for title, url in search(text, 5):
            if bad(title):
                continue
            key = title.lower()
            if key in used:
                continue
            used.add(key)
            results.append(("🎵", title, url))
            if len(results) == 3:
                break
    except:
        pass

    # РЕМІКСИ
    for tag in REMIX_TAGS:
        try:
            for title, url in search(f"{text} {tag}", 5):
                if bad(title):
                    continue
                key = title.lower()
                if key in used:
                    continue
                used.add(key)
                results.append(("🔥", title, url))
                if len(results) >= 10:
                    break
        except:
            pass

    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        active_search.remove(chat_id)
        return

    user_results[chat_id] = results

    kb = InlineKeyboardMarkup(row_width=1)
    for i, (icon, title, _) in enumerate(results):
        kb.add(InlineKeyboardButton(
