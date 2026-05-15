import aiosqlite

DB_NAME = "database.db"


async def create_table():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER,
            nickname TEXT,
            rank TEXT,
            server TEXT,
            agents TEXT,
            online INTEGER DEFAULT 0
        )
        """)
        await db.commit()


async def add_user(telegram_id, nickname, rank, server, agents):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        INSERT INTO users
        (telegram_id, nickname, rank, server, agents)
        VALUES (?, ?, ?, ?, ?)
        """, (telegram_id, nickname, rank, server, agents))
        await db.commit()


async def get_user(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT nickname, rank, server, agents
        FROM users
        WHERE telegram_id = ?
        """, (telegram_id,))
        return await cursor.fetchone()


async def get_online_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("""
        SELECT nickname, rank, server, agents
        FROM users
        WHERE online = 1
        """)
        return await cursor.fetchall()


async def set_online(telegram_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        UPDATE users
        SET online = ?
        WHERE telegram_id = ?
        """, (status, telegram_id))
        await db.commit()


async def delete_user(telegram_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        DELETE FROM users WHERE telegram_id = ?
        """, (telegram_id,))
        await db.commit()