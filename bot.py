import telebot
import subprocess
import os
import re
import time

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

active_search = set()
TIKTOK_REGEX = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Музичний бот\n\n"
        "✍️ Напиши назву пісні\n"
        "🔗 Або встав посилання з TikTok"
    )

def find_url(query):
    try:
        out = subprocess.check_output(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print", "webpage_url",
                f"ytsearch1:{query}"
            ],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        return out if out else None
    except:
        return None

def download_audio(chat_id, url):
    try:
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

        subprocess.run(
            [
                "yt-dlp",
                "-f", "bestaudio",
                "--no-playlist",
                "-o", os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s"),
                url
            ],
            check=True
        )

        time.sleep(1)

        files = os.listdir(DOWNLOAD_DIR)
        if not files:
            bot.send_message(chat_id, "❌ Аудіо не знайдено")
            return

        path = os.path.join(DOWNLOAD_DIR, files[0])
        with open(path, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(path)

    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in active_search:
        bot.send_message(chat_id, "⏳ Зачекай, я ще працюю…")
        return

    active_search.add(chat_id)

    if TIKTOK_REGEX.search(text):
        bot.send_message(chat_id, "🎶 Дістаю звук з TikTok…")
        download_audio(chat_id, text)
        active_search.remove(chat_id)
        return

    bot.send_message(chat_id, "🔍 Шукаю…")

    url = find_url(text)
    if not url:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        active_search.remove(chat_id)
        return

    download_audio(chat_id, url)
    active_search.remove(chat_id)

print("BOT STARTED — STABLE")
bot.infinity_polling(skip_pending=True, none_stop=True)
