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
        "Напиши назву пісні — я знайду і надішлю mp3."
    )

def find_video_url(query):
    try:
        cmd = [
            "yt-dlp",
            "--flat-playlist",
            "--print", "webpage_url",
            f"ytsearch1:{query}"
        ]
        result = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return result.strip()
    except:
        return None

def download_audio(chat_id, url):
    try:
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "--no-playlist",
                "-o", os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
                url
            ],
            check=True
        )

        for f in os.listdir(DOWNLOAD_DIR):
            if f.endswith(".mp3"):
                path = os.path.join(DOWNLOAD_DIR, f)
                with open(path, "rb") as audio:
                    bot.send_audio(chat_id, audio)
                os.remove(path)
                return

        bot.send_message(chat_id, "❌ Не вдалося завантажити трек")

    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

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

print("MUSIC BOT STARTED")
bot.infinity_polling(skip_pending=True, none_stop=True)


