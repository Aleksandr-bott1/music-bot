import os
import re
import random
import telebot
from telebot import types
from yt_dlp import YoutubeDL

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"
bot = telebot.TeleBot(TOKEN)

# =====================
# ФОТО
# =====================
PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

# =====================
# yt-dlp: ПОШУК (ШВИДКО)
# =====================
YDL_FAST = {
    "quiet": True,
    "default_search": "ytsearch25",
    "extract_flat": True,
    "noplaylist": True,
}

YDL_SAFE = {
    "quiet": True,
    "default_search": "ytsearch25",
    "noplaylist": True,
}

# =====================
# yt-dlp: АУДІО (ШВИДКО)
# =====================
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
        "✍️ Напиши назву пісні\n"
        "🔗 або встав TikTok-посилання\n\n"
        "🔥 1–3 оригінали → ремікси"
    )

# =====================
# ПОШУК
# =====================
@bot.message_handler(content_types=["text"])
def search_music(message):
    chat_id = message.chat.id
    text = message.text.strip()

    status = bot.send_message(chat_id, "🔍 Шукаю музику...")

    # TikTok → прибираємо URL
    query = re.sub(r"https?://\S+", "", text).strip()
    if not query:
        query = text

    results = []

    # швидкий flat-пошук
    try:
        with YoutubeDL(YDL_FAST) as ydl:
            data = ydl.extract_info(query, download=False)
            results = data.get("entries", [])
    except Exception:
        results = []

    # fallback
    if not results:
        try:
            with YoutubeDL(YDL_SAFE) as ydl:
                data = ydl.extract_info(query, download=False)
                results = data.get("entries", [])
        except Exception:
            results = []

    if not results:
        bot.edit_message_text("❌ Нічого не знайшов", chat_id, status.message_id)
        return

    seen = set()
    originals, remixes = [], []

    for r in results:
        vid = r.get("id")
        title_low = (r.get("title") or "").lower()

        if not vid or vid in seen:
            continue
        seen.add(vid)

        if any(w in title_low for w in REMIX_WORDS):
            remixes.append(r)
        else:
            originals.append(r)

    final = (originals[:3] + remixes)[:15]

    # Фото
    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        caption="🎶 Обери пісню 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(final):
        title = r.get("title", "Без назви")
        title = title.split("(")[0].split("[")[0][:40]
        vid = r.get("id")
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

# =====================
# АУДІО
# =====================
@bot.callback_query_handler(func=lambda c: True)
def send_audio(call):
    chat_id = call.message.chat.id
    vid, title = call.data.split("|", 1)

    bot.send_message(chat_id, "⬇️ Завантажую трек...")

    with YoutubeDL(YDL_AUDIO) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={vid}",
            download=True
        )
        filename = ydl.prepare_filename(info)

    with open(filename, "rb") as f:
        bot.send_audio(chat_id, f, title=title)

    os.remove(filename)
    bot.send_message(chat_id, "⬇️ Завантажую трек…")
    # =====================
# RUN
# =====================
bot.infinity_polling(skip_pending=True)



