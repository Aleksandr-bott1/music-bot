import os
import re
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from flask import Flask, request

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# =====================
# yt-dlp налаштування
# =====================
YDL_SEARCH = {
    "quiet": True,
    "default_search": "ytsearch25",
    "noplaylist": True,
}

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
        "🔥 1–3 оригінали → ремікси\n"
        "⚡ Без повторів"
    )

# =====================
# ПОШУК (1 РАЗ)
# =====================
@bot.message_handler(content_types=["text"])
def search_music(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # TikTok → прибираємо URL, лишаємо текст
    if "tiktok.com" in text:
        query = re.sub(r"https?://\S+", "", text).strip()
        if not query:
            query = "music"
    else:
        query = text

    status = bot.send_message(chat_id, "🔍 Шукаю...")

    try:
        with YoutubeDL(YDL_SEARCH) as ydl:
            data = ydl.extract_info(query, download=False)
            entries = data.get("entries", [])
    except Exception:
        bot.edit_message_text("❌ Помилка пошуку", chat_id, status.message_id)
        return

    if not entries:
        bot.edit_message_text("❌ Нічого не знайшов", chat_id, status.message_id)
        return

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
        "🎶 Обери пісню:",
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
# WEBHOOK
# =====================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(
        request.stream.read().decode("utf-8")
    )
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot is running", 200

# =====================
# RUN
# =====================
if name == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{os.environ.get('RAILWAY_STATIC_URL')}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
