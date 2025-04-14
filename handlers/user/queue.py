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
from data.config import STATUS_QUEUE


@userRouter.callback_query(F.data=='queue_list')
async def queue_page(call: CallbackQuery, state: FSM):

    list_queue = await db.get_in_queue_user(call.from_user.id)
    
    text = f'''
<b>📄 Очередь</b>

<i>ℹ️ В этом разделе вы можете посмотреть свои номера, которые находятся в очереди. 
Нажав на кнопку с номером телефона можно посмотреть более подробную информацию.
Нажав на "🗑" вы удалите свой номер из очереди</i>
'''
    
    key = queuePagination(list_queue[0:5], 0, len(list_queue[:5]), len(list_queue))

    await call.message.delete()

    return call.message.answer(text, reply_markup=key)


@userRouter.callback_query(F.data.startswith('list_ph_next_'))
async def listPhoneFunc_next(call: CallbackQuery, state: FSM):
    
    step = int(call.data.replace('list_ph_next_', ''))
    
    await state.clear()

    list_queue: list = await db.get_in_queue_user(call.from_user.id)
    
        
    if len(list_queue[step:step+5]) == 0:
        await call.answer('Это последняя страница', True)
        
    else:        
        key = queuePagination(list_queue[step:step+5], step, len(list_queue[:step+5]), len(list_queue))
        
        await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith('list_ph_back_'))
async def listPhonePage_back(call: CallbackQuery, state: FSM):
    
    step = int(call.data.replace('list_ph_back_', ''))
    
    if step == 0:
        await call.answer('Это была последняя страница', True)
    
    else:
        await state.clear()
        
        list_queue: list = await db.get_in_queue_user(call.from_user.id)
 
        key = queuePagination(list_queue[step-5:step], step-5, len(list_queue[:step]), len(list_queue))
        
        await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith('open_ph_'))
async def open_ph_page(call: CallbackQuery, state: FSM):

    _, _, type_, _id = call.data.split('_')

    logger.warning(type_)
    logger.warning(_id)

    _id = int(_id)

    queue_info = await db.get_queue_info_by_id(_id)

    text = f'''
<b>ℹ️ Инофрмация о номере</b>

📲 Номер: <code>{queue_info["phone_number"]}</code>
📄 Место в очереди: 0
🔷 Статус: {STATUS_QUEUE[queue_info["status"]]["name"]}
'''
    _call = 'queue_list' if type_ == 'q' else 'number_history'

    return call.message.edit_text(text, reply_markup=backFunKey(_call))


@userRouter.callback_query(F.data.startswith('delph_'))
async def delph__page(call: CallbackQuery, state: FSM):
    
    _id = int(call.data.replace('delph_', ''))

    queue_info = await db.get_queue_info_by_id(_id)

    if queue_info["status"] not in ['in_queue']:

        return call.answer('⚠️ Этот номер не возможно удалить так как его уже взяли в обработку')

    text = f'''
<b>❓ Вы уверны, что хотите удалить номер из очеред?</b>

<i>⚠️ Если вы это сделаете и добавите номер снова он встанет в конец очереди</i>
'''

    return call.message.edit_text(text, reply_markup=deletePhoneTwoFactor(_id))


@userRouter.callback_query(F.data.startswith('sucdelph_'))
async def sucdelph_func(call: CallbackQuery, state: FSM):

    _id = int(call.data.replace('sucdelph_', ''))

    queue_info = await db.get_queue_info_by_id(_id)

    if queue_info["status"] not in ['in_queue']:

        return call.answer('Этот номер не возможно удалить так как его уже взяли в обработку', True)

    delete = await db.update_phone_number_status(_id, 'deleted')

    if delete:
        return call.message.edit_text('<b>✅ Номер успешно удален</b>', reply_markup=backFunKey('queue_list'))
    
    else:
        return call.answer('<b>⚠️ Произошла ошибка при удалении номера</b>', True)
    


@userRouter.callback_query(F.data=='number_history')
async def number_history_page(call: CallbackQuery, state: FSM):

    list_queue = await db.get_all_phone_numbers_user(call.from_user.id)
    list_queue.reverse()

    text = f'''
<b>🗂 История номеров</b>

<i>ℹ️ Здесь вы можете просмотреть историю номеров</i>
'''
    
    key = historyPhoneNumberPagination(list_queue[0:5], 0, len(list_queue[:5]), len(list_queue))

    await call.message.delete()

    return call.message.answer(text, reply_markup=key)


@userRouter.callback_query(F.data.startswith('list_hpn_next_'))
async def listPhoneFunc_next(call: CallbackQuery, state: FSM):
    
    step = int(call.data.replace('list_hpn_next_', ''))
    
    await state.clear()

    list_queue: list = await db.get_all_phone_numbers_user(call.from_user.id)
    list_queue.reverse()
        
    if len(list_queue[step:step+5]) == 0:
        await call.answer('Это последняя страница', True)
        
    else:
        key = historyPhoneNumberPagination(list_queue[step:step+5], step, len(list_queue[:step+5]), len(list_queue))
        
        await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith('list_hpn_back_'))
async def listPhonePage_back(call: CallbackQuery, state: FSM):
    
    step = int(call.data.replace('list_hpn_back_', ''))
    
    if step == 0:
        await call.answer('Это была последняя страница', True)
    
    else:
        await state.clear()
        
        list_queue: list = await db.get_all_phone_numbers_user(call.from_user.id)
        list_queue.reverse()
   
        key = historyPhoneNumberPagination(list_queue[step-5:step], step-5, len(list_queue[:step]), len(list_queue))
        
        await call.message.edit_reply_markup(reply_markup=key)