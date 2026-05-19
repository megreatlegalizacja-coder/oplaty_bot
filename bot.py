import os
import re
from io import BytesIO
from datetime import datetime

import pandas as pd
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters


BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_URL = os.getenv("SHEET_URL")


def sheet_export_url(url):
    match = re.search(r"/d/([^/]+)", url or "")
    if match:
        return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=xlsx"
    return url


def load_database():
    response = requests.get(sheet_export_url(SHEET_URL), timeout=30)
    response.raise_for_status()
    xlsx = BytesIO(response.content)

    voivodeships = pd.read_excel(xlsx, sheet_name="voivodeships").fillna("")
    xlsx.seek(0)
    accounts = pd.read_excel(xlsx, sheet_name="accounts").fillna("")
    xlsx.seek(0)
    routes = pd.read_excel(xlsx, sheet_name="payment_routes").fillna("")

    return {
        "voivodeships": voivodeships,
        "accounts": accounts,
        "routes": routes,
    }


DB = load_database()


FINAL_PAYMENTS = {
    "ТАК, по роботі": {
        "payment_type_id": "pobyt_praca",
        "label": "Pobyt czasowy i praca",
        "amount": 440,
        "title": "Opłata skarbowa za zezwolenie na pobyt czasowy i pracę dla {full_name}, ur. {birth_date}",
    },
    "НІ, не по роботі": {
        "payment_type_id": "pobyt_czasowy",
        "label": "Pobyt czasowy",
        "amount": 340,
        "title": "Opłata skarbowa za zezwolenie na pobyt czasowy dla {full_name}, ur. {birth_date}",
    },
    "На підставі карти Поляка": {
        "payment_type_id": "pobyt_staly_karta_polaka",
        "label": "Pobyt stały na podstawie Karty Polaka",
        "amount": 0,
        "free": True,
        "title": "",
    },
    "Без карти Поляка": {
        "payment_type_id": "pobyt_staly",
        "label": "Pobyt stały",
        "amount": 640,
        "title": "Opłata skarbowa za zezwolenie na pobyt stały dla {full_name}, ur. {birth_date}",
    },
    "Резидент ЄС": {
        "payment_type_id": "rezydent_ue",
        "label": "Rezydent długoterminowy UE",
        "amount": 640,
        "title": "Opłata skarbowa za zezwolenie na pobyt rezydenta długoterminowego UE dla {full_name}, ur. {birth_date}",
    },
    "Громадянство": {
        "payment_type_id": "obywatelstwo",
        "label": "Uznanie za obywatela polskiego",
        "amount": 1000,
        "title": "Opłata za wniosek o uznanie za obywatela polskiego dla {full_name}, ur. {birth_date}",
    },
    "Карта CUKR": {
        "payment_type_id": "karta_cukr",
        "label": "Karta CUKR",
        "amount": 100,
        "title": "Opłata za wydanie karty pobytu CUKR dla {full_name}, ur. {birth_date}",
    },
    "Повнолітня особа без пільг": {
        "payment_type_id": "karta_100",
        "label": "Karta pobytu tradycyjna 100%",
        "amount": 100,
        "title": "Opłata za wydanie karty pobytu dla {full_name}, ur. {birth_date}",
    },
    "Пільгова оплата": {
        "payment_type_id": "karta_50",
        "label": "Karta pobytu tradycyjna 50%",
        "amount": 50,
        "title": "Opłata za wydanie karty pobytu - ulga 50% dla {full_name}, ur. {birth_date}",
    },
    "Доручення": {
        "payment_type_id": "pelnomocnictwo",
        "label": "Pełnomocnictwo",
        "amount": 17,
        "needs_proxy": True,
        "title": "Opłata skarbowa od pełnomocnictwa: {proxy_name}, sprawa osoby: {full_name}, ur. {birth_date}",
    },
}


def make_keyboard(items, row_size=2):
    rows = []
    row = []

    for item in items:
        row.append(str(item))
        if len(row) == row_size:
            rows.append(row)
            row = []

    if row:
        rows.append(row)

    rows.append(["🔄 Почати спочатку"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def is_latin_name(name):
    return re.fullmatch(r"^[A-Za-zÀ-ÿ' -]+$", name.strip()) is not None


def validate_birth_date(date_text):
    try:
        birth = datetime.strptime(date_text, "%d.%m.%Y")
        today = datetime.today()

        if birth > today:
            return False

        age = today.year - birth.year
        if age > 120:
            return False

        return True
    except ValueError:
        return False


def get_voivodeship(name):
    rows = DB["voivodeships"][DB["voivodeships"]["name_pl"] == name]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


def get_route(voivodeship_id, payment_type_id):
    routes = DB["routes"]
    rows = routes[
        (routes["voivodeship_id"] == voivodeship_id)
        & (routes["payment_type_id"] == payment_type_id)
    ]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


def get_account(account_id):
    rows = DB["accounts"][DB["accounts"]["account_id"] == account_id]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "Привіт 👋\nЯ допоможу підготувати оплату.",
        reply_markup=ReplyKeyboardMarkup(
            [["ХОЧУ ОПЛАТИТИ ОПЛАТИ СКАРБОВІ"]],
            resize_keyboard=True,
        ),
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if text == "🔄 Почати спочатку":
        return await start(update, context)

    step = context.user_data.get("step")

    if text == "ХОЧУ ОПЛАТИТИ ОПЛАТИ СКАРБОВІ":
        context.user_data["step"] = "voivodeship"
        names = DB["voivodeships"]["name_pl"].tolist()

        await update.message.reply_text(
            "Оберіть воєводство:",
            reply_markup=make_keyboard(names, 2),
        )
        return

    if step == "voivodeship":
        voivodeship = get_voivodeship(text)

        if not voivodeship:
            await update.message.reply_text("Оберіть воєводство з кнопок.")
            return

        context.user_data["voivodeship"] = voivodeship
        context.user_data["step"] = "main_payment_category"

        await update.message.reply_text(
            "За що платимо?",
            reply_markup=make_keyboard(
                [
                    "Тимчасове перебування",
                    "Постійне перебування",
                    "Резидент ЄС",
                    "Громадянство",
                    "Друк карти побиту",
                    "Доручення",
                ],
                1,
            ),
        )
        return

    if step == "main_payment_category":
        if text == "Тимчасове перебування":
            context.user_data["step"] = "temporary_work"
            await update.message.reply_text(
                "Чи по роботі?",
                reply_markup=make_keyboard(["ТАК, по роботі", "НІ, не по роботі"], 1),
            )
            return

        if text == "Постійне перебування":
            context.user_data["step"] = "permanent_basis"
            await update.message.reply_text(
                "Оберіть підставу:",
                reply_markup=make_keyboard(["На підставі карти Поляка", "Без карти Поляка"], 1),
            )
            return

        if text == "Друк карти побиту":
            context.user_data["step"] = "card_type"
            await update.message.reply_text(
                "Оберіть тип карти:",
                reply_markup=make_keyboard(["Карта CUKR", "Karta Pobytu tradycyjna (Nie CUKR)"], 1),
            )
            return

        if text in ["Резидент ЄС", "Громадянство", "Доручення"]:
            context.user_data["selected_payment"] = FINAL_PAYMENTS[text]
            context.user_data["step"] = "full_name"
            await update.message.reply_text(
                "Введіть ім’я та прізвище заявника ЛАТИНСЬКИМИ літерами.\nНаприклад: IVAN PETRENKO"
            )
            return

        await update.message.reply_text("Оберіть варіант з кнопок.")
        return

    if step in ["temporary_work", "permanent_basis"]:
        if text not in FINAL_PAYMENTS:
            await update.message.reply_text("Оберіть варіант з кнопок.")
            return

        context.user_data["selected_payment"] = FINAL_PAYMENTS[text]

        if FINAL_PAYMENTS[text].get("free"):
            result = build_result(context.user_data)
            context.user_data.clear()
            await update.message.reply_text(result)
            return

        context.user_data["step"] = "full_name"
        await update.message.reply_text(
            "Введіть ім’я та прізвище заявника ЛАТИНСЬКИМИ літерами.\nНаприклад: IVAN PETRENKO"
        )
        return

    if step == "card_type":
        if text == "Карта CUKR":
            context.user_data["selected_payment"] = FINAL_PAYMENTS[text]
            context.user_data["step"] = "full_name"
            await update.message.reply_text(
                "Введіть ім’я та прізвище заявника ЛАТИНСЬКИМИ літерами.\nНаприклад: IVAN PETRENKO"
            )
            return

        if text == "Karta Pobytu tradycyjna (Nie CUKR)":
            context.user_data["step"] = "traditional_card_discount"
            await update.message.reply_text(
                "Оберіть варіант:",
                reply_markup=make_keyboard(["Повнолітня особа без пільг", "Пільгова оплата"], 1),
            )
            return

        await update.message.reply_text("Оберіть варіант з кнопок.")
        return

    if step == "traditional_card_discount":
        if text not in FINAL_PAYMENTS:
            await update.message.reply_text("Оберіть варіант з кнопок.")
            return

        context.user_data["selected_payment"] = FINAL_PAYMENTS[text]
        context.user_data["step"] = "full_name"
        await update.message.reply_text(
            "Введіть ім’я та прізвище заявника ЛАТИНСЬКИМИ літерами.\nНаприклад: IVAN PETRENKO"
        )
        return

    if step == "full_name":
        if not is_latin_name(text):
            await update.message.reply_text(
                "⚠️ Введіть ім’я та прізвище тільки латинськими літерами.\nНаприклад: IVAN PETRENKO"
            )
            return

        context.user_data["full_name"] = text.upper()
        context.user_data["step"] = "birth_date"

        await update.message.reply_text(
            "Введіть дату народження у форматі ДД.ММ.РРРР.\nНаприклад: 01.01.1990"
        )
        return

    if step == "birth_date":
        if not validate_birth_date(text):
            await update.message.reply_text(
                "⚠️ Невірна дата народження.\nВведіть дату у форматі ДД.ММ.РРРР.\nНаприклад: 01.01.1990"
            )
            return

        context.user_data["birth_date"] = text
        selected = context.user_data["selected_payment"]

        if selected.get("needs_proxy"):
            context.user_data["step"] = "proxy_name"
            await update.message.reply_text(
                "Введіть ім’я та прізвище довіреної особи ЛАТИНСЬКИМИ літерами.\nНаприклад: ANNA KOWALSKA"
            )
            return

        result = build_result(context.user_data)
        context.user_data.clear()
        await update.message.reply_text(result)
        return

    if step == "proxy_name":
        if not is_latin_name(text):
            await update.message.reply_text(
                "⚠️ Введіть ім’я та прізвище довіреної особи тільки латинськими літерами.\nНаприклад: ANNA KOWALSKA"
            )
            return

        context.user_data["proxy_name"] = text.upper()

        result = build_result(context.user_data)
        context.user_data.clear()
        await update.message.reply_text(result)
        return

    await update.message.reply_text("Натисніть /start, щоб почати.")


def build_result(data):
    voivodeship = data["voivodeship"]
    payment = data["selected_payment"]

    if payment.get("free"):
        return f"""
✅ Оплата не потрібна

Воєводство:
{voivodeship["name_pl"]}

Тип справи:
{payment["label"]}

📌 Сума оплати:
0 zł

Ця дія є безкоштовною.
Не виконуйте переказ.
Реквізити для оплати не потрібні.
"""

    route = get_route(voivodeship["voivodeship_id"], payment["payment_type_id"])

    if not route:
        return f"""
⚠️ У Google Sheets немає маршруту оплати.

Воєводство:
{voivodeship["name_pl"]}

Тип оплати:
{payment["label"]}

Payment type ID:
{payment["payment_type_id"]}

Додай цей payment_type_id у вкладку payment_routes.
"""

    account = get_account(route["account_id"])

    if not account:
        return "⚠️ Не знайдено рахунок у вкладці accounts."

    title = payment["title"].format(
        full_name=data.get("full_name", ""),
        birth_date=data.get("birth_date", ""),
        proxy_name=data.get("proxy_name", ""),
    )

    return f"""
✅ Дані для оплати готові

Оберіть у своєму банку звичайний переказ на рахунок.

📌 У полі «ОТРИМУВАЧ» / «ODBIORCA» встав:

{account["recipient"]}

📌 У полі «НОМЕР РАХУНКУ» / «NUMER RACHUNKU» встав:

{account["bank_account"]}

📌 У полі «СУМА ОПЛАТИ» / «KWOTA» встав:

{payment["amount"]} zł

📌 У полі «ПРИЗНАЧЕННЯ ПЛАТЕЖУ» / «TYTUŁ PRZELEWU» встав:

{title}

━━━━━━━━━━━━━━

Деталі справи:

Воєводство:
{voivodeship["name_pl"]}

Ужонд:
{voivodeship["office_name"]}

Тип оплати:
{payment["label"]}

Статус перевірки:
{route.get("verification_status", "")}

Джерело:
{route.get("source_url", "")}

⚠️ Перед оплатою перевірте реквізити на офіційній сторінці ужонду.
"""


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    print("Bot works.")
    app.run_polling()


if __name__ == "__main__":
    main()
