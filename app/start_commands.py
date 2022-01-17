from aiogram import Bot
from aiogram.types import BotCommand, ReplyKeyboardMarkup, KeyboardButton

RECOGNIZE_PLANT = 'recognize_plant'
LIST_WATERING = 'list_watering'
NEW_SCHEDULE = 'new_schedule'
LIST_SCHEDULE = 'list_schedule'
NEW_HISTORY_PHOTO = 'new_history_photo'
SHOW_HISTORY_PHOTOS = 'show_history_photos'


async def register_commands(bot: Bot):
    commands = [
        BotCommand(RECOGNIZE_PLANT, 'Опознать растение'),
        BotCommand(LIST_WATERING, 'Показать последний полив'),
        BotCommand(NEW_SCHEDULE, 'Добавить расписание полива'),
        BotCommand(LIST_SCHEDULE, 'Настроенное расписание'),
        BotCommand(NEW_HISTORY_PHOTO, 'Запечатлить растение'),
        BotCommand(SHOW_HISTORY_PHOTOS, 'Посмотреть историю растения')
    ]
    return await bot.set_my_commands(commands)
