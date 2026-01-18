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
# ⚡ АУДІО (ШВИДКО, СТАБІЛЬНО)
# =====================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "socket_timeout": 10,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# ⚡ 2-РІВНЕВИЙ ПОШУК
# =====================
def fast_search(query):
    # ⚡ Дуже швидкий
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch3",
            "noplaylist": True,
            "extract_flat": True,
            "socket_timeout": 6,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            results = data.get("entries", [])
            if results:
                return results
    except Exception:
        pass

    # 🐢 Надійний (fallback)
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
        "🎧 Привіт!\n\n"
        "🎵 Напиши назву пісні або виконавця\n"
        "🔥 TOP результат буде першим\n"
        "⚡ Пошук 1–3 секунди"
    )

# =====================
# 🔎 ПОШУК
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    query = message.text.strip()

    results = fast_search(query)
    if not results:
        bot.send_message(
            chat_id,
            "❌ Не вдалося знайти 😔\n"
            "Спробуй:\n"
            "• іншу назву\n"
            "• додати виконавця\n"
            "• англійською"
        )
        return

    # 🔥 TOP завжди перший
    top = results[0]
    rest = results[1:5]
    final_results = [top] + rest

    # 🖼️ СПОЧАТКУ КАРТИНКА
    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(final_results):
        raw_title = r.get("title", "Без назви")
        title = raw_title.split("(")[0].split("[")[0][:35].strip()
        video_id = r.get("id")

        if i == 0:
            emoji = "🔥"
        else:
            emoji = "🎵" if i % 2 == 0 else "🔥"

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
# ⬇️ НАДСИЛАННЯ АУДІО
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


