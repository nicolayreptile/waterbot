from aiogram.dispatcher.filters.state import StatesGroup, State


class BaseStates(StatesGroup):
    default = State()
