import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from database import *

TOKEN = "8811805904:AAHdxtHRwTZX3jfWm8oiiFhxT_SGADpozNo"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------- КНОПКИ ----------

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Регистрация")],
        [KeyboardButton(text="🟢 Я онлайн"),
         KeyboardButton(text="🔴 Я оффлайн")],
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
    await message.answer(
        "🎮 Добро пожаловать в Valorant Team Finder!\n\n"
        "Находи тиммейтов для Valorant 🔥",
        reply_markup=main_menu
    )


# ---------- РЕГИСТРАЦИЯ ----------

@dp.message(F.text == "📝 Регистрация")
async def register_start(message: Message, state: FSMContext):
    await message.answer("🎮 Введите Riot nickname:")
    await state.set_state(Register.nickname)


@dp.message(Register.nickname)
async def get_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)

    await message.answer("🏆 Введите ваш ранг:")
    await state.set_state(Register.rank)


@dp.message(Register.rank)
async def get_rank(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)

    await message.answer("🌍 Введите сервер:")
    await state.set_state(Register.server)


@dp.message(Register.server)
async def get_server(message: Message, state: FSMContext):
    await state.update_data(server=message.text)

    await message.answer("🧠 Введите основных агентов:")
    await state.set_state(Register.agents)


@dp.message(Register.agents)
async def get_agents(message: Message, state: FSMContext):
    await state.update_data(agents=message.text)

    data = await state.get_data()

    await add_user(
        message.from_user.id,
        data["nickname"],
        data["rank"],
        data["server"],
        data["agents"]
    )

    await message.answer(
        "✅ Анкета успешно сохранена!",
        reply_markup=main_menu
    )

    await state.clear()


# ---------- ОНЛАЙН ----------

@dp.message(F.text == "🟢 Я онлайн")
async def online(message: Message):
    await set_online(message.from_user.id, 1)

    await message.answer("🟢 Теперь ты онлайн")


# ---------- ОФФЛАЙН ----------

@dp.message(F.text == "🔴 Я оффлайн")
async def offline(message: Message):
    await set_online(message.from_user.id, 0)

    await message.answer("🔴 Теперь ты оффлайн")


# ---------- ПОИСК ----------

@dp.message(F.text == "🎯 Найти тиммейтов")
async def find(message: Message):
    users = await get_online_users()

    if not users:
        await message.answer("❌ Сейчас нет игроков онлайн")
        return

    text = "🎯 Игроки онлайн:\n\n"

    for user in users:
        text += (
            f"🎮 Ник: {user[0]}\n"
            f"🏆 Ранг: {user[1]}\n"
            f"🌍 Сервер: {user[2]}\n"
            f"🧠 Агенты: {user[3]}\n\n"
        )

    await message.answer(text)


# ---------- ЗАПУСК ----------

async def main():
    await create_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())