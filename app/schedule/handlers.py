import datetime
import re

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentTypes
from contextlib import suppress

from aiogram.utils.exceptions import MessageCantBeEdited, \
    MessageToEditNotFound
from aiogram.utils.markdown import hstrikethrough
from tortoise.functions import Max

from app.loader import dp, storage
from app.start_commands import NEW_SCHEDULE, LIST_SCHEDULE, LIST_WATERING
from .markup import Y_BUTTON, N_BUTTON, Y_N_KB
from app.schedule.models import Schedule, WateringHistory
from app.schedule.states import States
from app.utils.helpers import delete_markup
from app.history.markup import get_plants_keyboard
from app.history.models import Plant


@dp.message_handler(commands=[NEW_SCHEDULE], state='*')
async def watering_schedule_command_handler(msg: types.Message, state: FSMContext):
    await state.set_state(States.setting_name)
    plants = await Plant.filter_by_user(msg.from_user.id)

    if plants:
        keyboard = get_plants_keyboard(plants)
        answer = await msg.answer('Выберите растение или введите название', reply_markup=keyboard)
        await state.update_data({'message_id': answer.message_id})
    else:
        await msg.answer('Введите название растения')


@dp.message_handler(commands=[LIST_SCHEDULE], state='*')
async def watering_schedule_list(msg: types.Message, state: FSMContext):
    schedules = await Schedule.filter(user_id=msg.from_user.id, chat_id=msg.chat.id) \
        .order_by('updated_at') \
        .prefetch_related('plant')
    for schedule in schedules:
        await msg.bot.send_message(msg.chat.id, schedule.text, reply_markup=schedule.edit_keyboard)


@dp.callback_query_handler(Schedule.match_delete_query, state='*')
async def delete_schedule(msg: types.CallbackQuery, state: FSMContext):
    schedule_id = Schedule.get_id_from_query(msg)
    await Schedule.filter(id=schedule_id).delete()
    text = hstrikethrough(msg.message.text)
    await msg.message.edit_text(f'{text}. Удалено.')
    await msg.answer('Расписание удалено')


@dp.message_handler(state=States.setting_name)
async def watering_schedule_getting_name(msg: types.Message, state: FSMContext):
    plant = await Plant.create(name=msg.text, chat_id=msg.chat.id, user_id=msg.from_user.id)
    await state.update_data({'plant_id': plant.id})
    await delete_markup(msg, state)
    await state.set_state(States.setting_period)
    await msg.answer('Введите период полива в днях')


@dp.callback_query_handler(Plant.query_filter, state=States.setting_name)
async def watering_schedule_getting_name_query_handler(msg: types.CallbackQuery, state: FSMContext):
    plant_id = Plant.get_plant_id_from_query(msg)
    plant = await Plant.get(id=plant_id)
    await state.update_data({'plant_id': plant.id})
    await delete_markup(msg)
    await state.set_state(States.setting_period)
    await msg.bot.send_message(msg.message.chat.id, 'Введите период полива в днях')


@dp.message_handler(state=States.setting_period, content_types=ContentTypes.TEXT)
async def watering_schedule_getting_period(msg: types.Message, state: FSMContext):
    try:
        period = int(msg.text)
    except ValueError:
        return await msg.answer('Допустимо вводить только число')

    await state.set_state(States.setting_notification)
    await msg.answer('Необходимо присылать уведомления?', reply_markup=Y_N_KB)
    await state.update_data({'period': period})


@dp.callback_query_handler(lambda q: q.data in (Y_BUTTON.callback_data, N_BUTTON.callback_data),
                           state=States.setting_notification)
async def watering_schedule_getting_notification(msg: types.CallbackQuery, state: FSMContext):
    schedule = await save_schedule(msg, state)

    await delete_markup(msg)
    await delete_markup(msg, state)

    await msg.answer('Расписание создано!')
    await msg.bot.send_message(msg.message.chat.id, schedule.text)

    await state.finish()


@dp.callback_query_handler(Schedule.match_switch_query, state='*')
async def switch_notifications(msg: types.CallbackQuery, state: FSMContext):
    schedule_id = Schedule.get_id_from_query(msg)
    schedule = await Schedule.get(id=schedule_id)
    schedule.notification = not schedule.notification
    await schedule.save()
    await msg.bot.edit_message_reply_markup(msg.message.chat.id, msg.message.message_id,
                                            reply_markup=schedule.edit_keyboard)
    await msg.answer(f'Уведомления {"включены" if schedule.notification else "отключены"}')


@dp.callback_query_handler(Schedule.match_check_query, state='*')
async def check_watering(msg: types.CallbackQuery, state: FSMContext):
    schedule_id = Schedule.get_id_from_query(msg)
    schedule = await Schedule.get(id=schedule_id).prefetch_related('plant')
    await WateringHistory.create(plant_id=schedule.plant.id, user_id=msg.from_user.id, datetime=datetime.datetime.now())
    await msg.bot.edit_message_reply_markup(msg.message.chat.id, msg.message.message_id,
                                            reply_markup=schedule.checked_watering_keyboard)
    await msg.answer()


@dp.message_handler(commands=[LIST_WATERING], state='*')
async def watering_history(msg: types.Message, state: FSMContext):
    plants = await WateringHistory \
        .filter_by_user(msg.from_user.id) \
        .select_related('plant') \
        .annotate(last_watering=Max('datetime')) \
        .group_by('plant_id', 'plant__name') \
        .values('plant__name', 'last_watering')
    text = '\n'.join(['{}: {}'.format(p['plant__name'], p['last_watering'].strftime('%d.%m.%Y %H:%M')) for p in plants])
    await msg.bot.send_message(msg.chat.id, f'Последние поливы: \n{text}')


async def save_schedule(msg: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    enable_notifications = True if msg.data == Y_BUTTON.callback_data else False
    plant = await Plant.get(id=data.pop('plant_id'))
    data.update({
        'notification': enable_notifications,
        'user_id': msg.from_user.id,
        'chat_id': msg.message.chat.id,
        'plant': plant
    })
    data = dict(filter(lambda x: x[0] in Schedule._meta.fields, data.items()))
    return await Schedule.create(**data)
