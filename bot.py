import telebot
import subprocess
import os
import re
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}

PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

BAD_WORDS = [
    "karaoke", "live", "cover", "instrumental",
    "acapella", "acoustic", "concert"
]

REMIX_TAGS = ["remix", "phonk", "bass boosted"]
TIKTOK_REGEX = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")

# ===== yt-dlp runner (трохи швидше) =====
def run_yt_dlp(args):
    return subprocess.check_output(
        [
            "python", "-m", "yt_dlp",
            "--ignore-errors",
            "--no-warnings",
            "--socket-timeout", "8",
        ] + args,
        text=True,
        stderr=subprocess.DEVNULL,
        timeout=12
    )

def is_bad(title):
    title = title.lower()
    return any(w in title for w in BAD_WORDS)

def search_music(query, count):
    out = run_yt_dlp([
        "--flat-playlist",
        "--print", "title",
        "--print", "webpage_url",
        f"ytsearch{count}:{query}"
    ])
    lines = out.strip().split("\n")
    return list(zip(lines[0::2], lines[1::2]))

def download_audio(chat_id, url):
    try:
        subprocess.run(
            [
                "python", "-m", "yt_dlp",
                "-x",
                "--audio-format", "mp3",
                "--audio-quality", "0",
                "--no-playlist",
                "--quiet",
                "-o", os.path.join(DOWNLOAD_DIR, "%(id)s.%(ext)s"),
                url
            ],
            check=True,
            timeout=120
        )

        mp3_files = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".mp3")]
        if not mp3_files:
            bot.send_message(chat_id, "❌ Не вдалося отримати звук")
            return

        path = os.path.join(DOWNLOAD_DIR, mp3_files[0])
        with open(path, "rb") as audio:
            bot.send_audio(chat_id, audio)

        os.remove(path)

    except:
        bot.send_message(chat_id, "❌ Помилка при завантаженні")

# ===== START =====
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_photo(
        message.chat.id,
        random.choice(PHOTOS),
        caption=(
            "🔥 Потужний музичний бот\n\n"
            "✍️ Напиши назву пісні — оригінали + ремікси\n"
            "🔗 Або встав TikTok-посилання 🎶"
        )
    )

# ===== MAIN =====
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # очищаємо старі результати ТІЛЬКИ перед новим пошуком
    user_results.pop(chat_id, None)

    if TIKTOK_REGEX.search(text):
        bot.send_message(chat_id, "🎶 Дістаю звук з TikTok...")
        download_audio(chat_id, text)
        return

    bot.send_message(chat_id, "🔍 Шукаю...")

    results = []
    used = set()

    # 1–3 оригінали
    try:
        originals = search_music(text, 4)
        for title, url in originals:
            key = (title.lower(), url)
            if key in used or is_bad(title):
                continue
            used.add(key)
            results.append(("🎵", title, url))
            if len(results) >= 3:
                break
    except:
        pass

    # ремікси до 15
    for tag in REMIX_TAGS:
        if len(results) >= 15:
            break
        try:
            remixes = search_music(f"{text} {tag}", 4)
            for title, url in remixes:
                key = (title.lower(), url)
                if key in used or is_bad(title):
                    continue
                used.add(key)
                results.append(("🔥", title, url))
                if len(results) >= 15:
                    break
        except:
            pass

    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    user_results[chat_id] = results

    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, (icon, title, _) in enumerate(results):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{icon} {title[:60]}",
                callback_data=str(i)
            )
        )

    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        caption="🎶 Обери трек:",
        reply_markup=keyboard
    )

# ===== CALLBACK =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    index = int(call.data)

    if chat_id not in user_results or index >= len(user_results[chat_id]):
        bot.answer_callback_query(call.id, "❌ Список застарів")
        return

    _, _, url = user_results[chat_id][index]
    bot.answer_callback_query(call.id, "⏳ Завантажую...")
    download_audio(chat_id, url)

print("🔥 Бот запущений (STABLE)")
bot.infinity_polling(skip_pending=True, none_stop=True)
