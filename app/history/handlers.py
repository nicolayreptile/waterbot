import io
import os.path
import re
from contextlib import suppress
from datetime import datetime
from typing import Union

from PIL import Image, ImageFont
from PIL import ImageDraw
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentTypes
from tortoise.functions import Count

from app.configuration import MEDIA_URL
from app.history.markup import get_plants_keyboard
from app.history.states import States
from app.history.models import Plant, PlantHistory
from app.loader import dp
from app.start_commands import NEW_HISTORY_PHOTO, SHOW_HISTORY_PHOTOS
from app.utils.helpers import delete_markup

AnyMessage = Union[types.Message, types.CallbackQuery]


@dp.message_handler(commands=[NEW_HISTORY_PHOTO], state='*')
async def adding_history_command_handler(msg: types.Message, state: FSMContext):
    await state.set_state(States.choosing_plant_adding)
    plants = await Plant.filter_by_user(msg.from_user.id)
    keyboard = get_plants_keyboard(plants)
    if keyboard:
        answer = await msg.answer('Выберите растение или введите название', reply_markup=keyboard)
        await state.update_data({'message_id': answer.message_id})
    else:
        await msg.answer('Введите название растения')


@dp.message_handler(commands=[SHOW_HISTORY_PHOTOS], state='*')
async def show_history_command_handler(msg: types.Message, state: FSMContext):
    plants = await Plant.annotate(history_count=Count('history')) \
        .filter(user_id=msg.from_user.id, history_count__gt=0) \
        .all()
    keyboard = get_plants_keyboard(plants)
    if keyboard:
        await state.set_state(States.choosing_plant_showing)
        await msg.answer('Выберите растение', reply_markup=keyboard)
    else:
        await msg.answer('Вы пока не добавили ни одной истории')


@dp.callback_query_handler(Plant.query_filter, state=States.choosing_plant_showing)
async def show_history_query_handler(msg: types.CallbackQuery, state: FSMContext):
    await delete_markup(msg)
    await state.finish()
    plant_id = Plant.get_plant_id_from_query(msg)
    plants_history = await PlantHistory.filter(plant=plant_id)
    plants_history = [(plant.get_image(), plant.created_at) for plant in plants_history]
    width, height = 640, 640 * len(plants_history)
    collage = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(collage)
    font = ImageFont.truetype("FreeMono.ttf", 46)
    for i, plant in enumerate(plants_history):
        img, dt = plant
        img.thumbnail((640, 640))
        collage.paste(img, (0, i * 640))
        draw.text((10, i * 640), dt.strftime('%d.%m.%Y %H:%M'), font=font, fill=(0, 0, 0, 128))
    with io.BytesIO() as buffer:
        collage.save(buffer, format='JPEG')
        buffer.seek(0)
        await msg.bot.send_photo(msg.message.chat.id, buffer)
    await msg.answer()


@dp.callback_query_handler(Plant.query_filter, state=States.choosing_plant_adding)
async def choose_plant(msg: types.CallbackQuery, state: FSMContext):
    plant_id = Plant.get_plant_id_from_query(msg)
    plant = await Plant.get(id=plant_id)
    await sent_photo_request_msg(msg, state, plant)


@dp.message_handler(state=States.choosing_plant_adding, content_types=ContentTypes.TEXT)
async def new_plant(msg: types.Message, state: FSMContext):
    name, user_id, chat_id = msg.text, msg.from_user.id, msg.chat.id
    plant = await Plant.create(name=name, user_id=user_id, chat_id=chat_id)
    await sent_photo_request_msg(msg, state, plant)


async def sent_photo_request_msg(msg: AnyMessage, state: FSMContext, plant: Plant):
    await state.update_data({'plant_id': plant.id})
    await state.set_state(States.adding_photo)
    text = f'Теперь загрузите или сделайте фото для растения {plant.name}'
    if isinstance(msg, types.Message):
        await msg.answer(text)
    elif isinstance(msg, types.CallbackQuery):
        await msg.bot.send_message(msg.message.chat.id, text)
    await delete_markup(msg, state)


@dp.message_handler(state=States.adding_photo, content_types=ContentTypes.PHOTO)
async def add_photo(msg: types.Message, state: FSMContext):
    photo = await save_image(msg)
    data = await state.get_data()
    await state.finish()
    plant = await Plant.get(id=data['plant_id'])
    await PlantHistory.create(plant=plant, image=photo, user_id=msg.from_user.id, chat_id=msg.chat.id)
    await msg.bot.delete_message(msg.chat.id, msg.message_id)
    await msg.answer('Фото сохранено в историю')


async def save_image(msg: types.Message) -> str:
    timestamp = datetime.now().timestamp()
    dir_path = get_user_directory(msg.from_user.id)

    with io.BytesIO() as buffer:
        await msg.photo[-1].download(buffer)
        image = Image.open(buffer)
        filename = f'{timestamp}_ph.{image.format}'
        image.save(dir_path / filename, format='JPEG')
    return filename


def get_user_directory(user_id: int):
    path = MEDIA_URL / str(user_id)
    if not os.path.exists(path):
        os.mkdir(path)
    return path
