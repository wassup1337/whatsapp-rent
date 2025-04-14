from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import random


def deletePhoneTwoFactor(_id: int) -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    key.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="queue_list"),
        InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"sucdelph_{_id}")
    )
    return key.as_markup()


def authUserKey(_id: int) -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    key.row(
        InlineKeyboardButton(text="✅ Вошел", callback_data=f"sucauth_{_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data=f"falseauth_{_id}")
    )
    key.row(
        InlineKeyboardButton(text="♻️ Запросить код повторно", callback_data=f"getauthus_{_id}")
    )
    return key.as_markup()


def historyPhoneNumberPagination(
    phoneList: list[dict], start_count: int = 0, step_count: int = 0, allPhones: int = 0
) -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    for item in phoneList:
        name = f"{item['phone_number']}"
        key.row(InlineKeyboardButton(text=name, callback_data=f"open_ph_h_{item['_id']}"))
    key.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_hpn_back_{start_count}"),
        InlineKeyboardButton(text=f"{step_count}/{allPhones}", callback_data="kkkk"),
        InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_hpn_next_{step_count}")
    )
    key.row(InlineKeyboardButton(text="◀️ Назад", callback_data="backMainMenu"))
    return key.as_markup()


def queuePagination(
    phoneList: list[dict], start_count: int = 0, step_count: int = 0, allPhones: int = 0
) -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    for item in phoneList:
        name = f"{item['phone_number']}"
        key.row(
            InlineKeyboardButton(text=name, callback_data=f"open_ph_q_{item['_id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"delph_{item['_id']}")
        )
    key.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list_ph_back_{start_count}"),
        InlineKeyboardButton(text=f"{step_count}/{allPhones}", callback_data="kkkk"),
        InlineKeyboardButton(text="Вперед ➡️", callback_data=f"list_ph_next_{step_count}")
    )
    key.row(InlineKeyboardButton(text="◶️ Назад", callback_data="backMainMenu"))
    return key.as_markup()


def mainKeyInline() -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    key.row(
        InlineKeyboardButton(text="📲 Сдать номер", callback_data="number_rent"),
        InlineKeyboardButton(text="👛 Вывод средств", callback_data="withdraft")
    )
    key.row(
        InlineKeyboardButton(text="📄 Очередь", callback_data="queue_list"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="statistic")
    )
    key.row(
        InlineKeyboardButton(text="👤 Реферальная система", callback_data="referal_system")
    )
    key.row(
        InlineKeyboardButton(text="🗂 История номеров", callback_data="number_history")
    )
    return key.as_markup()


def referalKeyInline(url: str) -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    key.row(InlineKeyboardButton(text="📢 Поделиться", url=f"tg://msg_url?url={url}"))
    key.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="backMainMenu"))
    return key.as_markup()


def capthcaKeyUser() -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    emojis = [
        {"photo": "dolphin.jpg", "emoji": "🐳"},
        {"photo": "lucky.jpg", "emoji": "🍀"},
        {"photo": "star.jpg", "emoji": "🌟"},
        {"photo": "basket.jpg", "emoji": "🏀"},
        {"photo": "coub.jpg", "emoji": "🎲"},
        {"photo": "rocket.jpg", "emoji": "🚀"},
    ]
    random.shuffle(emojis)
    for item in emojis:
        data = item["photo"].replace(".jpg", "")
        key.button(text=item["emoji"], callback_data=f"capt_{data}")
    key.adjust(3)
    return key.as_markup()


def reluseKeyUser() -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    key.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="backMainMenu"))
    return key.as_markup()


def refferalKey(ref_url: str) -> InlineKeyboardMarkup:
    key = InlineKeyboardBuilder()
    key.row(InlineKeyboardButton(text="↗️ Поделиться", url=f"tg://msg_url?url={ref_url}"))
    key.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="backMainMenu"))
    return key.as_markup()