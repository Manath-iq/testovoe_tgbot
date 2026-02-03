import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from app.config import Config
from app.db import create_pool
from app.llm import gemini_query
from app.query_spec import QuerySpec
from app.sql_builder import build_sql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


dp = Dispatcher()


@dp.message()
async def handle_message(message: Message) -> None:
    if not message.text:
        await message.answer("0")
        return

    config: Config = message.bot["config"]
    pool = message.bot["db_pool"]

    try:
        spec_raw = await gemini_query(config.gemini_api_key, config.gemini_model, message.text)
        spec = QuerySpec.model_validate(spec_raw)
        sql_query = build_sql(spec)
        async with pool.acquire() as conn:
            result = await conn.fetchval(sql_query.sql, *sql_query.params)
        await message.answer(str(int(result or 0)))
    except Exception:
        logger.exception("Failed to process message")
        await message.answer("0")


async def main() -> None:
    config = Config()
    bot = Bot(token=config.telegram_token)
    pool = await create_pool(config.database_url)

    bot["config"] = config
    bot["db_pool"] = pool

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
