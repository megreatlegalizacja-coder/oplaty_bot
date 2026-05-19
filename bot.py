import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        ["ХОЧУ ОПЛАТИТИ ОПЛАТИ СКАРБОВІ"]
    ]

    await update.message.reply_text(
        "Привіт 👋",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "ХОЧУ ОПЛАТИТИ ОПЛАТИ СКАРБОВІ":

        keyboard = [
            ["Dolnośląskie"],
            ["Mazowieckie"],
            ["Małopolskie"],
            ["Śląskie"]
        ]

        await update.message.reply_text(
            "Оберіть воєводство:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    elif text == "Dolnośląskie":

        keyboard = [
            ["Тимчасове перебування"],
            ["Постійне перебування"],
            ["Резидент ЄС"],
            ["Громадянство"],
            ["Друк карти побиту"],
            ["Доручення"]
        ]

        await update.message.reply_text(
            "За що платимо?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    elif text == "Тимчасове перебування":

        keyboard = [
            ["ТАК, по роботі"],
            ["НІ, не по роботі"]
        ]

        await update.message.reply_text(
            "Чи по роботі?",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    elif text == "ТАК, по роботі":

        await update.message.reply_text(
            """
✅ Дані для оплати готові

📌 У полі «ОТРИМУВАЧ»:

Dolnośląski Urząd Wojewódzki

📌 У полі «НОМЕР РАХУНКУ»:

00 0000 0000 0000 0000 0000 0000

📌 У полі «СУМА»:

440 zł

📌 У полі «ПРИЗНАЧЕННЯ ПЛАТЕЖУ»:

Opłata za pobyt czasowy i pracę
"""
        )

    elif text == "НІ, не по роботі":

        await update.message.reply_text(
            """
✅ Дані для оплати готові

📌 У полі «ОТРИМУВАЧ»:

Dolnośląski Urząd Wojewódzki

📌 У полі «НОМЕР РАХУНКУ»:

00 0000 0000 0000 0000 0000 0000

📌 У полі «СУМА»:

340 zł

📌 У полі «ПРИЗНАЧЕННЯ ПЛАТЕЖУ»:

Opłata za pobyt czasowy
"""
        )


def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT,
            message_handler
        )
    )

    print("Bot works.")

    app.run_polling()


if __name__ == "__main__":
    main()
