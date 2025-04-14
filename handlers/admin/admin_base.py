from aiogram.filters import Command, CommandObject

from keyboards.reply.adminkey import kbMainAdmin
from loader import *
from utils.misc_func.bot_models import FSM
from loguru import logger


@adminRouter.message(Command("admin"))
async def admin_main_page(msg: Message, state: FSM):
    text = (
        "Добро пожаловать в <b>панель администратора!</b>\n\n"
        "<i>Воспользуйтесь кнопками ниже для управления ботом 👇</i>"
    )
    return msg.answer(text, reply_markup=kbMainAdmin())


@adminRouter.message(F.text == "⚙️ Настройки")
async def settings_page(msg: Message, state: FSM):
    await state.clear()
    settings = await db.get_settings()
    text = (
        "<b>⚙️ Настройки</b>\n\n"
        "<i>ℹ️ В данном разделе находятся инофрмация и команды для смены реферального процента и для смены ставки</i>\n\n"
        f"📟 Актуальный реферальный процент: <code>{settings['referal_procent']}%</code>\n"
        f"💸 Актуальная ставка за 2 часа: <code>{settings['amount_pay']}$</code>\n\n"
        "<b>🎫 Команды:</b>\n\n"
        "<code>/percent число</code> — в место <b>\"число\"</b> введите новый реферальный процент, например:\n"
        "<code>/percent 10</code>\n\n"
        "<code>/pay число</code> — в место <b>\"число\"</b> введите новую ставку за 2 часа, например:\n"
        "<code>/pay 7</code>"
    )
    return msg.answer(text)


@adminRouter.message(F.text.startswith("/percent"))
async def percent_set_page(msg: Message, state: FSM):
    try:
        percent = float(msg.text.replace("/percent ", ""))
        await db.update_percent(percent)
        text = f"✅ Реферальный процент успешно изменен на <code>{percent}%</code>"
    except Exception as e:
        logger.error(e)
        text = "⚠️ Кажется, вы ввели не число, попробуйте снова"
    return msg.reply(text, reply_markup=kbMainAdmin())


@adminRouter.message(F.text.startswith("/pay"))
async def percent_set_page(msg: Message, state: FSM):
    try:
        percent = float(msg.text.replace("/pay ", ""))
        await db.update_pay(percent)
        text = f"✅ Размер выплаты за 2 зача изменен на <code>{percent}$</code>"
    except Exception as e:
        logger.error(e)
        text = "⚠️ Кажется, вы ввели не число, попробуйте снова"
    return msg.reply(text, reply_markup=kbMainAdmin())