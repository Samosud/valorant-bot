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

RANKS = [
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

SERVERS = [
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
        keyboard=[[KeyboardButton(text=i)] for i in items] + [[KeyboardButton(text="⬅️ Назад")]],
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
    await message.answer("Выбери ранг:", reply_markup=kb_list(RANKS))
    await state.set_state(Register.rank)

@dp.message(Register.rank)
async def reg3(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    await message.answer("Выбери сервер:", reply_markup=kb_list(SERVERS))
    await state.set_state(Register.server)

@dp.message(Register.server)
async def reg4(message: Message, state: FSMContext):
    await state.update_data(server=message.text)
    await state.update_data(agents=[])

    await show_agents(message, state)
    await state.set_state(Register.agents)

# ---------- INLINE АГЕНТЫ (ФИКС) ----------

async def show_agents(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("agents", [])

    keyboard = []

    for a in AGENTS:
        text = f"☑️ {a}" if a in selected else a
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"agent_{a}")])

    keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="done_agents")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await message.answer(
        f"Выбрано: {len(selected)}/3",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

@dp.callback_query(F.data.startswith("agent_"))
async def select_agent(call: CallbackQuery, state: FSMContext):
    agent = call.data.split("_")[1]

    data = await state.get_data()
    selected = data.get("agents", [])

    if agent in selected:
        selected.remove(agent)
    else:
        if len(selected) >= 3:
            await call.answer("❌ Максимум 3")
            return
        selected.append(agent)

    await state.update_data(agents=selected)

    keyboard = []

    for a in AGENTS:
        text = f"☑️ {a}" if a in selected else a
        keyboard.append([InlineKeyboardButton(text=text, callback_data=f"agent_{a}")])

    keyboard.append([InlineKeyboardButton(text="✅ Готово", callback_data="done_agents")])
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])

    await call.message.edit_text(
        f"Выбрано: {len(selected)}/3",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )

    await call.answer()

@dp.callback_query(F.data == "done_agents")
async def done_agents(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    agents = data.get("agents", [])

    if len(agents) != 3:
        await call.answer("❌ Выбери 3 агента")
        return

    await add_user(
        pool,
        call.from_user.id,
        data["nickname"],
        data["rank"],
        data["server"],
        ", ".join(agents)
    )

    await call.message.answer("✅ Регистрация завершена", reply_markup=main_menu)
    await state.clear()
    await call.answer()

# ---------- НАЗАД ----------

@dp.callback_query(F.data == "back")
async def back_inline(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Выбери сервер:", reply_markup=kb_list(SERVERS))
    await state.set_state(Register.server)
    await call.answer()

@dp.message(F.text == "⬅️ Назад")
async def back(message: Message, state: FSMContext):
    current = await state.get_state()

    if current == Register.rank:
        await message.answer("Введите ник:")
        await state.set_state(Register.nickname)

    elif current == Register.server:
        await message.answer("Выбери ранг:", reply_markup=kb_list(RANKS))
        await state.set_state(Register.rank)

    elif current == Register.agents:
        await message.answer("Выбери сервер:", reply_markup=kb_list(SERVERS))
        await state.set_state(Register.server)

    else:
        await state.clear()
        await message.answer("Меню", reply_markup=main_menu)

# ---------- ПРОФИЛЬ ----------

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user = await get_user(pool, message.from_user.id)

    if not user:
        await message.answer("❌ Нет анкеты")
        return

    await message.answer(
        f"{user['nickname']}\n{user['rank']}\n{user['server']}\n{user['agents']}"
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

# ---------- ЗАПУСК ----------

async def main():
    global pool

    threading.Thread(target=run_web).start()

    pool = await create_pool()
    await create_table(pool)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())