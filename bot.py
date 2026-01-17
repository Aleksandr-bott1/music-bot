import telebot
import subprocess
import os
import re
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}

# ===== НАЛАШТУВАННЯ =====
BAD_WORDS = [
    "karaoke", "live", "cover", "instrumental",
    "acapella", "acoustic", "concert"
]

# ⏩ ЗМЕНШЕНО ДЛЯ ШВИДКОСТІ (але якість лишилась)
REMIX_TAGS = [
    "remix",
    "phonk",
    "bass boosted"
]

TIKTOK_REGEX = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")

# ===== ФУНКЦІЇ =====
def is_bad(title):
    title = title.lower()
    return any(w in title for w in BAD_WORDS)

def search_soundcloud(query, count):
    cmd = [
        "yt-dlp",
        "--print", "title",
        "--print", "webpage_url",
        f"scsearch{count}:{query}"
    ]
    out = subprocess.check_output(cmd, text=True)
    lines = out.strip().split("\n")
    return list(zip(lines[0::2], lines[1::2]))

def download_audio(chat_id, url):
    output = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")
    try:
        subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output, url],
            check=True
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
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "🔥 Потужний музичний бот\n\n"
        "✍️ Напиши назву пісні — оригінали + ремікси\n"
        "🔗 Або встав TikTok-посилання 🎶"
    )

# ===== MAIN HANDLER =====
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # --- TikTok ---
    if TIKTOK_REGEX.search(text):
        bot.send_message(chat_id, "🎶 Дістаю звук з TikTok...")
        download_audio(chat_id, text)
        return

    bot.send_message(chat_id, "🔍 Шукаю оригінали та ремікси...")

    results = []

    # --- ОРИГІНАЛИ (1–3) ---
    try:
        originals = search_soundcloud(text, 3)
        for title, url in originals:
            if not is_bad(title):
                results.append(("🎵", title, url))
    except:
        pass

    # --- РЕМІКСИ (швидше) ---
    for tag in REMIX_TAGS:
        try:
            remixes = search_soundcloud(f"{text} {tag}", 3)
            for title, url in remixes:
                if not is_bad(title):
                    results.append(("🔥", title, url))
        except:
            pass

    if not results:
        bot.send_message(chat_id, "❌ Нічого не знайшов")
        return

    results = results[:20]
    user_results[chat_id] = results

    keyboard = InlineKeyboardMarkup(row_width=1)
    for i, (icon, title, _) in enumerate(results):
        keyboard.add(
            InlineKeyboardButton(
                text=f"{icon} {title[:60]}",
                callback_data=str(i)
            )
        )

    bot.send_message(chat_id, "🎶 Обери трек:", reply_markup=keyboard)

# ===== BUTTON CLICK =====
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    chat_id = call.message.chat.id
    index = int(call.data)

    if chat_id not in user_results:
        bot.answer_callback_query(call.id, "❌ Список застарів")
        return

    _, _, url = user_results[chat_id][index]
    bot.answer_callback_query(call.id, "⏳ Завантажую...")
    download_audio(chat_id, url)
    del user_results[chat_id]

print("🔥 Бот запущений (FULL + FAST)")
bot.infinity_polling()