from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


YES_BTN = InlineKeyboardButton('Да', callback_data='YES')
NO_BTN = InlineKeyboardButton('Нет', callback_data='NO')

recognizing_approving_kb = InlineKeyboardMarkup(2, [[YES_BTN, NO_BTN]])
