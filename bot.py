import os
import random
import re
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
IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

# =====================
# ⚡ AUDIO (МАКС СТАБІЛЬНО)
# =====================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 10,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# ⚡ СТАБІЛЬНИЙ ПОШУК
# =====================
def search_music(query):
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch5",
            "noplaylist": True,
            "socket_timeout": 10,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            return data.get("entries", [])
    except Exception:
        return []

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Музичний бот\n\n"
        "🎵 Напиши назву пісні\n"
        "🔗 або просто встав TikTok-посилання\n\n"
        "⚡ Стабільний пошук без зависань"
    )

# =====================
# 🔎 ОБРОБКА ТЕКСТУ / TikTok
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # якщо TikTok — чистимо текст
    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    bot.send_message(chat_id, "🔍 Шукаю музику...")

    results = search_music(query)
    if not results:
        bot.send_message(
            chat_id,
            "❌ Не вдалося знайти 😔\n"
            "Спробуй іншу назву або англійською"
        )
        return

    # 🖼️ КАРТИНКА
    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(results[:5]):
        raw_title = r.get("title", "Без назви")
        title = raw_title.split("(")[0].split("[")[0][:35].strip()
        video_id = r.get("id")

        emoji = "🔥" if i == 0 else ("🎵" if i % 2 == 0 else "🔥")

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=f"{video_id}|{title}"
            )
        )

    bot.send_message(
        chat_id,
        "👇 Список пісень:",
        reply_markup=keyboard
    )

# =====================
# ⬇️ AUDIO
# =====================
@bot.callback_query_handler(func=lambda call: True)
def send_audio(call):
    chat_id = call.message.chat.id
    video_id, title = call.data.split("|", 1)
    url = f"https://www.youtube.com/watch?v={video_id}"

    bot.send_message(chat_id, "⬇️ Надсилаю трек...")

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

# =====================
# 🚀 RUN
# =====================
bot.infinity_polling(skip_pending=True)

