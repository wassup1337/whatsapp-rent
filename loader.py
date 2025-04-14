from data.config import TOKEN, db
from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from typing import Any, Dict, Union
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, F, Router
from services.api_session import *
from utils.misc_func.filters import *

import asyncio, pytz

from middlewares.middleware_users import *
from middlewares.album import *
from middlewares.throttling import *
from utils.postgres_db import DB


userRouter = Router()
userRouter.message.filter(IsPrivate())
userRouter.callback_query.filter(IsPrivate())
userRouter.message.filter(IsPrivate())
userRouter.message.filter(IsBan())
userRouter.callback_query.filter(IsBan())
userRouter.message.middleware(ExistsUserMiddleware())
userRouter.message.middleware(ThrottlingMiddleware())

adminRouter = Router()
adminRouter.callback_query.filter(IsPrivate())
adminRouter.message.filter(IsPrivate())
adminRouter.message.filter(IsAdmin())
adminRouter.callback_query.filter(IsAdmin())
adminRouter.message.middleware(MediaGroupMiddleware())
adminRouter.message.middleware(ExistsUserMiddleware())

captchaRouter = Router()

session = AiohttpSession()
bot_settings = {"session": session, "parse_mode": "HTML"}

bot = Bot(token=TOKEN, **bot_settings)

storage = MemoryStorage()

