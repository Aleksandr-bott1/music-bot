import os
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
# 🎵 yt-dlp НАЛАШТУВАННЯ
# =====================
YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }
    ],
}

# =====================
# 🔍 ПОШУК (ШВИДКИЙ)
# =====================
def search_music(query):
    with YoutubeDL({
        "quiet": True,
        "default_search": "ytsearch8",
        "noplaylist": True,
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
# 🔎 ОБРОБКА ТЕКСТУ
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    query = message.text.strip()

    bot.send_message(chat_id, "🔍 Шукаю...")

    results = search_music(query)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    keyboard = types.InlineKeyboardMarkup()
    for r in results[:8]:
        title = r.get("title", "Без назви")[:60]
        video_id = r.get("id")

        keyboard.add(
            types.InlineKeyboardButton(
                f"🎵 {title}",
                callback_data=video_id
            )
        )

    bot.send_message(
        chat_id,
        "👇 Обери пісню:",
        reply_markup=keyboard
    )

# =====================
# ⬇️ ЗАВАНТАЖЕННЯ MP3
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
import os
import re
import random
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
]

# =====================
# 🎵 yt-dlp (МАКС ШВИДКО)
# =====================
YDL_AUDIO = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 8,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "128",
    }],
}

# =====================
# ⚡ МЕГА ШВИДКИЙ ПОШУК
# =====================
def fast_search(query):
    with YoutubeDL({
        "quiet": True,
        "default_search": "ytsearch5",
        "noplaylist": True,
        "extract_flat": "in_playlist",
        "socket_timeout": 8,
    }) as ydl:
        data = ydl.extract_info(query, download=False)
        return data.get("entries", [])

# =====================
# 🎵 TikTok → Назва треку
# =====================
def tiktok_to_query(url):
    with YoutubeDL({
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "socket_timeout": 8,
    }) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get("track") or info.get("title")

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🔥 Музичний бот\n\n"
        "🎵 Напиши назву пісні\n"
        "🎶 або скинь TikTok-посилання\n\n"
        "⚡ Працюю МЕГА швидко"
    )

# =====================
# 🔎 ТЕКСТ / TIKTOK
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    bot.send_message(chat_id, "⚡ Шукаю...")

    # TikTok
    if "tiktok.com" in text:
        try:
            query = tiktok_to_query(text)
        except Exception:
            bot.send_message(chat_id, "❌ Не вдалося розпізнати TikTok")
            return
    else:
        query = text

    results = fast_search(query)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎧 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(results):
        title = r.get("title", "Без назви")[:55]
        video_id = r.get("id")
        emoji = "🔥" if i % 2 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=video_id
            )
        )

    bot.send_message(
        chat_id,
        "👇 Результати:",
        reply_markup=keyboard
    )

# =====================
# ⬇️ MP3
# =====================
@bot.callback_query_handler(func=lambda call: True)
def download(call):
    chat_id = call.message.chat.id
    url = f"https://www.youtube.com/watch?v={call.data}"

    bot.send_message(chat_id, "⬇️ Завантажую mp3...")

    with YoutubeDL(YDL_AUDIO) as ydl:
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
