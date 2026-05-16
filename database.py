import asyncpg
import os

DB_URL = os.getenv("DATABASE_URL")


async def create_pool():
    return await asyncpg.create_pool(DB_URL)


async def create_table(pool):
    async with pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id BIGINT PRIMARY KEY,
            nickname TEXT,
            rank TEXT,
            server TEXT,
            agents TEXT,
            online BOOLEAN DEFAULT FALSE
        )
        """)


async def add_user(pool, telegram_id, nickname, rank, server, agents):
    async with pool.acquire() as conn:
        await conn.execute("""
        INSERT INTO users (telegram_id, nickname, rank, server, agents)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (telegram_id)
        DO UPDATE SET
            nickname = EXCLUDED.nickname,
            rank = EXCLUDED.rank,
            server = EXCLUDED.server,
            agents = EXCLUDED.agents
        """, telegram_id, nickname, rank, server, agents)


async def get_user(pool, telegram_id):
    async with pool.acquire() as conn:
        return await conn.fetchrow("""
        SELECT * FROM users WHERE telegram_id = $1
        """, telegram_id)


async def set_online(pool, telegram_id, status):
    async with pool.acquire() as conn:
        await conn.execute("""
        UPDATE users SET online = $1 WHERE telegram_id = $2
        """, status, telegram_id)


async def get_online_users(pool):
    async with pool.acquire() as conn:
        return await conn.fetch("""
        SELECT nickname, rank, server FROM users WHERE online = TRUE
        """)


async def delete_user(pool, telegram_id):
    async with pool.acquire() as conn:
        await conn.execute("""
        DELETE FROM users WHERE telegram_id = $1
        """, telegram_id)