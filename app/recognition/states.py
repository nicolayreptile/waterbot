from aiogram.dispatcher.filters.state import StatesGroup, State

from app.core.base_states import BaseStates


class States(BaseStates):
    recognizing = State()
    recognizing_approving = State()
