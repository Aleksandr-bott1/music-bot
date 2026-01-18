import telebot
import subprocess
import os
import re
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

DOWNLOAD_DIR = "music"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

user_results = {}
active_search = set()

PHOTOS = [
    "https://images.unsplash.com/photo-1511379938547-c1f69419868d",
    "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f",
    "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4",
    "https://images.unsplash.com/photo-1506157786151-b8491531f063",
]

BAD_WORDS = ["karaoke", "live", "cover", "instrumental", "acoustic"]
REMIX_TAGS = ["remix", "phonk", "bass boosted", "sped up"]

TIKTOK_REGEX = re.compile(r"(tiktok\.com|vm\.tiktok\.com)")

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "🎵 Музичний бот\n\n"
        "✍️ Напиши назву пісні\n"
        "🔗 Або встав TikTok-посилання"
    )

# ---------- ПОШУК ----------
def search_youtube(query, limit):
    cmd = [
        "yt-dlp",
        "--print", "title",
        "--print", "webpage_url",
        f"ytsearch{limit}:{query}"
    ]
    out = subprocess.check_output(
        cmd,
        text=True,
        stderr=subprocess.DEVNULL,
        timeout=15  # ⬅️ ВАЖЛИВО: щоб НЕ мовчав
    )
    lines = out.strip().split("\n")
    return list(zip(lines[0::2], lines[1::2]))

def is_bad(title):
    t = title.lower()
    return any(w in t for w in BAD_WORDS)

# ---------- ЗАВАНТАЖЕННЯ ----------
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
            check=True,
            timeout=60
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

# ---------- ТЕКСТ ----------
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    if chat_id in active_search:
        bot.send_message(chat_id, "⏳ Зачекай, я ще шукаю…")
        return

    active_search.add(chat_id)
    msg = bot.send_message(chat_id, "🔍 Шукаю…")

    # TikTok
    if TIKTOK_REGEX.search(text):
        bot.edit_message_text("🎶 Дістаю звук з TikTok…", chat_id, msg.message_id)
        download_audio(chat_id, text)
        active_search.remove(chat_id)
        return

    results = []
    used = set()

    # ---- ОРИГІНАЛИ (1–3) ----
    try:
        for title, url in search_youtube(text, 6):
            if is_bad(title):
                continue
            key = title.lower()
            if key in used:
                continue
            used.add(key)
            results.append(("🎵", title, url))
            if len(results) == 3:
                break
    except:
        pass

    # ---- РЕМІКСИ ----
    for tag in REMIX_TAGS:
        try:
            for title, url in search_youtube(f"{text} {tag}", 6):
                if is_bad(title):
                    continue
                key = title.lower()
                if key in used:
                    continue
                used.add(key)
                results.append(("🔥", title, url))
                if len(results) >= 10:
                    break
        except:
            pass

    if not results:
        bot.edit_message_text("❌ Нічого не знайшов", chat_id, msg.message_id)
        active_search.remove(chat_id)
        return

    user_results[chat_id] = results

    kb = InlineKeyboardMarkup(row_width=1)
    for i, (icon, title, _) in enumerate(results):
        kb.add(
            InlineKeyboardButton(
                text=f"{icon} {title[:60]}",
                callback_data=str(i)
            )
        )

    bot.send_photo(
        chat_id,
        random.choice(PHOTOS),
        caption="🎶 Обери трек:",
        reply_markup=kb
    )

# ---------- КНОПКИ ----------
@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    chat_id = c.message.chat.id
    idx = int(c.data)

    if chat_id not in user_results:
        bot.answer_callback_query(c.id, "❌ Список застарів")
        return

    _, _, url = user_results[chat_id][idx]
    bot.answer_callback_query(c.id, "⏳ Завантажую…")
    download_audio(chat_id, url)

    user_results.pop(chat_id, None)
    active_search.discard(chat_id)

print("BOT STARTED — FINAL WITH TIMEOUT")
bot.infinity_polling(skip_pending=True, none_stop=True)
