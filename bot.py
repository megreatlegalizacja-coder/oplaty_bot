cd ~/oplaty_bot
nano bot.py%                                                                                                            (base) nikalexa@MacBook-Pro-Veronika ~ % cd ~/oplaty_bot
(base) nikalexa@MacBook-Pro-Veronika oplaty_bot % nano bot.py































































  UW PICO 5.09                                              File: bot.py                                                

import os
import re
from io import BytesIO
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SHEET_URL = os.getenv("SHEET_URL")

PAYMENT_TREE = {
    "pobyt_work_question": {
        "label": "Тимчасове перебування",
        "children": ["ТАК, по роботі", "НІ, не по роботі"]
    },
    "permanent_question": {
        "label": "Постійне перебування",
        "children": ["На підставі карти Поляка", "Без карти Поляка"]
    },
    "card_print_question": {
        "label": "Друк карти побиту",
        "children": ["Карта CUKR", "Karta Pobytu tradycyjna (Nie CUKR)"]
    },
    "traditional_card_question": {
        "label": "Karta Pobytu tradycyjna (Nie CUKR)",
        "children": ["Повнолітня особа без пільг", "Пільгова оплата"]
    }
}

FINAL_PAYMENTS = {
    "ТАК, по роботі": {
        "payment_type_id": "pobyt_praca",
        "label": "Pobyt czasowy i praca",
        "amount": 440,
        "title": "Opłata skarbowa za zezwolenie na pobyt czasowy i pracę dla {full_name}, ur. {birth_date}"
    },
    "НІ, не по роботі": {
        "payment_type_id": "pobyt_czasowy",
        "label": "Pobyt czasowy",
        "amount": 340,
        "title": "Opłata skarbowa za zezwolenie na pobyt czasowy dla {full_name}, ur. {birth_date}"
    },
    "На підставі карти Поляка": {
        "payment_type_id": "pobyt_staly_karta_polaka",
        "label": "Pobyt stały na podstawie Karty Polaka",
        "amount": 0,
        "free": True,
        "title": ""
    },
    "Без карти Поляка": {
        "payment_type_id": "pobyt_staly",
        "label": "Pobyt stały",
        "amount": 640,
        "title": "Opłata skarbowa za zezwolenie na pobyt stały dla {full_name}, ur. {birth_date}"
    },
    "Резидент ЄС": {
        "payment_type_id": "rezydent_ue",

^G Get Help         ^O WriteOut         ^R Read File        ^Y Prev Pg          ^K Cut Text         ^C Cur Pos          
^X Exit             ^J Justify          ^W Where is         ^V Next Pg          ^U UnCut Text       ^T To Spell        
