import os
import random
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL

# =====================
# 🔐 TOKEN
# =====================
TOKEN = "ВСТАВ_СВІЙ_ТОКЕН"
bot = telebot.TeleBot(TOKEN)

telebot.apihelper.delete_webhook(TOKEN)

# =====================
# 🖼️ КАРТИНКИ
# =====================
IMAGES = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
]

# =====================
# ⚡ AUDIO
# =====================
YDL_AUDIO = {
    "format": "bestaudio[ext=m4a]/bestaudio",
    "quiet": True,
    "noplaylist": True,
    "outtmpl": "%(id)s.%(ext)s",
}

# =====================
# 🔎 НАДІЙНИЙ ПОШУК
# =====================
def search_music(query):
    try:
        with YoutubeDL({
            "quiet": True,
            "default_search": "ytsearch10",
            "noplaylist": True,
        }) as ydl:
            data = ydl.extract_info(query, download=False)
            return data.get("entries", [])
    except Exception:
        return []

# =====================
# 🧠 ОРИГІНАЛ / РЕМІКС
# =====================
def split_results(results):
    remix_words = [
        "remix", "slowed", "sped", "speed",
        "bass", "reverb", "nightcore", "edit"
    ]

    originals, remixes = [], []

    for r in results:
        title = (r.get("title") or "").lower()
        if any(w in title for w in remix_words):
            remixes.append(r)
        else:
            originals.append(r)

    return originals, remixes

# =====================
# ▶️ START
# =====================
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎧 Музичний бот\n\n"
        "✍️ Напиши назву пісні\n"
        "🔗 або встав TikTok-посилання\n\n"
        "🔥 1–3 оригінали → ремікси\n"
        "⚡ Працює стабільно"
    )

# =====================
# 🟢 ЄДИНИЙ ТЕКСТОВИЙ HANDLER
# =====================
@bot.message_handler(content_types=["text"])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    bot.send_message(chat_id, "🔍 Шукаю музику...")

    # TikTok → чистимо посилання
    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    results = search_music(query)
    if not results:
        bot.send_message(chat_id, "❌ Не знайшов 😔 Спробуй іншу назву")
        return

    originals, remixes = split_results(results)
    final = (originals[:3] + remixes)[:10]

    bot.send_photo(
        chat_id,
        random.choice(IMAGES),
        caption="🎶 Обери трек 👇"
    )

    keyboard = types.InlineKeyboardMarkup()

    for i, r in enumerate(final):
        title = (r.get("title") or "Без назви")
        title = title.split("(")[0].split("[")[0][:35].strip()
        video_id = r.get("id")

        emoji = "🔥" if i % 2 == 0 else "🎵"

        keyboard.add(
            types.InlineKeyboardButton(
                f"{emoji} {title}",
                callback_data=f"{video_id}|{title}"
            )
        )

    bot.send_message(chat_id, "👇 Список пісень:", reply_markup=keyboard)

# =====================
# ⬇️ AUDIO
# =====================
@bot.callback_query_handler(func=lambda call: True)
def send_audio(call):
    chat_id = call.message.chat.id
    video_id, title = call.data.split("|", 1)

    bot.send_message(chat_id, "⬇️ Надсилаю трек...")

    with YoutubeDL(YDL_AUDIO) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}",
            download=True
        )
        filename = ydl.prepare_filename(info)

    with open(filename, "rb") as audio:
        bot.send_audio(chat_id, audio, title=title)

    os.remove(filename)

# =====================
# 🚀 RUN
# =====================
bot.infinity_polling(skip_pending=True)
