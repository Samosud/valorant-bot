import asyncio
import os
import threading

from flask import Flask

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import *

# ---------- НАСТРОЙКИ ----------

TOKEN = "8811805904:AAH96u6i1ak0Ms3hJm4UHaa2h6E67n7H0aw"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

pool = None

queue = []
matches = {}
accepted = {}

# ---------- WEB (для Render) ----------

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ---------- МЕНЮ ----------

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Регистрация")],
        [KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="✏️ Изменить анкету")],
        [KeyboardButton(text="🟢 Я онлайн"), KeyboardButton(text="🔴 Я оффлайн")],
        [KeyboardButton(text="⚡ Быстрый поиск")],
        [KeyboardButton(text="🎯 Найти тиммейтов")],
    ],
    resize_keyboard=True
)


# ---------- СОСТОЯНИЯ ----------

class Register(StatesGroup):
    nickname = State()
    rank = State()
    server = State()
    agents = State()


# ---------- START ----------

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("🎮 Добро пожаловать!", reply_markup=main_menu)


# ---------- РЕГИСТРАЦИЯ ----------

@dp.message(F.text == "📝 Регистрация")
async def register_start(message: Message, state: FSMContext):
    await message.answer("Введите ник:")
    await state.set_state(Register.nickname)


@dp.message(Register.nickname)
async def step1(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer("Введите ранг:")
    await state.set_state(Register.rank)


@dp.message(Register.rank)
async def step2(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    await message.answer("Введите сервер:")
    await state.set_state(Register.server)


@dp.message(Register.server)
async def step3(message: Message, state: FSMContext):
    await state.update_data(server=message.text)
    await message.answer("Введите агентов:")
    await state.set_state(Register.agents)


@dp.message(Register.agents)
async def step4(message: Message, state: FSMContext):
    await state.update_data(agents=message.text)
    data = await state.get_data()

    await add_user(
        pool,
        message.from_user.id,
        data["nickname"],
        data["rank"],
        data["server"],
        data["agents"]
    )

    await message.answer("✅ Сохранено", reply_markup=main_menu)
    await state.clear()


# ---------- ПРОФИЛЬ ----------

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user = await get_user(pool, message.from_user.id)

    if not user:
        await message.answer("❌ Нет анкеты")
        return

    await message.answer(
        f"👤 Профиль:\n\n"
        f"🎮 {user['nickname']}\n"
        f"🏆 {user['rank']}\n"
        f"🌍 {user['server']}\n"
        f"🧠 {user['agents']}"
    )


# ---------- ОНЛАЙН ----------

@dp.message(F.text == "🟢 Я онлайн")
async def online(message: Message):
    await set_online(pool, message.from_user.id, True)
    await message.answer("🟢 Ты онлайн")


@dp.message(F.text == "🔴 Я оффлайн")
async def offline(message: Message):
    await set_online(pool, message.from_user.id, False)
    await message.answer("🔴 Ты оффлайн")


# ---------- СПИСОК ----------

@dp.message(F.text == "🎯 Найти тиммейтов")
async def find(message: Message):
    users = await get_online_users(pool)

    if not users:
        await message.answer("❌ Никого нет")
        return

    text = "🎯 Онлайн:\n\n"
    for u in users:
        text += f"{u['nickname']} | {u['rank']} | {u['server']}\n"

    await message.answer(text)


# ---------- ПОИСК ----------

@dp.message(F.text == "⚡ Быстрый поиск")
async def quick_search(message: Message):
    uid = message.from_user.id

    if uid in queue:
        await message.answer("⏳ Уже ищем")
        return

    queue.append(uid)
    await message.answer("🔍 Поиск...")

    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        matches[u1] = u2
        matches[u2] = u1

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data="accept"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data="decline")
            ]
        ])

        await bot.send_message(u1, "🎯 Найден тиммейт!", reply_markup=kb)
        await bot.send_message(u2, "🎯 Найден тиммейт!", reply_markup=kb)


# ---------- КНОПКИ ----------

@dp.callback_query(F.data == "accept")
async def accept(call: CallbackQuery):
    user = call.from_user.id
    partner = matches.get(user)

    if not partner:
        return

    accepted[user] = True

    if accepted.get(partner):
        await bot.send_message(user, f"🎉 Матч! Написать: tg://user?id={partner}")
        await bot.send_message(partner, f"🎉 Матч! Написать: tg://user?id={user}")

        matches.pop(user, None)
        matches.pop(partner, None)
        accepted.pop(user, None)
        accepted.pop(partner, None)
    else:
        await call.message.answer("⏳ Ждём второго игрока...")


@dp.callback_query(F.data == "decline")
async def decline(call: CallbackQuery):
    user = call.from_user.id
    partner = matches.get(user)

    if partner:
        await bot.send_message(partner, "❌ Игрок отказался")

    matches.pop(user, None)
    accepted.pop(user, None)

    await call.message.answer("❌ Ты отказался")


# ---------- ЗАПУСК ----------

async def main():
    global pool

    # веб (для Render)
    threading.Thread(target=run_web).start()

    pool = await create_pool()
    await create_table(pool)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())