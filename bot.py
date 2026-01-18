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
# 🖼️ МУЗИЧНІ КАРТИНКИ
# =====================
IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
    "https://images.unsplash.com/photo-1487180144351-b8472da7d491",
]

# =====================
# ⚡ НАЙШВИДШЕ АУДІО (без mp3)
# =====================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 8,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# ⚡ МЕГА ШВИДКИЙ ПОШУК
# =====================
def fast_search(query):
    with YoutubeDL({
        "quiet": True,
        "default_search": "ytsearch3",
        "noplaylist": True,
        "extract_flat": True,
        "socket_timeout": 8,
    }) as ydl:
        data = ydl.extract_info(query, download=False)
        return data.get("entries", [])

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Привіт!\n\n"
        "🎵 Напиши назву пісні або виконавця\n"
        "⚡ Пошук майже миттєвий\n"
        "🖼️ Гарні картинки + 🔥"
    )

# =====================
# 🔎 ПОШУК
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    query = message.text.strip()

    bot.send_message(chat_id, "⚡ Шукаю...")

    results = fast_search(query)
    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    # 🖼️ випадкова картинка
    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(results):
        title = r.get("title", "Без назви")[:60]
        video_id = r.get("id")

        emoji = "🔥" if i % 2 == 0 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=video_id
            )
        )

    bot.send_message(
        chat_id,
        "👇 Список пісень:",
        reply_markup=keyboard
    )

# =====================
# ⬇️ НАДСИЛАННЯ АУДІО
# =====================
@bot.callback_query_handler(func=lambda call: True)
def send_audio(call):
    chat_id = call.message.chat.id
    url = f"https://www.youtube.com/watch?v={call.data}"

    bot.send_message(chat_id, "⬇️ Надсилаю трек...")

    with YoutubeDL(YDL_AUDIO) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    with open(filename, "rb") as audio:
        bot.send_audio(chat_id, audio)

    os.remove(filename)

# =====================
# 🚀 RUN
# =====================
bot.infinity_polling(skip_pending=True)
