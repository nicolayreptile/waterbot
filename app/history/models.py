import re

from PIL import Image
from aiogram import types
from tortoise import fields

from app.configuration import MEDIA_URL
from app.core.base_model import BaseModel, UserModelMixin, ChatModelMixin
from app.history.fields import ImageField


class Plant(BaseModel, UserModelMixin, ChatModelMixin):
    name = fields.TextField()

    callback_data_pattern = r'^PLANT:[\d]+$'
    callback_data_format = '{}:{}'

    class Meta:
        table = 'plant'

    @staticmethod
    def query_filter(query: types.CallbackQuery) -> bool:
        return re.match(Plant.callback_data_pattern, query.data) is not None

    @staticmethod
    def get_plant_id_from_query(query: types.CallbackQuery) -> int:
        plant_id = re.findall(r'[\d]+$', query.data)[0]
        return int(plant_id)


class PlantHistory(BaseModel, UserModelMixin, ChatModelMixin):
    plant = fields.ForeignKeyField('app.Plant', 'history')
    image = ImageField()

    class Meta:
        table = 'planthistory'

    def get_image(self):
        path = f'{MEDIA_URL}/{self.user_id}/{self.image}'
        return Image.open(path)
