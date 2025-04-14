from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def kbMainAdmin() -> ReplyKeyboardMarkup:
    key = [
        [
            KeyboardButton(text="👤 Юзеры"),
            KeyboardButton(text="🗂 Очередь номеров"),
        ],
        [
            KeyboardButton(text="▶️ Активные заявки"),
            KeyboardButton(text="💱 Транзакции"),
        ],
        [
            KeyboardButton(text="📢 Рассылка"),
            KeyboardButton(text="⚙️ Настройки"),
        ],
        [
            KeyboardButton(text="📊 Статистика")
        ]
    ]
    keyReplayAdmin = ReplyKeyboardMarkup(
        keyboard=key,
        resize_keyboard=True,
        input_field_placeholder="Действуйте!"
    )
    return keyReplayAdmin