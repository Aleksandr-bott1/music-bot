import telebot

TOKEN = "8145219838:AAGkYaV13RtbAItOuPNt0Fp3bYyQI0msil4"

bot = telebot.TeleBot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "✅ Бот працює!\n\n"
        "Напиши будь-який текст — я відповім."
    )

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.send_message(
        message.chat.id,
        f"📩 Ти написав: {message.text}"
    )

print("BOT STARTED SUCCESSFULLY")
bot.infinity_polling(skip_pending=True, none_stop=True)

