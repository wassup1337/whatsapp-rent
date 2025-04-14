from data.config import db
from keyboards.inline.adminkeyinline import mailingFalseKey, sendMailingKey
from keyboards.reply.adminkey import kbMainAdmin
from loader import *
from states.admin_state import mailingPost
from utils.misc_func.bot_models import FSM
from utils.misc_func.otherfunc import createMediaGroup


@adminRouter.message(F.text == "📢 Рассылка")
async def mailing_main_page(msg: Message, state: FSM):
    text = (
        "<b>📢 Рассылка</b>\n\n"
        "<i>Для того, что бы начать рассылку отправьте боту готовый пост, включая картинки, текст и т.д.</i>"
    )
    await state.set_state(mailingPost.post)
    return msg.answer(text, reply_markup=mailingFalseKey())


@adminRouter.message(mailingPost.post, F.media_group_id)
async def mailing_post_page(msg: Message, state: FSM, album: list[Message]):
    media_group = await createMediaGroup(album)
    await bot.send_media_group(chat_id=msg.from_user.id, media=media_group.build())
    await state.update_data(post=media_group)
    await state.set_state(mailingPost.send)
    return msg.answer("Будет рассылаться пост выше, разослать?", reply_markup=sendMailingKey())


@adminRouter.message(mailingPost.post)
async def mailing_postd_page(msg: Message, state: FSM):
    await bot.copy_message(
        chat_id=msg.from_user.id, from_chat_id=msg.from_user.id, message_id=msg.message_id
    )
    await state.update_data(post=msg.message_id)
    await state.set_state(mailingPost.send)
    return msg.answer("Будет рассылаться пост выше, разослать?", reply_markup=sendMailingKey())


@adminRouter.callback_query(mailingPost.send, F.data == "start_spam")
async def start_spam_func(call: CallbackQuery, state: FSM):
    data = await state.get_data()
    await state.clear()
    all_users = await db.get_all_users()
    try:
        data_int = int(data["post"])
        data_type = True
    except:
        data_type = False
    s = 0
    n = 0
    await call.message.edit_text("Рассылка начата, после ее окончания вам придет уведомление")
    for user in all_users:
        try:
            if data_type:
                await bot.copy_message(
                    chat_id=user["_id"], from_chat_id=call.from_user.id, message_id=data_int
                )
            else:
                await bot.send_media_group(chat_id=user["_id"], media=data["post"].build())
            s += 1
        except Exception as e:
            logger.error(e)
            n += 1
    text = (
        f"Рассылка завершена!\n\n"
        f"Всего пользователей: <code>{len(all_users)} чел.</code>\n"
        f"Удалось отправить: <code>{s} сообщений</code>\n"
        f"Не удалось отправить: <code>{n} сообщений</code>"
    )
    await bot.send_message(chat_id=call.from_user.id, text=text)


@adminRouter.callback_query(F.data == "falsespam")
async def falsespam_func(call: CallbackQuery, state: FSM):
    await state.clear()
    await call.message.delete()
    text = (
        "Добро пожаловать в <b>панель администратора!</b>\n\n"
        "<i>Воспользуйтесь кнопками ниже для управления ботом 👇</i>"
    )
    await bot.send_message(chat_id=call.from_user.id, text=text, reply_markup=kbMainAdmin())