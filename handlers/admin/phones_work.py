from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, Message

from data.config import CHAT_ID, ROLES, STATUS_QUEUE, WORK_THREAD_ID
from keyboards.inline.adminkeyinline import (
	activeTicketListKey,
	phonesListWorks,
	startPhoneWork,
	twoFactorCancleWork,
	twoFactorSclet,
	twoFactorSucWork,
	workPanel,
	openWorkPanel,
	sendCodeUser
)
from keyboards.inline.userinlinekey import authUserKey
from loader import *
from states.admin_state import setAuthCode
from utils.misc_func.bot_models import FSM


def phone_default_text(user: dict, info: dict) -> str:
	admin_text = (
		f"📱 Номер телефона: <code>{info['phone_number']}</code>\n"
		f"💻 Статус: {STATUS_QUEUE[info['status']]['name']}\n\n"
		f"👤 Пользователь: <code>{user['full_name']}</code>\n"
		f"👤 Юзернейм: @{user['username']}\n"
		f"🆔: <code>{user['_id']}</code>"
	)
	return admin_text


@adminRouter.callback_query(F.data.startswith("falsenum_"))
async def falsenum_page(call: CallbackQuery, state: FSM):
	_id = int(call.data.split("_")[1])
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	key = twoFactorCancleWork(_id)
	admin_text = phone_default_text(user, info)
	admin_text += "\n❓ Вы уверены, что хотите отменить аренду?"
	return call.message.edit_text(admin_text, reply_markup=key)


@userRouter.callback_query(F.data.startswith("getauthus_"))
async def getauthus_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	await db.update_phone_number_status(int(_id), "wait_auth")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	admin_text = phone_default_text(user, info)
	admin_text += "\n♻️ Пользователь повторно запросил код авторизации"
	await bot.send_message(
		chat_id=info["worker_id"], text=admin_text, reply_markup=workPanel(_id, "wait_auth")
	)
	return call.message.edit_text(f"♻️ Код повторно запрошен для номер <code>{info['phone_number']}</code>")


@adminRouter.callback_query(F.data.startswith("airfalse_"))
async def airfalse_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	text = "Вы уверен что хотите регнуть слет?"
	return call.message.edit_text(text, reply_markup=twoFactorSclet(_id))


@adminRouter.callback_query(F.data.startswith("yfs_"))
async def yfs_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	await db.update_phone_number_status(int(_id), "cancel")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	admin_text = phone_default_text(user, info)
	admin_text += f"\n⚠️ Вы пометили слет для номера <code>{info['phone_number']}</code>"
	user_text = (
		f"⚠️ Аренда вашего номера <code>{info['phone_number']}</code> была отменена из за слета"
	)
	await bot.send_message(chat_id=user["_id"], text=user_text)
	return call.message.edit_text(admin_text)


@userRouter.callback_query(F.data.startswith("falseauth_"))
async def falseauth_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	await db.update_phone_number_status(int(_id), "false_user")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	admin_text = phone_default_text(user, info)
	admin_text += (
		f"\n⚠️ Пользователь отменил сдачу в аренду этого номера <code>{info['phone_number']}</code>"
	)
	user_text = (
		f"⚠️ Аренда вашего номера <code>{info['phone_number']}</code> была отменена до начала работы вами"
	)
	await bot.send_message(chat_id=info["worker_id"], text=admin_text)
	return call.message.edit_text(user_text)


@adminRouter.callback_query(F.data.startswith("tffalsework_"))
async def tffalsework_page(call: CallbackQuery, state: FSM):
	_id = int(call.data.split("_")[1])
	await db.update_phone_number_status(_id, "false")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	admin_text = phone_default_text(user, info)
	admin_text += "\n⚠️ Вы отменили аренду этого номера"
	user_text = (
		f"⚠️ Аренда вашего номера <code>{info['phone_number']}</code> была отменена до начала работы администрацией"
	)
	await bot.send_message(chat_id=user["_id"], text=user_text)
	return call.message.edit_text(admin_text)


@adminRouter.callback_query(F.data.startswith("openwpan_"))
async def openwpan_page(call: CallbackQuery, state: FSM):
	_id = call.data.split("_")[1]
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	admin_text = phone_default_text(user, info)
	return call.message.edit_text(admin_text, reply_markup=workPanel(_id, info["status"]))


@adminRouter.message(F.text == "🗂 Очередь номеров")
async def queue_admin_page(msg: Message, state: FSM):
	list_phones = await db.get_all_numbers_in_queue()
	text = "<b>🗂 Очередь номеров</b>\n\n<i>ℹ️ Выберите номер для работы</i>"
	key = phonesListWorks(list_phones[:5], 0, len(list_phones[:5]), len(list_phones))
	return msg.answer(text, reply_markup=key)


@adminRouter.callback_query(F.data == "phoneworklist")
async def call_queue_admin_page(call: CallbackQuery, state: FSM):
	list_phones = await db.get_all_numbers_in_queue()
	text = "<b>🗂 Очередь номеров</b>\n\n<i>ℹ️ Выберите номер для работы</i>"
	key = phonesListWorks(list_phones[:5], 0, len(list_phones[:5]), len(list_phones))
	return call.message.edit_text(text, reply_markup=key)


@adminRouter.callback_query(F.data.startswith("getphone_"))
async def getphone_page(call: CallbackQuery, state: FSM):
	_id = int(call.data.split("_")[1])
	info = await db.get_queue_info_by_id(_id)
	user = await db.get_user_info(int(info["user_id"]))
	create_at = user["created_at"]
	formatted_date = create_at.strftime("%Y-%m-%d %H:%M")
	text = (
		f"👤 Пользователь: <code>{user['full_name']}</code>\n"
		f"👤 Юзернейм: @{user['username']}\n"
		f"🆔: <code>{user['_id']}</code>\n\n"
		f"⏳ Дата регистрации: <code>{formatted_date}</code>\n\n"
		f"🔐 Роль: <code>{ROLES[user['role']]}</code>\n\n"
		f"👛 Баланс: <code>{user['balance']}$</code>\n\n"
		"▫️▫️▫️▫️▫️▫️▫️▫️▫️\n\n"
		f"📲 Номер телефона: <code>{info['phone_number']}</code>"
	)
	return call.message.edit_text(text, reply_markup=startPhoneWork(_id))


@adminRouter.callback_query(F.data.startswith("startwork_"))
async def startwork_page(call: CallbackQuery, state: FSM):
	_id = int(call.data.split("_")[1])
	await db.update_at_queue(int(_id))
	info = await db.get_queue_info_by_id(_id)
	user = await db.get_user_info(int(info["user_id"]))
	create_at = user["created_at"]
	formatted_date = create_at.strftime("%Y-%m-%d %H:%M")
	text = (
		f"<b>📱 Внимание, настала ваша очередь для номера</b> <code>{info['phone_number']}</code>\n\n"
		"<b>⏳ Ожидайте, в течении 5-ти минут бот отправит вам код, который нужно будет ввести в whatsapp</b>"
	)
	await bot.send_message(user["_id"], text)
	text = phone_default_text(user, info)
	text += "\n<b>Что бы отправить пользователю код для входа воспользуйтесь кнопкой ниже 👇</b>"
	await db.update_phone_number_status(_id, "wait_auth")
	await db.update_woeker_phone(_id, call.from_user.id)
	await call.message.edit_text(
		text=text, message_thread_id=WORK_THREAD_ID, reply_markup=workPanel(_id, "wait_auth")
	)


@adminRouter.callback_query(F.data.startswith("getauthcode_"))
async def getauthcode_page(call: CallbackQuery, state: FSM):
	_id = int(call.data.split("_")[1])
	text = (
		"Введите код авторизации.\n\n"
		"Внимание, после ввода кода он автоматически будет отправлен пользователю\n\n"
		"Так же вы можете вернуться обратно с помощью кнопки ниже"
	)
	key = openWorkPanel(_id)
	await state.set_state(setAuthCode.id_)
	await state.update_data(id_=_id)
	await state.set_state(setAuthCode.code)
	data = await state.get_data()
	return call.message.edit_text(text, reply_markup=key)


@adminRouter.message(StateFilter(setAuthCode.code))
async def set_auth_code_ff(msg: Message, state: FSM):
	code = msg.text
	data = await state.get_data()
	await state.clear()
	text = f"Вы ввели код: <code>{code}</code>\n\nОтправить его пользователю?"
	key = sendCodeUser(data["id_"], code)
	return msg.answer(text, reply_markup=key)


@adminRouter.callback_query(F.data.startswith("sndc|"))
async def send_code_to_user(call: CallbackQuery, state: FSM):
	_, _id, code = call.data.split("|")
	await db.update_phone_number_status(int(_id), "user_auth")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	text = (
		f"Ваш код для входа: <code>{code}</code> по номеру <code>{info['phone_number']}</code>\n\n"
		'После того как введете его нажмите на кнопку "✅ Вошел"'
	)
	await bot.send_message(chat_id=user["_id"], text=text, reply_markup=authUserKey(_id))
	admin_text = phone_default_text(user, info)
	admin_text += (
		"\n⏳ Код отправлен пользователю, ожидайте когда пользователь подтвердит вход в аккаунт\n\n"
		"<i>ℹ️ Если на стороне пользователя возниклик какие либо проблемы вы можете либо начать работу сейчас либо отменить аренду, "
		"для этого воспользуйтесь кнопками ниже 👇</i>"
	)
	return call.message.edit_text(admin_text, reply_markup=workPanel(_id, "user_auth"))


@userRouter.callback_query(F.data.startswith("sucauth_"))
async def sucauth_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	_id = int(_id)
	await db.update_phone_number_status(_id, "in_proccess")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	user_text = (
		"✅ Готово! По окончнию аренды вам придет уведомление и на баланс придет начисление, ожидайте ⏳"
	)
	await call.message.edit_text(user_text)
	admin_text = phone_default_text(user, info)
	admin_text += "\n✅ Пользователь подтвердил вход, вы можете работать"
	await bot.send_message(
		chat_id=info["worker_id"], text=admin_text, reply_markup=workPanel(_id, "in_proccess")
	)


@adminRouter.callback_query(F.data.startswith("sucwork_"))
async def sucwork_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	admin_text = phone_default_text(user, info)
	admin_text += "\n❓ Вы уверены что хотите произвести выплату?"
	key = twoFactorSucWork(_id)
	return call.message.edit_text(admin_text, reply_markup=key)


@adminRouter.callback_query(F.data.startswith("tfsucwork_"))
async def twofactor_page(call: CallbackQuery, state: FSM):
	_, _id = call.data.split("_")
	settings = await db.get_settings()
	amount_pay = settings["amount_pay"]
	info = await db.get_queue_info_by_id(int(_id))
	user = await db.get_user_info(int(info["user_id"]))
	worker_id = int(info["worker_id"])
	up_balance = await db.update_amount_user(user["_id"], float(amount_pay))
	if up_balance["status"]:
		await db.create_transactions(user["_id"], float(amount_pay), "replenishment")
		if user["refferer"] is not None:
			amount_ref = round(float(amount_pay * (float(settings["referal_procent"]) / 100)), 2)
			await db.update_amount_user(int(user["refferer"]), amount_ref)
			await db.create_transactions(user["refferer"], float(amount_pay), "refferal")
			text_red = (
				f"<b>🤝 Выплата за реферела</b>\n\n"
				f"👛 Ваш баланс был пополнен на <code>{amount_ref}$</code>"
			)
			await bot.send_message(chat_id=user["refferer"], text=text_red)
		await db.update_phone_number_status(int(_id), "done")
		admin_text = phone_default_text(user, info)
		admin_text += (
			"\n✅ Номер успешно обработан, пользователю отправлено уведомление о начислении средств!"
		)
		user_text = (
			f"✅ Ваш номер <code>{info['phone_number']}</code> был успешно обработан!\n"
			f"👛 Ваш баланс: <code>{up_balance['new_amount']}$</code>"
		)
		await bot.send_message(chat_id=user["_id"], text=user_text)
		await db.update_at_queue(int(_id))
		return call.message.edit_text(admin_text, reply_markup=None)
	else:
		msg_error = up_balance["error"]
		return call.answer(msg_error, True)


@adminRouter.message(F.text == "▶️ Активные заявки")
async def active_ticket_page(msg: Message, state: FSM):
	active_list = await db.get_all_queue_active()
	active_list.reverse()
	key = activeTicketListKey(active_list[:5], 0, len(active_list[:5]), len(active_list))
	text = (
		"<b>▶️ Активные заявки</b>\n\n"
		"Здесь вы можете открыть активную заявку если вдруг вы ее потеряли"
	)
	return msg.answer(text, reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_gp_next_"))
async def list_payments_func_next(call: CallbackQuery, state: FSM):
	step = int(call.data.replace("list_gp_next_", ""))
	await state.clear()
	active_list = await db.get_all_queue_active()
	active_list.reverse()
	if len(active_list[step : step + 5]) == 0:
		await call.answer("Это последняя страница", True)
	else:
		key = activeTicketListKey(
			active_list[step : step + 5], step, len(active_list[: step + 5]), len(active_list)
		)
		await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_gp_back_"))
async def list_payments_page_back(call: CallbackQuery, state: FSM):
	step = int(call.data.replace("list_gp_back_", ""))
	if step == 0:
		await call.answer("Это была последняя страница", True)
	else:
		await state.clear()
		active_list = await db.get_all_transactions()
		active_list.reverse()
		key = activeTicketListKey(
			active_list[step - 5 : step], step - 5, len(active_list[:step]), len(active_list)
		)
		await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_pl_next_"))
async def list_payments_l_func_next(call: CallbackQuery, state: FSM):
	step = int(call.data.replace("list_pl_next_", ""))
	await state.clear()
	active_list = await db.get_all_numbers_in_queue()
	if len(active_list[step : step + 5]) == 0:
		await call.answer("Это последняя страница", True)
	else:
		key = phonesListWorks(
			active_list[step : step + 5], step, len(active_list[: step + 5]), len(active_list)
		)
		await call.message.edit_reply_markup(reply_markup=key)


@userRouter.callback_query(F.data.startswith("list_pl_back_"))
async def list_payments_l_page_back(call: CallbackQuery, state: FSM):
	step = int(call.data.replace("list_pl_back_", ""))
	if step == 0:
		await call.answer("Это была последняя страница", True)
	else:
		await state.clear()
		active_list = await db.get_all_numbers_in_queue()
		key = phonesListWorks(
			active_list[step - 5 : step], step - 5, len(active_list[:step]), len(active_list)
		)
		await call.message.edit_reply_markup(reply_markup=key)