from aiogram.filters import Command, CommandObject
from aiogram.types import FSInputFile

from data.config import CHAT_ID, PAYMENT_THREAD_ID, STATUS_QUEUE, STATUS_TRANSACTIONS, NAME_PROJECT
from keyboards.inline.adminkeyinline import withdraftChatPanel, backFunKey, withdraftPanle
from keyboards.inline.userinlinekey import mainKeyInline, referalKeyInline

from loader import *
from utils.misc_func.bot_models import FSM


def default_transaction_text(user, transaction):
    text = (
        f"<b>ID транзакция:</b> <code>{transaction['_id']}</code>\n\n"
        f"👤 Пользователь: <code>{user['full_name']}</code>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user['_id']}</code>\n\n"
        f"💸 Сумма: <code>{transaction['amount']}$</code>\n"
        f"ℹ️ Статус: <b>{STATUS_TRANSACTIONS[transaction['status']]['name']}</b>"
    )
    return text


def default_user_info_for_admin(user: dict, sum_hold: str):
    text = (
        f"👤 Пользователь: <code>{user['full_name']}</code>\n"
        f"👤 Юзернейм: @{user['username']}\n"
        f"🆔: <code>{user['_id']}</code>\n\n"
        f"💸 Сумма вывода: ${round(float(sum_hold), 2)}"
    )
    return text


@userRouter.message(Command("start"))
async def start_user(msg: Message, state: FSM):
    if "withdraft_" in msg.text.replace("/start ", ""):
        withdraft_id = int(msg.text.replace("/start ", "").replace("withdraft_", ""))
        withdraft = await db.get_transaction(withdraft_id)
        user = await db.get_user_info(int(withdraft["user_id"]))
        hold = await db.get_hold_balance_user(int(withdraft["user_id"]), "wait_withdraft")
        sum_hold = sum(row["amount"] for row in hold)
        if withdraft["status"] == "wait_withdraft":
            text_admin = default_transaction_text(user, withdraft)
            return msg.answer(text_admin, reply_markup=withdraftPanle(withdraft_id))
        else:
            return msg.answer("Транзакция не акутальна")
    settings = await db.get_settings()
    user = await db.get_user_info(msg.from_user.id)
    hold = await db.get_hold_balance_user(msg.from_user.id, "wait_withdraft")
    sum_hold = sum(row["amount"] for row in hold)
    text = (
        f"👋 Добро пожаловать в <b>{NAME_PROJECT}</b>!\n\n"
        f"🆔: <code>{msg.from_user.id}</code>\n"
        f"👛 Баланс: ${round(user['balance'], 2)}\n"
        f"🧊 На выводе: ${round(float(sum_hold), 2)}\n\n"
        f"💰 Ставка за 2 часа: ${settings['amount_pay']}"
    )
    return msg.answer_photo(
        photo=FSInputFile("data/hello_page.jpg"), caption=text, reply_markup=mainKeyInline()
    )


@userRouter.message(Command("menu"))
@userRouter.message(F.text == "💠 Показать меню 💠")
async def view_menu_user_func(msg: Message, state: FSM):
    settings = await db.get_settings()
    user = await db.get_user_info(msg.from_user.id)
    hold = await db.get_hold_balance_user(msg.from_user.id, "wait_withdraft")
    sum_hold = sum(row["amount"] for row in hold)
    text = (
        f"👋 Добро пожаловать в <b>{NAME_PROJECT}</b>!\n\n"
        f"🆔: <code>{msg.from_user.id}</code>\n"
        f"👛 Баланс: ${user['balance']}\n"
        f"🧊 На выводе: ${round(float(sum_hold), 2)}\n\n"
        f"💰 Ставка за 2 часа: ${settings['amount_pay']}"
    )
    return msg.answer_photo(
        photo=FSInputFile("data/hello_page.jpg"), caption=text, reply_markup=mainKeyInline()
    )


@userRouter.callback_query(F.data == "backMainMenu")
async def back_main_menu_func(call: CallbackQuery, state: FSM):
    await state.clear()
    settings = await db.get_settings()
    user = await db.get_user_info(call.from_user.id)
    hold = await db.get_hold_balance_user(call.from_user.id, "wait_withdraft")
    sum_hold = sum(row["amount"] for row in hold)
    text = (
        f"👋 Добро пожаловать в <b>{NAME_PROJECT}</b>!\n\n"
        f"🆔: <code>{call.from_user.id}</code>\n"
        f"👛 Баланс: ${user['balance']}\n"
        f"🧊 На выводе: ${round(float(sum_hold), 2)}\n\n"
        f"💰 Ставка за 2 часа: ${settings['amount_pay']}"
    )
    await call.message.delete()
    await bot.send_photo(
        chat_id=call.from_user.id,
        photo=FSInputFile("data/hello_page.jpg"),
        caption=text,
        reply_markup=mainKeyInline(),
    )


@userRouter.callback_query(F.data == "referal_system")
async def referal_system_page(call: CallbackQuery, state: FSM):
    bot_info = await bot.get_me()
    username = bot_info.username
    link = f"https://t.me/{username}?start={call.from_user.id}"
    ref_amounts = await db.get_hold_balance_user(call.from_user.id, "refferal")
    sum_amount = sum(row["amount"] for row in ref_amounts)
    settings = await db.get_settings()
    text = (
        f"<b>👤 Реферальная система</b>\n\n"
        "<i>ℹ️ Приглашайте друзей и получайте процент с заработка ваших рефералов.</i>\n\n"
        f"📟 Реферальный процент: <code>{settings['referal_procent']}%</code>\n\n"
        f"💸 Всего заработано с рефералов: <code>{round(float(sum_amount), 2)}$</code>\n\n"
        f"🔗 Пригласительная ссылка: {link}"
    )
    await call.message.delete()
    return call.message.answer(text, reply_markup=referalKeyInline(link))


@userRouter.callback_query(F.data == "withdraft")
async def withdraft_page(call: CallbackQuery, state: FSM):
    user = await db.get_user_info(call.from_user.id)
    if user["balance"] <= 0:
        return call.answer(f"На вашем балансе {user['balance']}$. Этого не достаточно для вывода", True)
    transaction_id = await db.create_transactions(call.from_user.id, float(user["balance"]), "wait_withdraft")
    await db.update_amount_user(call.from_user.id, float(f"-{user['balance']}"))
    text = (
        "<b>✅ Заявка на вывод средств была подана!</b>\n\n"
        "<i>⏳ Обычно вывод средств не занимает более 24 часов</i>"
    )
    text_admin = (
        f"💰 Новая заявка на вывод средств (ID: <code>{transaction_id}</code>):\n\n"
        f"👤 Пользователь: <code>{call.from_user.first_name}</code>\n"
        f"👤 Юзернейм: @{call.from_user.username}\n"
        f"🆔: <code>{call.from_user.id}</code>\n\n"
        f"💸 Сумма вывода: <code>{user['balance']}$</code>"
    )
    bot_info = await bot.get_me()
    username = bot_info.username
    link = f"https://t.me/{username}?start=withdraft_{transaction_id}"
    await bot.send_message(
        chat_id=CHAT_ID,
        text=text_admin,
        reply_markup=withdraftChatPanel(link),
        message_thread_id=PAYMENT_THREAD_ID,
    )
    await call.message.delete()
    return call.message.answer(text, reply_markup=backFunKey("backMainMenu"))


@userRouter.callback_query(F.data == "statistic")
async def get_statistic_user_page(call: CallbackQuery, state: FSM):
    all_queue_phones = await db.get_all_queue_by_user_id(call.from_user.id)
    text = f"\n📲 Всего номеров: <code>{len(all_queue_phones)} шт</code>\n"
    for key, status in STATUS_QUEUE.items():
        if key in ["in_queue", "in_proccess", "cancel", "false", "false_user", "done"]:
            text += (
                f"\n {status['symbol']} {status['name'].title()}: "
                f"<code>{len(await db.get_queue_user_by_status(call.from_user.id, key))} шт</code>"
            )
    list_trans = await db.get_hold_balance_user(call.from_user.id, "refferal")
    list_trans_2 = await db.get_hold_balance_user(call.from_user.id, "replenishment")
    ref_amount = sum(item["amount"] for item in list_trans)
    work_amount = sum(item["amount"] for item in list_trans_2)
    text += (
        f"\n\n💸 Заработано за рефералов всего: <code>{ref_amount}$</code>\n"
        f"💸 Заработано за сдачу номеров всего: <code>{work_amount}$</code>"
    )
    await call.message.delete()
    return call.message.answer(text, reply_markup=backFunKey("backMainMenu"))