from aiogram.dispatcher.filters.state import State

from app.core.base_states import BaseStates


class States(BaseStates):
    setting_schedule_start = State()
    setting_name = State()
    setting_period = State()
    setting_notification = State()
