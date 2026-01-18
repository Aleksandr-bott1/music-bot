import os
import re
import random
import time
import telebot
from telebot import types
from yt_dlp import YoutubeDL

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"
bot = telebot.TeleBot(TOKEN)

# =========================
# КОНСТАНТИ
# =========================
MAX_RESULTS = 15
ORIGINAL_LIMIT = 3

REMIX_WORDS = [
    "remix", "slowed", "sped", "speed",
    "nightcore", "reverb", "edit", "bass"
]

PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

# =========================
# yt-dlp: ПОШУК
# =========================
YDL_FAST = {
    "quiet": True,
    "default_search": "ytsearch20",
    "extract_flat": True,
    "noplaylist": True,
}

YDL_FALLBACK = {
    "quiet": True,
    "default_search": "ytsearch15",
    "noplaylist": True,
}

# =========================
# yt-dlp: АУДІО
# =========================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
}

# =========================
# START (ГАРАНТОВАНА ВІДПОВІДЬ)
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "✅ Я живий!\n\n"
        "🎧 Напиши назву пісні або виконавця\n"
        "🔗 Можна вставити TikTok-посилання\n"
        "🔥 1–3 оригінали → ремікси"
    )

# =========================
# ECHO (ЩОБ НЕ МОВЧАВ НІКОЛИ)
# =========================
@bot.message_handler(func=lambda m: True)
def main_handler(message):
    chat_id = message.chat.id
    text = (message.text or "").strip()

    # якщо це не текст — просто підтвердимо
    if not text:
        bot.send_message(chat_id, "🟢 Отримав повідомлення")
        return

    # показуємо, що бот реагує
    bot.send_message(chat_id, "🔍 Шукаю...")

    # чистимо URL (TikTok / YouTube)
    query = re.sub(r"https?://\S+", "", text).strip()
    if not query:
        query = text

    entries = []

    # швидкий пошук
    try:
        with YoutubeDL(YDL_FAST) as ydl:
            data = ydl.extract_info(query, download=False)
            entries = data.get("entries", [])
    except Exception:
        entries = []

    # fallback
    if not entries:
        try:
            with YoutubeDL(YDL_FALLBACK) as ydl:
                data = ydl.extract_info(query, download=False)
                entries = data.get("entries", [])
        except Exception:
            entries = []

    if not entries:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    # =========================
    # ФІЛЬТРАЦІЯ
    # =========================
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

    final_tracks = originals[:ORIGINAL_LIMIT] + remixes
    final_tracks = final_tracks[:MAX_RESULTS]

    if not final_tracks:
        bot.send_message(chat_id, "❌ Нічого не підійшло")
        return

    # =========================
    # UI
    # =========================
    bot.send_photo(chat_id, random.choice(PHOTOS))
    bot.send_message(chat_id, "🎶 Обери пісню:")

    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, t in enumerate(final_tracks):
        title = t.get("title", "Без назви")
        title = title.split("(")[0].split("[")[0][:40]
        emoji = "🔥" if i % 2 == 0 else "🎵"
        kb.add(types.InlineKeyboardButton(
            f"{emoji} {title}",
            callback_data=f"{t['id']}|{title}"
        ))

    bot.send_message(chat_id, "👇 Список пісень:", reply_markup=kb)

# =========================
# ЗАВАНТАЖЕННЯ АУДІО
# =========================
@bot.callback_query_handler(func=lambda call: True)
def send_audio(call):chat_id = call.message.chat.id
    try:
        vid, title = call.data.split("|", 1)
    except ValueError:
        bot.send_message(chat_id, "❌ Помилка вибору")
        return

    bot.send_message(chat_id, "⬇️ Завантажую трек...")

    try:
        with YoutubeDL(YDL_AUDIO) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid}",
                download=True
            )
            filename = ydl.prepare_filename(info)
    except Exception:
        bot.send_message(chat_id, "❌ Не вдалося завантажити")
        return

    try:
        with open(filename, "rb") as f:
            bot.send_audio(chat_id, f, title=title)
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# =========================
# RUN (З ПЕРЕЗАПУСКОМ)
# =========================
print("BOT STARTED")
while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)




