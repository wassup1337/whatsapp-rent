from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import *
from typing import Any, Dict, Union
from loader import *
from datetime import datetime
from keyboards.reply.usermainkey import *
from keyboards.inline.userinlinekey import *
from loguru import logger
from utils.misc_func.bot_models import *


from typing import *
from keyboards.inline.adminkeyinline import *

from data.config import ROLES
from states.user_state import *
from utils.misc_func.otherfunc import format_phone_number



@userRouter.callback_query(F.data=='number_rent')
async def number_rent_start_page(call: CallbackQuery, state: FSM):

    await state.clear()

    await state.set_state(addPhoneNumber.phone_number)

    text = f'''
<b>📲 Сдать номер</b>

<i>ℹ️ Что бы сдать свой номер в аренду введите его в формате:</i>

<code>79999999999</code>

<i>🔔 После этого вы попадете в очередь, когда очередь дойдет до вас придет уведомление.</i>
'''

    await call.message.delete()

    return call.message.answer(text, reply_markup=backFunKey('backMainMenu'))



@userRouter.message(addPhoneNumber.phone_number)
async def addPhoneNumber_phone_number_handler(msg: Message, state: FSM):
    
    phone_number = format_phone_number(msg.text)

    logger.warning(phone_number)

    if phone_number is False:

        await state.set_state(addPhoneNumber.phone_number)

        return msg.answer('Неправильный формат номер телефона, пожалуйста, введите номер телефона в формате:\n\n<code>79999999999</code>',
                        reply_markup=backFunKey('backMainMenu'))
    
    add = await db.add_phone_number(msg.from_user.id, phone_number)

    await state.clear()

    if add['status']:
        text = f'''
<b>✅ Номер телефона</b> {msg.text} <b>был успешно добавлен в очередь!</b>

<i>📄 Место в очереди для этого номера телефона:</i> <code>{add["msg"]}</code>
'''
        
    else:
        text = f'''
<b>⚠️ Не удалось добавить номер телефона в очередь</b>

📄 Причина: <code>{add["msg"]}</code>
'''
        
    return msg.answer(text, reply_markup=backFunKey('backMainMenu'))
    