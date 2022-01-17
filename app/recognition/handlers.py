import io
from typing import Union

import emoji
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentTypes
from PIL import Image

from app.loader import dp, PAYMENT_KEY
from app.recognition.exceptions import RecognitionLimit
from app.recognition.helpers import Recognizer
from app.recognition.markup import recognizing_approving_kb, YES_BTN, NO_BTN
from app.recognition.states import States
from app.start_commands import RECOGNIZE_PLANT
from app.utils.helpers import approving_query_filter, delete_markup


@dp.message_handler(commands=[RECOGNIZE_PLANT], state='*')
async def recognize_plant_command_handler(msg: types.Message, state: FSMContext):
    await Recognizer.check_recognition_count(msg.from_user.id, msg.chat.id)
    await state.set_state(States.recognizing)
    await msg.answer('Отправьте фото растения для опознанния')


@dp.message_handler(state=States.recognizing, content_types=ContentTypes.PHOTO)
async def recognize_plant_handler(msg: types.Message, state: FSMContext):
    await msg.answer(emoji.emojize('Нужно подумать... :hourglass:', use_aliases=True))
    with io.BytesIO() as buffer:
        recognizer = Recognizer(msg, state, buffer)
        image, text = await recognizer.recognize_plant()
        await msg.reply_photo(image, caption=text)
    await send_approving_message(msg, msg.chat.id)
    await state.set_state(States.recognizing_approving)


@dp.callback_query_handler(approving_query_filter, state=States.recognizing_approving)
async def recognize_plant_approving(msg: types.CallbackQuery, state: FSMContext):
    await delete_markup(msg)
    if msg.data == YES_BTN.callback_data:
        await state.finish()
        return await msg.answer('Рад стараться')
    elif msg.data == NO_BTN.callback_data:
        with io.BytesIO() as buffer:
            recognizer = Recognizer(msg, state, buffer)
            image, text = await recognizer.recognize_plant()
            await msg.bot.send_photo(msg.message.chat.id, image, caption=text)
        await send_approving_message(msg, msg.message.chat.id)
        await msg.answer()


async def send_approving_message(msg: Union[types.Message, types.CallbackQuery], chat_id: int):
    await msg.bot.send_message(chat_id, 'Это ваше растение?', reply_markup=recognizing_approving_kb)


@dp.errors_handler(exception=RecognitionLimit)
async def recognition_limit_handler(msg: types.Update, ex: RecognitionLimit):
    await msg.bot.send_message(msg.message.chat.id, 'Лимит привышен')
    await msg.bot.send_invoice(msg.message.chat.id,
                               title='Test',
                               description='Оплата',
                               payload='PAYMENT',
                               provider_token=PAYMENT_KEY,
                               currency='RUB',
                               prices=[types.LabeledPrice('RUB', 7257)])


@dp.pre_checkout_query_handler(lambda query: True, state='*')
async def checkout(pre_checkout_query: types.PreCheckoutQuery):
    await pre_checkout_query.bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                                           error_message="Aliens tried to steal your card's CVV,"
                                                                         " but we successfully protected your credentials,"
                                                                         " try to pay again in a few minutes, we need a small rest.")


@dp.message_handler(content_types=ContentTypes.SUCCESSFUL_PAYMENT, state='*')
async def got_payment(msg: types.Message):
    await msg.bot.send_message(msg.chat.id, 'Платеж принят. Вспользуйтесь командой /recognize_plant, чтобы продолжить!')
    await Recognizer.reset_recognition_count(msg.from_user.id, msg.chat.id)
