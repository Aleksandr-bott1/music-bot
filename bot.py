import telebot
import subprocess
import os

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Музичний бот\n\n"
        "Напиши назву пісні — я знайду і надішлю аудіо."
    )

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

def download_audio(chat_id, url):
    try:
        subprocess.run(
            [
                "yt-dlp",
                "--no-playlist",
                "-o", os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
                url
            ],
            check=True
        )

        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith((".m4a", ".webm", ".mp3")):
                path = os.path.join(DOWNLOAD_DIR, f)
                with open(path, "rb") as audio:
                    bot.send_audio(chat_id, audio)
                os.remove(path)
                return

        bot.send_message(chat_id, "❌ Не вдалося отримати аудіо")

    except:
        bot.send_message(chat_id, "❌ Помилка під час завантаження")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    query = message.text.strip()

    bot.send_message(chat_id, "🔍 Шукаю...")

    url = find_video_url(query)
    if not url:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return
