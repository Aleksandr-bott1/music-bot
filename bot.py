import os
import random
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL
import requests

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"
bot = telebot.TeleBot(TOKEN, threaded=False)

# 🔴 примусово вимикаємо webhook (щоб не мовчав)
requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
]

YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 8,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# 🔎 НАДІЙНИЙ ПОШУК
# =====================
def search_music(query):
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch25",
            "noplaylist": True,
            "socket_timeout": 8,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            return data.get("entries", [])
    except Exception:
        return []

# =====================
# 🧠 ФІЛЬТР + ОРИГІНАЛ / РЕМІКС
# =====================
def prepare_results(results):
    seen = set()
    originals, remixes = [], []

    remix_words = [
        "remix", "slowed", "sped", "speed",
        "bass", "reverb", "nightcore", "edit"
    ]

    for r in results:
        vid = r.get("id")
        title = (r.get("title") or "").lower()

        if not vid or vid in seen:
            continue

        seen.add(vid)

        if any(w in title for w in remix_words):
            remixes.append(r)
        else:
            originals.append(r)

    final = originals[:3] + remixes
    return final[:10]

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Музичний бот\n\n"
        "✍️ Напиши назву пісні\n"
        "🔗 або встав TikTok-посилання\n\n"
        "🔥 1–3 оригінали → ремікси\n"
        "⚡ Без зависань"
    )

# =====================
# 🟢 ЄДИНИЙ HANDLER
# =====================
@bot.message_handler(content_types=["text"])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # TikTok → чистимо
    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    bot.send_message(chat_id, "🔍 Шукаю музику...")

    results = search_music(query)
    if not results:
        bot.send_message(chat_id, "❌ Не знайшов. Спробуй іншу назву.")
        return

    final = prepare_results(results)
    if not final:
        bot.send_message(chat_id, "❌ Нема унікальних треків.")
        return

    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(final):
        title = (r.get("title") or "Без назви")
        title = title.split("(")[0].split("[")[0][:35]
        vid = r.get("id")

        emoji = "🔥" if i % 2 == 0 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=f"{vid}|{title}"
            )
        )

    bot.send_message(chat_id, "👇 Список:", reply_markup=keyboard)

# =====================
# ⬇️ AUDIO
# =====================
@bot.callback_query_handler(func=lambda c: True)
def send_audio(call):
    chat_id = call.message.chat.id
    vid, title = call.data.split("|", 1)

    bot.send_message(chat_id, "⬇️ Надсилаю трек...")

    with YoutubeDL(YDL_AUDIO) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={vid}",
            download=True
        )
        filename = ydl.prepare_filename(info)

    with open(filename, "rb") as f:
        bot.send_audio(chat_id, f, title=title)

    os.remove(filename)

bot.infinity_polling(skip_pending=True)

