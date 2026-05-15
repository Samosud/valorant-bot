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

# очередь поиска
queue = []


# ---------- КНОПКИ ----------

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
async def get_nickname(message: Message, state: FSMContext):
    await state.update_data(nickname=message.text)
    await message.answer("Введите ранг:")
    await state.set_state(Register.rank)


@dp.message(Register.rank)
async def get_rank(message: Message, state: FSMContext):
    await state.update_data(rank=message.text)
    await message.answer("Введите сервер:")
    await state.set_state(Register.server)


@dp.message(Register.server)
async def get_server(message: Message, state: FSMContext):
    await state.update_data(server=message.text)
    await message.answer("Введите агентов:")
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

    await message.answer("✅ Сохранено", reply_markup=main_menu)
    await state.clear()


# ---------- ПРОФИЛЬ ----------

@dp.message(F.text == "👤 Профиль")
async def profile(message: Message):
    user = await get_user(message.from_user.id)

    if not user:
        await message.answer("❌ Нет анкеты")
        return

    await message.answer(
        f"👤 Профиль:\n\n"
        f"🎮 Ник: {user[0]}\n"
        f"🏆 Ранг: {user[1]}\n"
        f"🌍 Сервер: {user[2]}\n"
        f"🧠 Агенты: {user[3]}"
    )


# ---------- РЕДАКТИРОВАНИЕ ----------

@dp.message(F.text == "✏️ Изменить анкету")
async def edit(message: Message, state: FSMContext):
    await delete_user(message.from_user.id)
    await message.answer("Заполни заново:")
    await state.set_state(Register.nickname)


# ---------- ОНЛАЙН ----------

@dp.message(F.text == "🟢 Я онлайн")
async def online(message: Message):
    await set_online(message.from_user.id, 1)
    await message.answer("🟢 Ты онлайн")


@dp.message(F.text == "🔴 Я оффлайн")
async def offline(message: Message):
    await set_online(message.from_user.id, 0)
    await message.answer("🔴 Ты оффлайн")


# ---------- ПОИСК ----------

@dp.message(F.text == "🎯 Найти тиммейтов")
async def find(message: Message):
    users = await get_online_users()

    if not users:
        await message.answer("❌ Никого нет онлайн")
        return

    text = "🎯 Игроки:\n\n"

    for user in users:
        text += (
            f"{user[0]} | {user[1]} | {user[2]}\n"
        )

    await message.answer(text)


# ---------- БЫСТРЫЙ ПОИСК ----------

@dp.message(F.text == "⚡ Быстрый поиск")
async def quick_search(message: Message):
    user_id = message.from_user.id

    if user_id in queue:
        await message.answer("⏳ Уже ищем")
        return

    queue.append(user_id)
    await message.answer("🔍 Поиск...")

    if len(queue) >= 2:
        u1 = queue.pop(0)
        u2 = queue.pop(0)

        await bot.send_message(u1, "🎉 Нашёл тиммейта!")
        await bot.send_message(u2, "🎉 Нашёл тиммейта!")


# ---------- ЗАПУСК ----------

async def main():
    await create_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())