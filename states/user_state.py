from aiogram.fsm.state import StatesGroup,State
from typing import Union

class addPhoneNumber(StatesGroup):
    phone_number: Union[str] = State()

class openUserProfileDeal(StatesGroup):
    user_info: Union[int, str] = State()    