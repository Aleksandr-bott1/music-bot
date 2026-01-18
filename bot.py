import os
import random
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# =====================
# 🔐 TOKEN
# =====================
TOKEN = "ВСТАВ_СВІЙ_ТОКЕН"

telebot.apihelper.delete_webhook(TOKEN)
bot = telebot.TeleBot(TOKEN)

# =====================
# 🖼️ КАРТИНКИ
# =====================
IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

# =====================
# ⚡ AUDIO
# =====================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 8,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# ⚡ ПОШУК (ШВИДКИЙ + НАДІЙНИЙ)
# =====================
def search_music(query):
    # 1️⃣ дуже швидкий
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch20",
            "extract_flat": True,
            "noplaylist": True,
            "socket_timeout": 5,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            fast = data.get("entries", [])
            if fast:
                return fast
    except Exception:
        pass

    # 2️⃣ fallback (завжди знаходить)
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch10",
            "noplaylist": True,
            "socket_timeout": 10,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            return data.get("entries", [])
    except Exception:
        return []

# =====================
# 🧠 ОРИГІНАЛ / РЕМІКС
# =====================
def split_results(results):
    remix_words = [
        "remix", "slowed", "sped", "speed",
        "bass", "reverb", "nightcore", "edit"
    ]

    originals = []
    remixes = []

    for r in results:
        title = (r.get("title") or "").lower()
        if any(w in title for w in remix_words):
            remixes.append(r)
        else:
            originals.append(r)

    return originals, remixes

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Музичний бот\n\n"
        "🎵 Напиши назву пісні\n"
        "🔗 або встав TikTok-посилання\n\n"
        "🔥 1–3 оригінали → ремікси\n"
        "⚡ Швидко і стабільно"
    )

# =====================
# 🔎 ПОШУК
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # TikTok → беремо текст
    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    bot.send_message(chat_id, "⚡ Шукаю музику...")

    results = search_music(query)
    if not results:
        bot.send_message(
            chat_id,
            "❌ Не вдалося знайти 😔\n"
            "Спробуй іншу назву або англійською"
        )
        return

    originals, remixes = split_results(results)

    final = originals[:3] + remixes
    final = final[:10]

    # 🖼️ КАРТИНКА
    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(final):
        raw_title = r.get("title", "Без назви")
        title = raw_title.split("(")[0].split("[")[0][:35].strip()
        video_id = r.get("id")

        emoji = "🔥" if i % 2 == 0 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=f"{video_id}|{title}"
            )
        )

    bot.send_message(chat_id, "👇 Список пісень:", reply_markup=keyboard)
bot.infinity_polling(skip_pending=True)



