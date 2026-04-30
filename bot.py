import os
import asyncio
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from openai import OpenAI

# =====================
# ENV
# =====================
load_dotenv()

TOKEN = os.getenv("TOKEN")
OPENAI_KEY = os.getenv("OPENAI_KEY")

client = OpenAI(api_key=OPENAI_KEY)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =====================
# DATABASE
# =====================
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    requests INTEGER DEFAULT 0,
    date TEXT,
    paid_until TEXT
)
""")

conn.commit()


def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return cursor.fetchone()


def create_user(user_id, date):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, requests, date, paid_until) VALUES (?, 0, ?, NULL)",
        (user_id, date)
    )
    conn.commit()


def update_requests(user_id, requests):
    cursor.execute(
        "UPDATE users SET requests=? WHERE user_id=?",
        (requests, user_id)
    )
    conn.commit()


def update_payment(user_id, paid_until):
    cursor.execute(
        "UPDATE users SET paid_until=? WHERE user_id=?",
        (paid_until, user_id)
    )
    conn.commit()


# =====================
# SETTINGS
# =====================
FREE_LIMIT = 10
WORD_LIMIT = 50
PRICE_STARS = 39


# =====================
# START
# =====================
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🤖 AI бот\n\n"
        "🆓 Free: 10 запросов/день (до 50 слов)\n"
        f"💎 PRO: {PRICE_STARS} ⭐ / 7 дней\n\n"
        "/buy — купить подписку"
    )


# =====================
# BUY (STARS)
# =====================
@dp.message(Command("buy"))
async def buy(message: types.Message):
    prices = [types.LabeledPrice(label="PRO 7 дней", amount=PRICE_STARS)]

    await bot.send_invoice(
        chat_id=message.chat.id,
        title="PRO подписка",
        description="Безлимитный AI бот на 7 дней",
        payload="pro_sub",
        provider_token="",
        currency="XTR",
        prices=prices
    )


@dp.pre_checkout_query()
async def checkout(q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(q.id, ok=True)


@dp.message(lambda m: m