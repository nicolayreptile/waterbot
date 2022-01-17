from contextlib import suppress
from typing import Union, Optional
import io

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageCantBeEdited, MessageNotModified, MessageToEditNotFound

from app.recognition.markup import YES_BTN, NO_BTN


def ignore_exceptions(func):
    async def wrapped(*args, **kwargs):
        with suppress(MessageCantBeEdited, MessageNotModified, MessageToEditNotFound):
            return await func(*args, **kwargs)
    return wrapped


@ignore_exceptions
async def delete_markup(msg: Union[types.Message, types.CallbackQuery], state: Optional[FSMContext] = None):
    if isinstance(msg, types.Message) and state:
        data = await state.get_data()
        await msg.bot.delete_message(msg.chat.id, data['message_id'])
    elif isinstance(msg, types.CallbackQuery):
        await msg.message.delete_reply_markup()


def approving_query_filter(query: types.CallbackQuery):
    return query.data in (YES_BTN.callback_data, NO_BTN.callback_data)
