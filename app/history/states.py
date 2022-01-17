from aiogram.dispatcher.filters.state import State

from app.core.base_states import BaseStates


class States(BaseStates):
    choosing_plant_adding = State()
    choosing_plant_showing = State()
    adding_photo = State()
