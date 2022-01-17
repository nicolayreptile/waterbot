import io
import aioredis
from typing import Union
from PIL import Image
from aiogram import types
from aiogram.dispatcher import FSMContext

from app.clients.clients import PlantNetClient
from app.consts import USER_RECOGNITION_LIMIT, EXPIRE_LIMIT_TIME
from app.loader import storage
from app.recognition.exceptions import RecognitionLimit


class Recognizer:
    __client = PlantNetClient
    RECOGNITION_COUNT_KEY = 'recognition_count'

    def __init__(self, msg: Union[types.Message, types.CallbackQuery], state: FSMContext, buffer: io.BytesIO):
        self.msg = msg
        self.state = state
        self.buffer = buffer
        self.client = self.__client()

    @classmethod
    async def set_user_recognition_count(cls, user_id: int, chat_id: int, value: int):
        await storage.set(user_id, chat_id, cls.RECOGNITION_COUNT_KEY, value, EXPIRE_LIMIT_TIME)

    @classmethod
    async def get_user_recognition_count(cls, user_id: int, chat_id: int):
        return await storage.get(user_id, chat_id, cls.RECOGNITION_COUNT_KEY)

    @classmethod
    async def check_recognition_count(cls, user_id: int, chat_id: int):
        count = await cls.get_user_recognition_count(user_id, chat_id)
        if count is None:
            return await cls.set_user_recognition_count(user_id, chat_id, 0)
        if count > USER_RECOGNITION_LIMIT:
            raise RecognitionLimit()

    @classmethod
    async def update_recognition_count(cls, user_id: int, chat_id: int):
        count = await cls.get_user_recognition_count(user_id, chat_id)
        await cls.set_user_recognition_count(user_id, chat_id, count + 1)

    @classmethod
    async def reset_recognition_count(cls, user_id: int, chat_id: int):
        await cls.set_user_recognition_count(user_id, chat_id, 0)

    async def recognize_plant(self) -> Union[tuple[bytes, str], None]:
        if isinstance(self.msg, types.Message):
            response, index = await self.request_recognition()
            await self.save_context(response)
        elif isinstance(self.msg, types.CallbackQuery):
            data = await self.state.get_data()
            index = data['index'] + 1
            await self.state.update_data({'index': index})
            response, index = data['response'], index
        else:
            raise ValueError
        try:
            return await self.client.parse_response(response, self.buffer, index)
        except IndexError:
            return None

    async def get_buffered_image_from_message(self) -> Image:
        await self.msg.photo[-1].download(self.buffer)
        self.buffer.seek(0)
        return self.buffer

    async def request_recognition(self):
        await self.msg.photo[-1].download(self.buffer)
        self.buffer.seek(0)
        response = await self.client.send_recognize_request(self.buffer)
        return response, 0

    async def save_context(self, response: dict, index: int = 0):
        context_data = {
            'index': index,
            'response': response
        }
        await self.state.update_data(context_data)
