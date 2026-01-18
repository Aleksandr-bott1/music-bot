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

def search_and_download(chat_id, query):
    try:
        # пошук + завантаження 1 найкращого треку
        subprocess.run(
            [
                "yt-dlp",
                "ytsearch1:" + query,
                "-x",
                "--audio-format", "mp3",
                "--no-playlist",
                "-o", os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
            ],
            check=True
        )

        for file in os.listdir(DOWNLOAD_DIR):
            if file.endswith(".mp3"):
                path = os.path.join(DOWNLOAD_DIR, file)
                with open(path, "rb") as audio:
                    bot.send_audio(chat_id, audio)
                os.remove(path)
                return

        bot.send_message(chat_id, "❌ Не вдалося завантажити трек")

    except Exception as e:
        bot.send_message(chat_id, "❌ Помилка при пошуку або завантаженні")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    bot.send_message(message.chat.id, "🔍 Шукаю...")
    search_and_download(message.chat.id, message.text)

print("MUSIC BOT STARTED")
bot.infinity_polling(skip_pending=True, none_stop=True)

print("BOT STARTED SUCCESSFULLY")
bot.infinity_polling(skip_pending=True, none_stop=True)


