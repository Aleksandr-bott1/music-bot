import os
import time
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
MUSIC_IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

# =====================
# ⚡ КЕШ
# =====================
CACHE = {}
CACHE_TTL = 300  # 5 хв

# =====================
# 🎵 yt-dlp (MP3)
# =====================
YDL_AUDIO_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

# =====================
# 🔍 ПОШУК (ШВИДКИЙ)
# =====================
def search_music(query):
    now = time.time()

    if query in CACHE:
        data, ts = CACHE[query]
        if now - ts < CACHE_TTL:
            return data

    opts = {
        "quiet": True,
        "default_search": "ytsearch15",
        "noplaylist": True,
        "extract_flat": "in_playlist",
    }

    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=False)
        results = info.get("entries", [])

    CACHE[query] = (results, now)
    return results

# =====================
# 🧠 ОРИГІНАЛ → РЕМІКСИ
# =====================
def sort_tracks(tracks):
    originals = []
    remixes = []

    remix_words = [
        "remix", "edit", "sped up", "slowed",
        "bass", "nightcore", "bootleg", "mix"
    ]

    for t in tracks:
        title = (t.get("title") or "").lower()
        if any(w in title for w in remix_words):
            remixes.append(t)
        else:
            originals.append(t)

    return originals + remixes

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎶 Привіт!\n\n"
        "🔍 Напиши назву пісні або виконавця\n"
        "⚡ Знайду швидко та красиво"
    )

# =====================
# 🔎 ТЕКСТ
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

    results = sort_tracks(results)[:10]

    # 🖼️ картинка
    bot.send_photo(
        chat_id,
        random.choice(MUSIC_IMAGES),
        caption="🎧 Знайдено треки — обирай 👇"
    )

    keyboard = types.InlineKeyboardMarkup()
    emojis = ["🎵", "🎶", "🔥", "🎧", "🎼"]

    for i, r in enumerate(results):
        title = r.get("title", "Без назви")[:55]
        video_id = r.get("id")
        emoji = emojis[i % len(emojis)]

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=video_id
            )
        )

    bot.send_message(
        chat_id,
        "👇 Обери пісню:",
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

    try:
        with YoutubeDL(YDL_AUDIO_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = filename.rsplit(".", 1)[0] + ".mp3"

        with open(filename, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(filename)


