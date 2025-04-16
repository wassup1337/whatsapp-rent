from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message

from data.config import STATUS_TRANSACTIONS
from keyboards.inline.adminkeyinline import backFunKey, sendPaymentKey, transactionViewerKey, transactionsListKey, twoFactorFalsePayKey
from loader import *
from states.admin_state import paymentUser
from utils.misc_func.bot_models import FSM
from utils.misc_func.otherfunc import generate_short_uuid


def default_transaction_text(user, transaction):
    return (
        f"<b>ID транзакция:</b> <code>{transaction['_id']}</code>\n\n"
        f"👤 Пользователь: <code>{user['full_name']}</code>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user['_id']}</code>\n\n"
        f"💸 Сумма: <code>{transaction['amount']}$</code>\n"
        f"ℹ️ Статус: <b>{STATUS_TRANSACTIONS[transaction['status']]['name']}</b>"
    )


@adminRouter.message(F.text == "💱 Транзакции")
async def admin_transactions_pay(msg: Message, state: FSM):
    await state.clear()
    transactions_list = await db.get_all_transactions()
    transactions_list.reverse()
    text = (
        "<b>💱 Транзакции</b>\n\n"
        "<i>ℹ️ В этом разделе вы можете посмотреть все транзакции</i>\n\n"
        'ℹ️ Если хотите осуществить транзакцию по ее ID или другой имеющейся у вас информации воспользуйтесь кнопкой <b>"🔎 Поиск"</b>'
    )
    key = transactionsListKey(transactions_list[:5], 0, len(transactions_list[:5]), len(transactions_list))
    return msg.answer(text, reply_markup=key)


@adminRouter.callback_query(F.data == "transactions")
async def transactions_page_func(call: CallbackQuery, state: FSM):
    await state.clear()
    transactions_list = await db.get_all_transactions()
    transactions_list.reverse()
    text = (
        "<b>💱 Транзакции</b>\n\n"
        "<i>ℹ️ В этом разделе вы можете посмотреть все транзакции</i>\n\n"
        'ℹ️ Если хотите осуществить транзакцию по ее ID или другой имеющейся у вас информации воспользуйтесь кнопкой <b>"🔎 Поиск"</b>'
    )
    key = transactionsListKey(transactions_list[:5], 0, len(transactions_list[:5]), len(transactions_list))
    return call.message.edit_text(text, reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_tr_next_"))
async def list_payments_func_next(call: CallbackQuery, state: FSM):
    step = int(call.data.replace("list_tr_next_", ""))
    await state.clear()
    transactions_list = await db.get_all_transactions()
    transactions_list.reverse()
    if len(transactions_list[step : step + 5]) == 0:
        await call.answer("Это последняя страница", True)
    else:
        key = transactionsListKey(
            transactions_list[step : step + 5],
            step,
            len(transactions_list[: step + 5]),
            len(transactions_list),
        )
        await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_tr_back_"))
async def list_payments_page_back(call: CallbackQuery, state: FSM):
    step = int(call.data.replace("list_tr_back_", ""))
    if step == 0:
        await call.answer("Это была последняя страница", True)
    else:
        await state.clear()
        transactions_list = await db.get_all_transactions()
        transactions_list.reverse()
        key = transactionsListKey(
            transactions_list[step - 5 : step],
            step - 5,
            len(transactions_list[:step]),
            len(transactions_list),
        )
        await call.message.edit_reply_markup(reply_markup=key)


@adminRouter.inline_query(F.query.startswith("payment "))
async def payment_inline_query_func(query: InlineQuery, state: FSM):
    user_params = query.query.replace("payment ", "")
    transactions_list = await db.get_all_transactions()
    return_list = []
    param = str(user_params).lower()
    for item in transactions_list:
        if (
            param in str(item["_id"]).lower()
            or param in str(item["user_id"]).lower()
            or param in str(item["status"])
        ):
            add = InlineQueryResultArticle(
                id=generate_short_uuid(),
                title=f"ID: {item['_id']} ({item['amount']})",
                input_message_content=InputTextMessageContent(
                    message_text=f"/transacition {item['_id']}"
                ),
            )
            return_list.append(add)
    await query.answer(results=return_list, cache_time=1)


@adminRouter.message(F.text.startswith("/transacition "))
async def open_user_message_func(msg: Message, state: FSM):
    await state.clear()
    transaction_id = int(msg.text.replace("/transacition ", ""))
    transaction = await db.get_transaction(transaction_id)
    user = await db.get_user_info(int(transaction["user_id"]))
    text = default_transaction_text(user, transaction)
    return msg.answer(text, reply_markup=transactionViewerKey(transaction_id, transaction["status"]))


@adminRouter.callback_query(F.data.startswith("gettrans_"))
async def gettrans_page(call: CallbackQuery, state: FSM):
    await state.clear()
    transaction_id = int(call.data.split("_")[1])
    transaction = await db.get_transaction(transaction_id)
    user = await db.get_user_info(int(transaction["user_id"]))
    text = default_transaction_text(user, transaction)
    return call.message.edit_text(
        text, reply_markup=transactionViewerKey(transaction_id, transaction["status"])
    )


@adminRouter.callback_query(F.data.startswith("payout_"))
async def payout_page(call: CallbackQuery, state: FSM):
    await state.clear()
    _id = int(call.data.split("_")[1])
    transaction = await db.get_transaction(int(_id))
    user = await db.get_user_info(int(transaction["user_id"]))
    text = default_transaction_text(user, transaction)
    text += f"\nОтправьте ссылку на чек с криптобота на сумму <code>{transaction['amount']}$</code>"
    await state.update_data(trans_id=_id)
    await state.set_state(paymentUser.url)
    return call.message.edit_text(text, reply_markup=backFunKey(f"gettrans_{_id}"))


@adminRouter.message(paymentUser.url)
async def payment_user_message(msg: Message, state: FSM):
    data = await state.get_data()
    _id = int(data["trans_id"])
    if "https://t.me/" in msg.text:
        transaction = await db.get_transaction(int(_id))
        user = await db.get_user_info(int(transaction["user_id"]))
        await state.update_data(url=msg.text)
        text = default_transaction_text(user, transaction)
        text += f"\n💸 Вы хотите отправить чек {msg.text} ?"
        await state.set_state(paymentUser.send)
        return msg.answer(text, reply_markup=sendPaymentKey(_id))
    else:
        await state.set_state(paymentUser.url)
        text = "Кажется, это не ссылка, попробуйте снова:"
        return msg.answer(text, reply_markup=backFunKey(f"gettrans_{_id}"))


@adminRouter.callback_query(paymentUser.send, F.data.startswith("sendcheck"))
async def sendcheck_page(call: CallbackQuery, state: FSM):
    data = await state.get_data()
    if data is None:
        return call.answer("Это сообщение для отправки выплаты не актуально, попробуйте сделать выплату снова")
    _id = data["trans_id"]
    transaction = await db.get_transaction(int(_id))
    user = await db.get_user_info(int(transaction["user_id"]))
    text_user = (
        f"🆔 транзакции: <code>{_id}</code>\n\n"
        f"💸 Ваш чек на <code>{transaction['amount']}$</code>\n\n"
        f"{data['url']}"
    )
    await bot.send_message(chat_id=transaction["user_id"], text=text_user)
    await db.update_transaction_status(int(_id), "finish_withdraft", data["url"])
    admin_text = default_transaction_text(user, transaction)
    admin_text += "\n💸 Чек был успешно отправлен пользоватлю, вы произвели выплату"
    return call.message.edit_text(admin_text)


@adminRouter.callback_query(F.data.startswith("falsepay_"))
async def falsepay_page(call: CallbackQuery, state: FSM):
    _id = int(call.data.split("_")[1])
    await state.clear()
    transaction = await db.get_transaction(int(_id))
    user = await db.get_user_info(int(transaction["user_id"]))
    text = default_transaction_text(user, transaction)
    text += (
        "\nВы уверены, что хотите отменить эту выплату? Пользователю будут возвращены средства на баланс"
    )
    return call.message.edit_text(text, reply_markup=twoFactorFalsePayKey(_id))


@adminRouter.callback_query(F.data.startswith("falpays_"))
async def falpays_page(call: CallbackQuery, state: FSM):
    _id = int(call.data.split("_")[1])
    await state.clear()
    transaction = await db.get_transaction(int(_id))
    user = await db.get_user_info(int(transaction["user_id"]))
    await db.update_transaction_status(int(_id), "false_withdraft")
    text = default_transaction_text(user, transaction)
    text += "\n♻️ Выплата отменена, пользоватль был уведомлен и получил средства на баланс"
    user_text = (
        "❓ К сожалению, администрация по какой то причине отменила ваш вывод средств. "
        "Деньги были возвращены на баланс бота, если у вас есть какие то вопросы напишите в техническую поддержку.\n"
        f"К возврату: <code>{transaction['amount']}$</code>"
    )
    up_balance = await db.update_amount_user(user["_id"], float(transaction["amount"]))
    await bot.send_message(chat_id=user["_id"], text=user_text)
    return call.message.edit_text(text)
