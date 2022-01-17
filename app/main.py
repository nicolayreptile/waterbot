import asyncio
import logging

from tortoise import Tortoise

from app.configuration import TORTOISE_ORM
from app.discovery import import_modules
from app.loader import bot, dp, scheduler
from app.schedule.jobs import send_notifications
from app.start_commands import register_commands

logger = logging.getLogger(__name__)

TORTOISE_ORM = TORTOISE_ORM


async def init_app():
    await Tortoise.init(TORTOISE_ORM)
    logger.info("Tortoise-ORM started, %s, %s", Tortoise._connections, Tortoise.apps)
    await import_modules('handlers')
    await register_commands(bot)


async def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    await init_app()

    try:
        await asyncio.gather(
            dp.start_polling()
        )

    finally:
        logger.info('App stopping')
        dp.stop_polling()
        await dp.storage.close()
        await dp.wait_closed()
        await bot.session.close()
        await Tortoise.close_connections()


def schedule_jobs():
    scheduler.add_job(send_notifications, 'cron', hour=10, args=[dp])
    scheduler.start()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        schedule_jobs()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.stop()
