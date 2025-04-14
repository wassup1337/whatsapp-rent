from aiogram.fsm.state import StatesGroup,State
from typing import Union


class paymentUser(StatesGroup):
    trans_id = State()
    url = State()
    send = State()


class mailingPost(StatesGroup):
    post = State()
    send = State()


class messageUser(StatesGroup):
    user_id = State()
    message = State()
    send = State()


class setAuthCode(StatesGroup):
    id_ = State()
    code = State()



class searchUser(StatesGroup):
    user_info: Union[int, str] = State()
    listing: Union[str, int] = State()
    

class ED(StatesGroup):
    step_ = State()
    post = State()
    text = State()
    media = State()
    keyboard = State()
    time_start = State()
    type_time = State()
    value_time = State()



