import os
import time
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# =====================
# 🔐 TOKEN
# =====================
TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

# очищає всі старі webhook / polling (409 fix)
telebot.apihelper.delete_webhook(TOKEN)

bot = telebot.TeleBot(TOKEN)

# =====================
# ⚡ КЕШ (ПРИСКОРЕННЯ)
# =====================
CACHE = {}
CACHE_TTL = 300  # 5 хвилин

# =====================
# 🎵 yt-dlp MP3
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
# 🔍 ШВИДКИЙ ПОШУК
# =====================
def search_music(query: str):
    now = time.time()

    # кеш
    if query in CACHE:
        data, ts = CACHE[query]
        if now - ts < CACHE_TTL:
            return data

    search_opts = {
        "quiet": True,
        "default_search": "ytsearch8",  # швидше
        "noplaylist": True,
        "extract_flat": "in_playlist",  # МЕНШЕ ДАНИХ → ШВИДШЕ
    }

    with YoutubeDL(search_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        results = info.get("entries", [])

    CACHE[query] = (results, now)
    return results

# =====================
# 🧠 СОРТУВАННЯ
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
# ▶️ /start
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Напиши назву пісні або виконавця\n"
        "⚡ Працюю швидко, без лагів"
    )

# =====================
# 🔎 ОБРОБКА ТЕКСТУ
# =====================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    query = message.text.strip()

    bot.send_message(message.chat.id, "🔍 Шукаю...")

    results = search_music(query)
    if not results:
        bot.send_message(message.chat.id, "❌ Нічого не знайшов")
        return

    results = sort_tracks(results)[:10]  # показуємо 10

    keyboard = types.InlineKeyboardMarkup()
    for r in results:
        title = r.get("title", "Без назви")[:60]
        url = r.get("url") or r.get("webpage_url")
        if url:
            keyboard.add(
                types.InlineKeyboardButton(
                    title, callback_data=url
                )
            )

    bot.send_message(
        message.chat.id,
        "🎶 Обери трек:",
        reply_markup=keyboard
    )

# =====================
# ⬇️ ЗАВАНТАЖЕННЯ MP3
# =====================
@bot.callback_query_handler(func=lambda call: True)
def download_song(call):
    chat_id = call.message.chat.id
    url = call.data

    bot.send_message(chat_id, "⬇️ Завантажую mp3...")

    try:
        with YoutubeDL(YDL_AUDIO_OPTS) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            filename = filename.rsplit(".", 1)[0] + ".mp3"

        with open(filename, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(filename)

    except Exception:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# =====================
# 🚀 ЗАПУСК
# =====================
bot.infinity_polling(skip_pending=True)

