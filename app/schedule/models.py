from __future__ import annotations

import re

import emoji
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from tortoise import fields

from app.core.base_model import BaseModel, UserModelMixin, ChatModelMixin
from app.history.models import Plant


class Schedule(BaseModel, UserModelMixin, ChatModelMixin):
    period = fields.IntField()
    notification = fields.BooleanField()
    plant = fields.ForeignKeyField('app.Plant', 'schedule',  on_delete=fields.CASCADE)

    class Meta:
        table = 'schedule'

    @property
    def text(self) -> str:
        notification_info = 'Будут приходить уведомления' if self.notification else 'Уведомления приходить не будут'
        return f'Растение: {self.plant.name}, поливать раз в {self.period} дней. {notification_info}'

    @property
    def notification_text(self):
        return f'Время поливать {self.plant.name}'

    @property
    def delete_button(self) -> InlineKeyboardButton:
        callback_data = f':DELETE:{self.id}'
        return InlineKeyboardButton('Удалить', callback_data=callback_data)

    @property
    def switch_button(self) -> InlineKeyboardButton:
        text = 'Отключить уведомления' if self.notification else 'Включить уведомления'
        callback_data = f':SWITCH_NOTIFICATION:{self.id}'
        return InlineKeyboardButton(text, callback_data=callback_data)

    @property
    def check_button(self) -> InlineKeyboardButton:
        text = emoji.emojize('Полит :check_mark:', use_aliases=True)
        callback_data = f':CHECK_WATERING:{self.id}'
        return InlineKeyboardButton(text, callback_data=callback_data)

    @property
    def checked_button(self) -> InlineKeyboardButton:
        text = emoji.emojize('Полит :check_mark_button:')
        callback_data = f':UNCHECK_WATERING:{self.id}'
        return InlineKeyboardButton(text, callback_data=callback_data)

    @staticmethod
    def match_check_query(query: types.CallbackQuery):
        return re.fullmatch(r'^:CHECK_WATERING:[\d]+$', query.data)

    @property
    def edit_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(2, [[self.switch_button, self.delete_button]])

    @staticmethod
    def match_delete_query(query: types.CallbackQuery):
        return re.fullmatch(r'^:DELETE:[\d]+$', query.data)

    @staticmethod
    def match_switch_query(query: types.CallbackQuery):
        return re.fullmatch(r'^:SWITCH_NOTIFICATION:[\d]+$', query.data)

    @staticmethod
    def get_id_from_query(query: types.CallbackQuery):
        return int(query.data.split(':')[-1])

    @property
    def storage_key(self):
        return f'PLANT:{self.id}'

    @property
    def check_watering_keyboard(self):
        return InlineKeyboardMarkup(2, [[self.check_button, self.switch_button]])

    @property
    def checked_watering_keyboard(self):
        return InlineKeyboardMarkup(2, [[self.checked_button, self.switch_button]])


class WateringHistory(BaseModel, UserModelMixin):
    plant = fields.ForeignKeyField('app.Plant', 'watering_history', on_delete=fields.CASCADE)
    datetime = fields.DatetimeField()

    @classmethod
    def get_last(cls, plant: int | Plant):
        plant_id = plant if isinstance(plant, int) else plant.id
        return cls.filter(plant_id=plant_id).order_by('-datetime').first()
