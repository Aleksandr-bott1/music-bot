import telebot
import subprocess
import os
import time

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Музичний бот\n\n"
        "Напиши назву пісні — я знайду і надішлю аудіо."
    )

# ---------- ПОШУК ----------
def find_video_url(query):
    try:
        result = subprocess.check_output(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print", "webpage_url",
                f"ytsearch1:{query}"
            ],
            text=True,
            stderr=subprocess.DEVNULL
        )
        return result.strip()
    except:
        return None

# ---------- ЗАВАНТАЖЕННЯ ----------
def download_audio(chat_id, url):
    try:
        # очищаємо папку
        for f in os.listdir(DOWNLOAD_DIR):
            os.remove(os.path.join(DOWNLOAD_DIR, f))

        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "-f", "bestaudio",
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

    except Exception as e:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# ---------- ТЕКСТ ----------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    query = message.text.strip()

    bot.send_message(chat_id, "🔍 Шукаю...")

    url = find_video_url(query)
    if not url:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    download_audio(chat_id, url)

print("BOT STARTED")
bot.infinity_polling(skip_pending=True, none_stop=True)
