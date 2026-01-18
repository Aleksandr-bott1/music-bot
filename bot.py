import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# 🔐 ВСТАВ СВІЙ ТОКЕН
TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

# 🔥 ВАЖЛИВО: очищає всі старі webhook / polling
telebot.apihelper.delete_webhook(TOKEN)

bot = telebot.TeleBot(TOKEN)

# 🎵 Налаштування yt-dlp (mp3 + ffmpeg)
ydl_opts = {
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

# 🔍 Пошук 5 треків
def search_music(query):
    with YoutubeDL({"quiet": True, "default_search": "ytsearch5"}) as ydl:
        info = ydl.extract_info(query, download=False)
        return info.get("entries", [])

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Напиши назву пісні або виконавця — я знайду музику!"
    )

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    results = search_music(message.text)

    if not results:
        bot.send_message(message.chat.id, "❌ Нічого не знайшов")
        return

    keyboard = types.InlineKeyboardMarkup()
    for r in results:
        title = r.get("title")
        url = r.get("webpage_url")
        keyboard.add(types.InlineKeyboardButton(title, callback_data=url))

    bot.send_message(
        message.chat.id,
        "🎶 Обери трек:",
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def download_song(call):
    url = call.data
    chat_id = call.message.chat.id

    bot.send_message(chat_id, "⏳ Завантажую mp3...")

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        with open(filename, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(filename)

    except Exception as e:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# ▶️ ЗАПУСК
bot.infinity_polling()
