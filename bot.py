import os
import random
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# =====================
# 🔐 TOKEN
# =====================
TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

telebot.apihelper.delete_webhook(TOKEN)
bot = telebot.TeleBot(TOKEN)

# =====================
# 🖼️ КАРТИНКИ
# =====================
MUSIC_IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
    "https://images.unsplash.com/photo-1487180144351-b8472da7d491",
]

# =====================
# 🎵 yt-dlp (MP3, ШВИДШЕ)
# =====================
YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 10,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }
    ],
}

# =====================
# 🔍 ПОШУК
# =====================
def search_music(query):
    with YoutubeDL({
        "quiet": True,
        "default_search": "ytsearch8",
        "noplaylist": True,
        "socket_timeout": 10,
    }) as ydl:
        info = ydl.extract_info(query, download=False)
        return info.get("entries", [])

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Напиши назву пісні або виконавця"
    )

# =====================
# 🔎 ТЕКСТ
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    query = message.text.strip()

    bot.send_message(chat_id, "⚡ Шукаю...")

    results = search_music(query)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    # 🖼️ Картинка кожен раз інша
    bot.send_photo(
        chat_id,
        random.choice(MUSIC_IMAGES),
        caption="🎧 Обери пісню 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(results[:8]):
        title = r.get("title", "Без назви")[:60]
        video_id = r.get("id")

        emoji = "🔥" if i % 2 == 1 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=video_id
            )
        )

    bot.send_message(
        chat_id,
        "👇 Список треків:",
        reply_markup=keyboard
    )

# =====================
# ⬇️ MP3
# =====================
@bot.callback_query_handler(func=lambda call: True)
def download_song(call):
    chat_id = call.message.chat.id
    video_id = call.data
    url = f"https://www.youtube.com/watch?v={video_id}"

    bot.send_message(chat_id, "⬇️ Завантажую mp3...")

    with YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        filename = filename.rsplit(".", 1)[0] + ".mp3"

    with open(filename, "rb") as audio:
        bot.send_audio(chat_id, audio)

    os.remove(filename)

# =====================
# 🚀 RUN
# =====================
bot.infinity_polling(skip_pending=True)
