from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


Y_BUTTON = InlineKeyboardButton('Да', callback_data=':YES')
N_BUTTON = InlineKeyboardButton('Нет', callback_data=':NO')

Y_N_KB = InlineKeyboardMarkup(row_width=2, inline_keyboard=[[Y_BUTTON, N_BUTTON]])
