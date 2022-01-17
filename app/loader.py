import os
from pytz import UTC
import dotenv

from aiogram import Bot, types, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.consts import TELEGRAM_BOT_API_KEY
from app.redis import Redis

dotenv.load_dotenv()

SHOP_ID = os.environ.get('SHOP_ID')
PAYMENT_KEY = os.environ.get('PAYMENT_KEY')

telegram_key = os.environ.get(TELEGRAM_BOT_API_KEY)
bot = Bot(telegram_key, parse_mode=types.ParseMode.HTML, )
dp = Dispatcher(bot, storage=RedisStorage2())
storage = Redis(db=2)
scheduler = AsyncIOScheduler(timezone=UTC)
