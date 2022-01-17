import logging
from asyncio import sleep
from datetime import datetime

import pypika
from aiogram import Dispatcher
from pypika import functions

from app.loader import bot
from pypika import CustomFunction
from tortoise.expressions import F
from tortoise.functions import Function
from tortoise import Tortoise

from pypika import terms

from .models import Schedule
from ..configuration import TORTOISE_ORM
from pypika import CustomFunction

from ..utils.decorators import retry

logger = logging.getLogger('scheduler')


class Extract(Function):
    database_func = functions.Extract

    def _get_function_field(self, field, *args):
        return self.database_func(args[0], field)


@retry(count=3)
async def send_notifications(dp: Dispatcher):
    now = datetime.now()
    to_send = await Schedule.annotate(delta=Extract(now - F('updated_at'), F('days'))) \
        .prefetch_related('plant') \
        .all()
    for entity in to_send:
        if not entity.delta % entity.period == 0:
            continue
        if entity.updated_at.date() == now.date():
            continue
        chat_id = entity.chat_id
        await dp.bot.send_message(chat_id, entity.notification_text, reply_markup=entity.check_watering_keyboard)
        await entity.save()


