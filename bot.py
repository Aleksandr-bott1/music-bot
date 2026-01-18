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

