import asyncio
import os
import threading

from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import *

TOKEN = "8811805904:AAH96u6i1ak0Ms3hJm4UHaa2h6E67n7H0aw"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
pool = None

# ---------- WEB ----------
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ---------- ДАННЫЕ ----------
RANKS = ["Неважно",
    "🪨 Железо 1","🪨 Железо 2","🪨 Железо 3",
    "🥉 Бронза 1","🥉 Бронза 2","🥉 Бронза 3",
    "🥈 Серебро 1","🥈 Серебро 2","🥈 Серебро 3",
    "🥇 Золото 1","🥇 Золото 2","🥇 Золото 3",
    "💎 Платина 1","💎 Платина 2","💎 Платина 3",
    "🔷 Алмаз 1","🔷 Алмаз 2","🔷 Алмаз 3",
    "🟣 Аскендант 1","🟣 Аскендант 2","🟣 Аскендант 3",
    "🔥 Иммортал 1","🔥 Иммортал 2","🔥 Иммортал 3",
    "🌟 Radiant"
]

SERVERS = ["Неважно",
    "Франкфурт","Париж","Лондон","Мадрид",
    "Стокгольм","Варшава","Стамбул"
]

AGENTS = [
    "Jett","Phoenix","Raze","Reyna","Yoru","Neon","Iso","Waylay",
    "Brimstone","Viper","Omen","Astra","Harbor","Clove","Miks",
    "Sova","Breach","Skye","KAY/O","Fade","Gekko","Tejo",
    "Sage","Cypher","Killjoy","Chamber","Deadlock","Vyse","Veto"
]

# ---------- КНОПКИ ----------

def kb_list(items):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=i)] for i in items],
        resize_keyboard=True
    )

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Регистрация")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🟢 Онлайн"), KeyboardButton(text="🔴 Оффлайн")],
        [KeyboardButton(text="🔍 Поиск")]
    ],
    resize_keyboard=True
)

# ---------- FSM ----------

class Register(StatesGroup):
    nickname = State()
    rank = State()
    server = State()
    agents = State()

# ---------- START ----------

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🎮 Добро пожаловать", reply_markup=main_menu)

# ---------- РЕГИСТРАЦИЯ ----------

@dp.message(F.text == "📝 Регистрация")
async def reg(message: Message, state: FSMContext):
    await message.answer("Введите ник:")
    await state.set_state(Register.nickname)

@dp.message(Register.nickname)
async def reg2(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer("Выбери ранг:", reply_markup=kb_list(RANKS[1:]))
    await state.set_state(Register.rank)

@dp.message(Register.rank)
async def reg3(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    await message.answer("Выбери сервер:", reply_markup=kb_list(SERVERS[1:]))
    await state.set_state(Register.server)

@dp.message(Register.server)
async def reg4(message: Message, state: FSMContext):
    await state.update_data(server=message.text)
    await state.update_data(agents=[])
    await message.answer("Выбери 3 агента (по одному):")
    await state.set_state(Register.agents)

@dp.message(Register.agents)
async def reg5(message: Message, state: FSMContext):
    data = await state.get_data()
    agents = data.get("agents", [])

    if message.text not in AGENTS:
        await message.answer("❌ Выбери из списка")
        return

    if message.text in agents:
        await message.answer("⚠️ Уже выбрал")
        return

    agents.append(message.text)
    await state.update_data(agents=agents)

    if len(agents) < 3:
        await message.answer(f"{len(agents)}/3 выбрано")
    else:
        data = await state.get_data()

        await add_user(
            pool,
            message.from_user.id,
            data["nickname"],
            data["rank"],
            data["server"],
            ", ".join(agents)
        )

        await message.answer("✅ Готово", reply_markup=main_menu)
        await state.clear()

# ---------- ПРОФИЛЬ ----------

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user = await get_user(pool, message.from_user.id)

    if not user:
        await message.answer("❌ Нет анкеты")
        return

    await message.answer(
        f"🎮 {user['nickname']}\n"
        f"{user['rank']}\n"
        f"{user['server']}\n"
        f"{user['agents']}"
    )

# ---------- ОНЛАЙН ----------

@dp.message(F.text == "🟢 Онлайн")
async def online(message: Message):
    await set_online(pool, message.from_user.id, True)
    await message.answer("🟢 Ты онлайн")

@dp.message(F.text == "🔴 Оффлайн")
async def offline(message: Message):
    await set_online(pool, message.from_user.id, False)
    await message.answer("🔴 Ты оффлайн")

# ---------- ПОИСК ----------

@dp.message(F.text == "🔍 Поиск")
async def find(message: Message):
    users = await get_online_users(pool)

    if not users:
        await message.answer("❌ Никого нет")
        return

    for u in users:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="✉️ Заявка",
                callback_data=f"invite_{u['telegram_id']}"
            )]
        ])

        await message.answer(
            f"{u['nickname']}\n{u['rank']}\n{u['server']}",
            reply_markup=kb
        )

# ---------- ЗАЯВКИ ----------

@dp.callback_query(F.data.startswith("invite_"))
async def invite(call: CallbackQuery):
    target = int(call.data.split("_")[1])

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"acc_{call.from_user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="decline")
        ]
    ])

    await bot.send_message(target, "📩 Заявка!", reply_markup=kb)
    await call.answer("Отправлено")

@dp.callback_query(F.data.startswith("acc_"))
async def accept(call: CallbackQuery):
    uid = int(call.data.split("_")[1])

    await bot.send_message(call.from_user.id, f"tg://user?id={uid}")
    await bot.send_message(uid, f"tg://user?id={call.from_user.id}")

# ---------- ЗАПУСК ----------

async def main():
    global pool

    threading.Thread(target=run_web).start()

    pool = await create_pool()
    await create_table(pool)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())