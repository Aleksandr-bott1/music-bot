import os
import random
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

telebot.apihelper.delete_webhook(TOKEN)
bot = telebot.TeleBot(TOKEN)

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
# ⚡ МЕГА ШВИДКИЙ ПОШУК (FLAT)
# =====================
def fast_search(query):
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch20",
            "extract_flat": True,
            "noplaylist": True,
            "socket_timeout": 5,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            return data.get("entries", [])
    except Exception:
        return []

# =====================
# 🧠 РОЗДІЛЕННЯ: ОРИГІНАЛ / РЕМІКС
# =====================
def split_results(results):
    originals = []
    remixes = []

    remix_words = [
        "remix", "slowed", "speed", "sped",
        "bass", "reverb", "nightcore", "edit"
    ]

    for r in results:
        title = (r.get("title") or "").lower()
        if any(word in title for word in remix_words):
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
        "🎵 Напиши назву пісні або виконавця\n"
        "🔗 або встав TikTok-посилання\n\n"
        "🔥 Спочатку оригінали, потім ремікси"
    )

# =====================
# 🔎 ПОШУК
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    bot.send_message(chat_id, "⚡ Швидкий пошук...")

    results = fast_search(query)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    originals, remixes = split_results(results)

    final = originals[:3] + remixes
    final = final[:10]

    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(final):
        title = (r.get("title") or "Без назви")
        title = title.split("(")[0].split("[")[0][:35].strip()
        video_id = r.get("id")

        emoji = "🔥" if i % 2 == 0 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=f"{video_id}|{title}"
            )
        )

    bot.send_message(chat_id, "👇 Список:", reply_markup=keyboard)

# =====================
# ⬇️ АУДІО (ТІЛЬКИ ПІСЛЯ КЛІКУ)
# =====================
@bot.callback_query_handler(func=lambda call: True)
def send_audio(call):
    chat_id = call.message.chat.id
    video_id, title = call.data.split("|", 1)
    url = f"https://www.youtube.com/watch?v={video_id}"

    bot.send_message(chat_id, "⬇️ Завантажую трек...")

    with YoutubeDL(YDL_AUDIO) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    with open(filename, "rb") as audio:
        bot.send_audio(
            chat_id,
            audio,
            title=title,
            performer="🎧 Music Bot"
        )

    os.remove(filename)

bot.infinity_polling(skip_pending=True)


