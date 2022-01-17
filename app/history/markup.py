from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.history.models import Plant

KB_LEN = 3  # buttons count in row
BTN_CALLBACK_DATA = 'PLANT'


def get_plants_keyboard(plants: list[Plant]) -> InlineKeyboardMarkup:
    total_items = len(plants)
    buttons = []
    for i in range(0, total_items, KB_LEN):
        row = plants[i:i+KB_LEN] if i + KB_LEN < total_items else plants[i:]
        buttons.append([get_button(plant) for plant in row])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_button(plant: Plant):
    callback_data = Plant.callback_data_format.format(BTN_CALLBACK_DATA, plant.id)
    return InlineKeyboardButton(text=plant.name, callback_data=callback_data)
