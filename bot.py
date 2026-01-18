import os
import random
import threading
import requests
import telebot
from telebot import types
from yt_dlp import YoutubeDL

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

# ⛔ ГАРАНТОВАНО ВИМИКАЄМО WEBHOOK
requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

bot = telebot.TeleBot(TOKEN, threaded=False)

# 🔒 БЛОКУВАННЯ (щоб не дублювало)
LOCK = threading.Lock()

# 🖼️ ФОТО (одне випадкове за запит)
PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

# 🔎 ПОШУК
YDL_SEARCH = {
    "quiet": True,
    "default_search": "ytsearch25",
    "noplaylist": True,
}

# ⬇️ АУДІО
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
}

REMIX_WORDS = [
    "remix", "slowed", "sped", "speed",
    "nightcore", "reverb", "edit", "bass"
]

# =====================
# START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Музичний бот\n\n"
        "✍️ Напиши назву пісні або виконавця\n"
        "🔥 1–3 оригінали → ремікси\n"
        "⚡ Швидко і стабільно"
    )

# =====================
# ПОШУК (ОДИН РАЗ)
# =====================
@bot.message_handler(content_types=["text"])
def search_music(message):
    if not LOCK.acquire(blocking=False):
        return  # ⛔ інший воркер вже обробляє

    try:
        chat_id = message.chat.id
        query = message.text.strip()

        status = bot.send_message(chat_id, "🔍 Шукаю музику…")

        with YoutubeDL(YDL_SEARCH) as ydl:
            data = ydl.extract_info(query, download=False)
            entries = data.get("entries", [])

        if not entries:
            bot.edit_message_text("❌ Нічого не знайшов", chat_id, status.message_id)
            return

        # 🧠 прибираємо дублікати + ділимо
        seen = set()
        originals, remixes = [], []

        for e in entries:
            vid = e.get("id")
            title_low = (e.get("title") or "").lower()

            if not vid or vid in seen:
                continue
            seen.add(vid)

            if any(w in title_low for w in REMIX_WORDS):
                remixes.append(e)
            else:
                originals.append(e)

        final = (originals[:3] + remixes)[:15]

        # 🖼️ ОДНЕ ФОТО
        bot.send_photo(
            chat_id,
            random.choice(PHOTOS),
            caption="🎶 Обери пісню 👇"
        )

        keyboard = types.InlineKeyboardMarkup()

        for i, e in enumerate(final):
            title = e.get("title", "Без назви")
            title = title.split("(")[0].split("[")[0][:40]
            vid = e.get("id")
            emoji = "🔥" if i % 2 == 0 else "🎵"

            keyboard.add(
                types.InlineKeyboardButton(
                    f"{emoji} {title}",
                    callback_data=f"{vid}|{title}"
                )
            )

        bot.edit_message_text(
            "👇 Список пісень:",
            chat_id,
            status.message_id,
            reply_markup=keyboard
        )

    finally:
        LOCK.release()

# =====================
# АУДІО
# =====================
@bot.callback_query_handler(func=lambda c: True)
def send_audio(call):
    chat_id = call.message.chat.id
    vid, title = call.data.split("|", 1)

    bot.send_message(chat_id, "⬇️ Надсилаю трек…")

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

