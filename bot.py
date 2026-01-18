import os
import random
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL
import requests

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"
bot = telebot.TeleBot(TOKEN, threaded=False)

# 🔴 ПРИМУСОВО ВИДАЛЯЄМО WEBHOOK
requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

# =====================
# КАРТИНКИ
# =====================
IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
]

# =====================
# AUDIO (ШВИДКО)
# =====================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# ПОШУК (ПРОСТИЙ І НАДІЙНИЙ)
# =====================
def search_music(query):
    with YoutubeDL({
        "quiet": True,
        "default_search": "ytsearch10",
        "noplaylist": True,
    }) as ydl:
        data = ydl.extract_info(query, download=False)
        return data.get("entries", [])

# =====================
# START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Музичний бот ПРАЦЮЄ\n\n"
        "✍️ Просто напиши назву пісні\n"
        "🔗 або встав TikTok-посилання"
    )

# =====================
# ЄДИНИЙ HANDLER (НЕ МОВЧИТЬ)
# =====================
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    chat_id = message.chat.id
    text = message.text.strip()

    bot.send_message(chat_id, "🔍 Шукаю...")

    # TikTok → чистимо
    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    results = search_music(query)
    if not results:
        bot.send_message(chat_id, "❌ Не знайшов. Спробуй іншу назву.")
        return

    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(results[:10]):
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
# AUDIO
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

# =====================
# RUN
# =====================
bot.infinity_polling(skip_pending=True)
