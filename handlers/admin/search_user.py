
from aiogram.types import CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message

from data.config import ADMIN, ROLES, STATUS_QUEUE, db
from keyboards.inline.adminkeyinline import backFunKey, sendMsgKey, setRoleKey, userOptions, transactionsListUserKey, allUserTicketListKey, searchUserKey
from loader import *
from states.admin_state import messageUser
from utils.misc_func.bot_models import FSM
from utils.misc_func.otherfunc import generate_short_uuid


@adminRouter.message(F.text == "👤 Юзеры")
async def info_search_user(msg: Message, state: FSM):
    text = (
        "<b>👤 Юзеры</b>\n\n"
        "Что бы найти пользователя воспользуйтесь кнопкой ниже и начните вводить информацию о пользователе, "
        "например его ID, имя или юзернейм в любом регистре.\n\n"
        "Альтернативный метод:\n\n"
        "<code>/user USER_ID</code>\n\n"
        "В место USER_ID вставьте ID пользователя и отправьте боту."
    )
    return msg.answer(text, reply_markup=searchUserKey())


@adminRouter.inline_query(F.query.startswith("user "))
async def inline_query_func(query: InlineQuery, state: FSM):
    user_params = query.query.replace("user ", "").replace("@", "")
    worker = await db.get_user_info(query.from_user.id)
    if worker["role"] in ["admin", "owner"] or worker["_id"] in ADMIN:
        users_list = await db.get_all_users()
    return_list = []
    for item in users_list:
        if (
            str(user_params).lower() in str(item["full_name"]).lower()
            or str(user_params).lower() in str(item["_id"]).lower()
        ):
            add = InlineQueryResultArticle(
                id=generate_short_uuid(),
                title=f"{item['full_name']} ({item['_id']})",
                input_message_content=InputTextMessageContent(message_text=f"/user {item['_id']}"),
            )
            return_list.append(add)
    await query.answer(results=return_list, cache_time=1)


@adminRouter.message(F.text.startswith("/user "))
async def open_user_message_func(msg: Message, state: FSM):
    user_id = int(msg.text.replace("/user ", ""))
    user = await db.get_user_info(user_id)
    create_at = user["created_at"]
    formatted_date = create_at.strftime("%Y-%m-%d %H:%M")
    text = (
        f"👤 Пользователь: <code>{user['full_name']}</code>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user_id}</code>\n\n"
        f"⏳ Дата регистрации: <code>{formatted_date}</code>\n\n"
        f"🔐 Роль: <code>{ROLES[user['role']]}</code>\n\n"
        f"👛 Баланс: <code>{user['balance']}$</code>"
    )
    return msg.answer(text, reply_markup=userOptions(user_id))


@adminRouter.callback_query(F.data.startswith("openuser_"))
async def open_user_callback_query_func(call: CallbackQuery, state: FSM):
    user_id = int(call.data.replace("openuser_", ""))
    user = await db.get_user_info(user_id)
    create_at = user["created_at"]
    formatted_date = create_at.strftime("%Y-%m-%d %H:%M")
    text = (
        f"👤 Пользователь: <code>{user['full_name']}</code>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user_id}</code>\n\n"
        f"⏳ Дата регистрации: <code>{formatted_date}</code>\n\n"
        f"🔐 Роль: <code>{ROLES[user['role']]}</code>\n\n"
        f"👛 Баланс: <code>{user['balance']}$</code>"
    )
    return call.message.edit_text(text, reply_markup=userOptions(user_id))


@adminRouter.callback_query(F.data.startswith("set_role_"))
async def set_role_func(call: CallbackQuery, state: FSM):
    user_id = int(call.data.replace("set_role_", ""))
    user = await db.get_user_info(user_id)
    text = (
        f"🔐 Смена роли для пользователя <code>{user['full_name']}</code> ({user['_id']})\n\n"
        f"👤 В настоящий момент роль: <code>{ROLES[user['role']]}</code>\n\n"
        "🔄 Что бы сменить роль выберите одну из тех что предоставлена ниже:"
    )
    return call.message.edit_text(text, reply_markup=setRoleKey(user_id))


@adminRouter.callback_query(F.data.startswith("updrole_"))
async def update_role_func(call: CallbackQuery, state: FSM):
    _, user_id, role = call.data.split("_")
    user_update = await db.update_user_role(int(user_id), role)
    await call.answer("✅ Роль успешно изменена")
    text = (
        f"🔐 Смена роли для пользователя <code>{user_update['full_name']}</code> ({user_update['_id']})\n\n"
        f"👤 В настоящий момент роль: <code>{ROLES[user_update['role']]}</code>\n\n"
        "🔄 Что бы сменить роль выберите одну из тех что предоставлена ниже:"
    )
    return call.message.edit_text(text, reply_markup=setRoleKey(user_id))


@adminRouter.callback_query(F.data.startswith("smsg_"))
async def send_msg_func(call: CallbackQuery, state: FSM):
    _, user_id = call.data.split("_")
    user = await db.get_user_info(int(user_id))
    text = (
        f"📨 Введите сообщение для пользователя {user['full_name']} (<code>{user_id}</code> | @{user['username']})"
    )
    await state.update_data(user_id=user_id)
    await state.set_state(messageUser.message)
    return call.message.edit_text(text, reply_markup=backFunKey(f"openuser_{user_id}"))


@adminRouter.message(messageUser.message)
async def message_user_function(msg: Message, state: FSM):
    data = await state.get_data()
    user_id = data.get("user_id")
    user = await db.get_user_info(int(user_id))
    await state.update_data(message=msg.html_text)
    await state.set_state(messageUser.send)
    msg_text = (
        f"📨 Ваше сообщение для пользователя {user['full_name']} (<code>{user_id}</code> | @{user['username']})\n\n"
        f"{msg.html_text}\n\n"
        "Отправить?"
    )
    return msg.answer(msg_text, reply_markup=sendMsgKey(user_id))


@adminRouter.callback_query(F.data == "sendmsguser")
async def send_msg_user_func(call: CallbackQuery, state: FSM):
    data = await state.get_data()
    if data is None:
        return call.answer("Это вообщение не возможно отправить", True)
    user_text = "<b>📨 Сообщение от администрации:\n\n</b>"
    user_text = data.get("message")
    user_id = data.get("user_id")
    try:
        await bot.send_message(user_id, user_text)
        await call.message.edit_text(
            str(call.message.html_text) + "\n✅ Сообщение успешно отправлено",
            reply_markup=backFunKey(f"openuser_{user_id}"),
        )
        await state.clear()
    except Exception as e:
        return call.answer(e.message, True)


@adminRouter.callback_query(F.data.startswith("statistic_"))
async def statistic_func_page(call: CallbackQuery, state: FSM):
    _, user_id = call.data.split("_")
    all_queue_phones = await db.get_all_queue_by_user_id(int(user_id))
    text = f"\n📲 Всего номеров: <code>{len(all_queue_phones)} шт</code>\n"
    for key, status in STATUS_QUEUE.items():
        if key in ["in_queue", "in_proccess", "cancel", "false", "false_user", "done"]:
            text += (
                f"\n {status['symbol']} {status['name'].title()}: "
                f"<code>{len(await db.get_queue_user_by_status(int(user_id), key))} шт</code>"
            )
    list_trans = await db.get_hold_balance_user(int(user_id), "refferal")
    list_trans_2 = await db.get_hold_balance_user(int(user_id), "replenishment")
    ref_amount = sum(item["amount"] for item in list_trans)
    work_amount = sum(item["amount"] for item in list_trans_2)
    text += (
        f"\n\n💸 Заработано за рефералов всего: <code>{ref_amount}$</code>\n"
        f"💸 Заработано за сдачу номеров всего: <code>{work_amount}$</code>"
    )
    return call.message.edit_text(text, reply_markup=backFunKey(f"openuser_{user_id}"))


@adminRouter.callback_query(F.data.startswith("transactions_"))
async def transactions_page_admin(call: CallbackQuery, state: FSM):
    _, user_id = call.data.split("_")
    transactions_list = await db.get_all_transactions_user(int(user_id))
    transactions_list.reverse()
    user = await db.get_user_info(int(user_id))
    text = (
        f"<b>💱 Транзакции пользователя <code>{user['full_name']}</code></b>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user_id}</code>"
    )
    key = transactionsListUserKey(
        transactions_list[:5], 0, len(transactions_list[:5]), len(transactions_list), user_id
    )
    return call.message.edit_text(text, reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_tru_next_"))
async def list_paymentsu_func_next(call: CallbackQuery, state: FSM):
    await state.clear()
    call_data = str(call.data.replace("list_tru_next_", ""))
    step = int(call_data.split("_")[0])
    user_id = call_data.split("_")[1]
    transactions_list = await db.get_all_transactions_user(int(user_id))
    transactions_list.reverse()
    if len(transactions_list[step : step + 5]) == 0:
        await call.answer("Это последняя страница", True)
    else:
        key = transactionsListUserKey(
            transactions_list[step : step + 5],
            step,
            len(transactions_list[: step + 5]),
            len(transactions_list),
            user_id,
        )
        await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_tru_back_"))
async def list_paymentsu_page_back(call: CallbackQuery, state: FSM):
    call_data = str(call.data.replace("list_tru_back_", ""))
    step = int(call_data.split("_")[0])
    user_id = call_data.split("_")[1]
    if step == 0:
        await call.answer("Это была последняя страница", True)
    else:
        await state.clear()
        transactions_list = await db.get_all_transactions_user(int(user_id))
        transactions_list.reverse()
        key = transactionsListUserKey(
            transactions_list[step - 5 : step],
            step - 5,
            len(transactions_list[:step]),
            len(transactions_list),
            user_id,
        )
        await call.message.edit_reply_markup(reply_markup=key)


@adminRouter.callback_query(F.data.startswith("numhistory_"))
async def numhistory_page(call: CallbackQuery, state: FSM):
    _, user_id = call.data.split("_")
    list_phones = await db.get_all_queue_by_user_id(int(user_id))
    user = await db.get_user_info(int(user_id))
    text = (
        f"<b>📱 Истори номеров клиента</b>\n\n"
        f"👤 Пользователь: <code>{user['full_name']}</code>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user_id}</code>"
    )
    key = allUserTicketListKey(
        list_phones[:5], 0, len(list_phones[:5]), len(list_phones), user_id
    )
    return call.message.edit_text(text, reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_ut_next_"))
async def list_paymentsu_ut_func_next(call: CallbackQuery, state: FSM):
    await state.clear()
    call_data = str(call.data.replace("list_ut_next_", ""))
    step = int(call_data.split("_")[0])
    user_id = call_data.split("_")[1]
    transactions_list = await db.get_all_queue_by_user_id(int(user_id))
    transactions_list.reverse()
    if len(transactions_list[step : step + 5]) == 0:
        await call.answer("Это последняя страница", True)
    else:
        key = allUserTicketListKey(
            transactions_list[step : step + 5],
            step,
            len(transactions_list[: step + 5]),
            len(transactions_list),
            user_id,
        )
        await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_ut_back_"))
async def list_paymentsu_ur_page_back(call: CallbackQuery, state: FSM):
    call_data = str(call.data.replace("list_ut_back_", ""))
    step = int(call_data.split("_")[0])
    user_id = call_data.split("_")[1]
    if step == 0:
        await call.answer("Это была последняя страница", True)
    else:
        await state.clear()
        transactions_list = await db.get_all_queue_by_user_id(int(user_id))
        transactions_list.reverse()
        key = allUserTicketListKey(
            transactions_list[step - 5 : step],
            step - 5,
            len(transactions_list[:step]),
            len(transactions_list),
            user_id,
        )
        await call.message.edit_reply_markup(reply_markup=key)