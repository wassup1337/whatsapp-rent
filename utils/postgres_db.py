import asyncpg
import pytz
from asyncpg import Pool, Record
from datetime import datetime, timedelta
from typing import List, Optional
from loguru import logger


class DictRecord(Record):
    def __getitem__(self, key):
        value = super().__getitem__(key)
        if isinstance(value, Record):
            return DictRecord(value)
        return value

    def to_dict(self):
        return self._convert_records_to_dicts(dict(super().items()))

    def _convert_records_to_dicts(self, obj):
        if isinstance(obj, dict):
            return {k: self._convert_records_to_dicts(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_records_to_dicts(item) for item in obj]
        elif isinstance(obj, Record):
            return dict(obj)
        return obj

    def __repr__(self):
        return str(self.to_dict())


class DB:
    def __init__(self, host: str, port: int, user: str, password: str, db_name: str):
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._db_name = db_name

    async def close(self):
        await self.db.close()
        logger.warning("Соединение с базой данных завершено!")

    async def setup(self):
        try:
            self.db = await asyncpg.create_pool(
                host=self._host,
                port=self._port,
                user=self._user,
                password=self._password,
                database=self._db_name,
                record_class=DictRecord,
                init=self._init_database,
            )
            logger.success("Соединение с базой данных успешно установлено!")
        except Exception as e:
            logger.error(f"Ошибка при подключении к базе данных: {e}")
            raise ValueError("Кажется, при подключении к базе данных возникла ошибка, из-за которой бот не может начать работу :(")

    @staticmethod
    async def _init_database(db: asyncpg.Connection):
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users(
                _id BIGINT NOT NULL PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                refferer BIGINT,
                role TEXT DEFAULT 'user',
                balance REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT now(),
                updated_at TIMESTAMP DEFAULT now()
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions(
                _id SERIAL PRIMARY KEY,
                user_id BIGINT,
                amount REAL,
                status TEXT,
                pay_url TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings(
                _id BIGINT PRIMARY KEY,
                work BOOLEAN DEFAULT False,
                amount_pay REAL DEFAULT 10,
                referal_procent REAL DEFAULT 5
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS queue(
                _id SERIAL PRIMARY KEY,
                user_id BIGINT,
                phone_number TEXT,
                worker_id BIGINT DEFAULT NULL,
                status TEXT DEFAULT 'in_queue',
                code_auth TEXT DEFAULT NULL,
                update_at TIMESTAMP DEFAULT now(),
                created_at TIMESTAMP DEFAULT now()
            )
        """)
        await db.execute("SET TIME ZONE 'Europe/Moscow'")

    async def get_all_hold(self):
        return await self.db.fetch("SELECT * FROM transactions WHERE status = 'wait_withdraft'")

    async def get_queue_user_by_status(self, user_id: int, status: str):
        return await self.db.fetch("SELECT * FROM queue WHERE user_id = $1 AND status = $2", user_id, status)

    async def update_transaction_status(self, _id: int, status: str, pay_url: Optional[str] = None):
        await self.db.execute("UPDATE transactions SET status = $1 WHERE _id = $2", status, _id)
        if pay_url is not None:
            await self.db.execute("UPDATE transactions SET pay_url = $1 WHERE _id = $2", pay_url, _id)

    async def get_transaction(self, _id: int):
        return await self.db.fetchrow("SELECT * FROM transactions WHERE _id = $1", _id)

    async def create_transactions(self, user_id: int, amount: float, status: str):
        try:
            add = await self.db.fetchval(
                "INSERT INTO transactions (user_id, amount, status) VALUES ($1, $2, $3) RETURNING _id",
                user_id, amount, status
            )
            return add
        except Exception as e:
            logger.exception(e)
            return None

    async def get_all_transactions_user(self, user_id: int):
        return await self.db.fetch("SELECT * FROM transactions WHERE user_id = $1", user_id)

    async def get_hold_balance_user(self, user_id: int, status: str):
        return await self.db.fetch("SELECT * FROM transactions WHERE user_id = $1 AND status = $2", user_id, status)

    async def update_amount_user(self, _id: int, amount: float):
        try:
            user_info = await self.get_user_info(_id)
            amount_now = user_info["balance"]
            new_amount = round(float(amount_now + amount), 2)
            await self.db.execute("UPDATE users SET balance = $1 WHERE _id = $2", new_amount, _id)
            return {"status": True, "new_amount": new_amount}
        except Exception as e:
            logger.exception(e)
            return {"status": False, "error": str(e)}

    async def update_woeker_phone(self, _id: int, worker_id: int):
        await self.db.execute("UPDATE queue SET worker_id = $1 WHERE _id = $2", worker_id, _id)

    async def get_all_queue_by_user_id(self, user_id: int):
        return await self.db.fetch("SELECT * FROM queue WHERE user_id = $1", user_id)

    async def get_all_queue_active(self):
        return await self.db.fetch("SELECT * FROM queue WHERE status IN ('wait_auth', 'user_auth', 'in_proccess', 'start')")

    async def get_all_queue(self):
        return await self.db.fetch("SELECT * FROM queue")

    async def get_all_numbers_in_queue(self):
        return await self.db.fetch("SELECT * FROM queue WHERE status = 'in_queue'")

    async def update_phone_number_status(self, _id: int, status: str):
        try:
            await self.db.execute("UPDATE queue SET status = $1 WHERE _id = $2", status, _id)
            return True
        except Exception as e:
            logger.exception(e)
            return False

    async def get_queue_info_by_id(self, _id: int):
        return await self.db.fetchrow("SELECT * FROM queue WHERE _id = $1", _id)

    async def get_in_queue_user(self, user_id: int):
        return await self.db.fetch("SELECT * FROM queue WHERE user_id = $1 AND status = 'in_queue'", user_id)

    async def get_all_phone_numbers_user(self, user_id: int):
        return await self.db.fetch("SELECT * FROM queue WHERE user_id = $1", user_id)

    async def update_percent(self, percent: float):
        await self.db.execute("UPDATE settings SET referal_procent = $1", percent)

    async def update_pay(self, amount: float):
        await self.db.execute("UPDATE settings SET amount_pay = $1", amount)

    async def get_phones_in_queue_user(self, user_id: int):
        return await self.db.fetch("SELECT * FROM queue WHERE user_id = $1 AND status = 'in_queue'", user_id)

    async def update_at_queue(self, _id: int):
        await self.db.execute("UPDATE queue SET update_at = CURRENT_TIMESTAMP WHERE _id = $1", _id)

    async def add_phone_number(self, user_id: int, phone_number: str) -> dict:
        try:
            now_number_in_queue = await self.db.fetch(
                "SELECT * FROM queue WHERE phone_number = $1 AND status = 'in_queue'", phone_number
            )
            if now_number_in_queue:
                return {"status": False, "msg": "этот номер прямо сейчас находится в очереди"}
            phone_history = await self.db.fetchrow(
                "SELECT * FROM queue WHERE phone_number = $1 ORDER BY update_at DESC LIMIT 1", phone_number
            )
            if phone_history is None:
                add = await self.db.fetchval(
                    "INSERT INTO queue (user_id, phone_number) VALUES ($1, $2) RETURNING _id", user_id, phone_number
                )
                if not add:
                    return {"status": False, "msg": "не удалось добавить номер в базу данных"}
                position = await self.db.fetchval(
                    "SELECT COUNT(*) + 1 AS position FROM queue WHERE status IN ('in_queue', 'process') "
                    "AND (_id < $1 OR (update_at = (SELECT update_at FROM queue WHERE _id = $1) AND _id < $1))", add
                )
                return {"status": True, "msg": position}
            dt = phone_history["update_at"]
            moscow_tz = pytz.timezone("Europe/Moscow")
            dt_moscow = moscow_tz.localize(dt)
            current_time_moscow = datetime.now(moscow_tz)
            if current_time_moscow - dt_moscow < timedelta(hours=24):
                return {"status": False, "msg": "с прошлого добавления этого номера телефона прошло меньше 24 часов"}
            add = await self.db.fetchval(
                "INSERT INTO queue (user_id, phone_number) VALUES ($1, $2) RETURNING _id", user_id, phone_number
            )
            if not add:
                return {"status": False, "msg": "не удалось добавить номер в базу данных"}
            position = await self.db.fetchval(
                "SELECT COUNT(*) + 1 AS position FROM queue WHERE status IN ('in_queue', 'process') "
                "AND (_id < $1 OR (update_at = (SELECT update_at FROM queue WHERE _id = $1) AND _id < $1))", add
            )
            return {"status": True, "msg": position}
        except Exception as e:
            logger.exception(e)
            return {"status": False, "msg": "не удалось добавить номер в базу данных"}

    async def get_all_transactions(self):
        return await self.db.fetch("SELECT * FROM transactions")

    async def delete_transaction(self, uniq_id: int):
        await self.db.execute("DELETE FROM transactions WHERE uniq_id = $1", uniq_id)
        return True

    async def get_success_transactions_user(self, user_id: int) -> List[dict]:
        return await self.db.fetch(
            "SELECT * FROM transactions WHERE status = 'success' AND pay_status = 'not_payed' AND user_id = $1", user_id
        )

    async def update_pay_status(self, user_id: int):
        await self.db.execute(
            "UPDATE transactions SET pay_status = 'payed' WHERE user_id = $1 AND status = 'success'", user_id
        )
        return await self.get_user_info(user_id)

    async def update_work_status(self, user_id: int, status: bool) -> dict:
        await self.db.execute("UPDATE users SET work_status = $1 WHERE _id = $2", status, user_id)
        return await self.get_user_info(user_id)

    async def get_settings(self) -> dict:
        response = await self.db.fetchrow("SELECT * FROM settings WHERE _id = 1")
        return response.to_dict()

    async def add_settings(self):
        try:
            await self.db.execute("INSERT INTO settings (_id) VALUES ($1)", 1)
            return True
        except Exception as e:
            logger.warning(e)
            return False

    async def update_course(self, coin_name: str, course: float):
        await self.db.execute("UPDATE liquid SET course = $1 WHERE coin_name = $2", course, coin_name)

    async def get_coin_info(self, coin_name: str) -> dict:
        response = await self.db.fetchrow("SELECT * FROM liquid WHERE coin_name = $1", coin_name)
        return response.to_dict()

    async def get_all_coins(self) -> List[dict]:
        return await self.db.fetch("SELECT * FROM liquid")

    async def update_pay_in_user(self, user_id: int, pay_in: str) -> dict:
        await self.db.execute("UPDATE users SET pay_in = $1 WHERE _id = $2", pay_in, user_id)
        return await self.get_user_info(user_id)

    async def add_coins(self, coin_name: str):
        try:
            await self.db.execute("INSERT INTO liquid (coin_name) VALUES ($1)", coin_name)
        except Exception as e:
            logger.error(e)

    async def add_transaction(
        self,
        uniq_id: int,
        user_id: int,
        from_chat_id: int,
        from_chat_message_id: int,
        to_chat_id: int,
        to_thread_id: int,
        to_chat_message_id: int,
        amount: int,
        procent: int,
        clear_amount: int,
    ):
        await self.db.execute(
            "INSERT INTO transactions(uniq_id, user_id, from_chat_id, from_chat_message_id, to_chat_id, "
            "to_thread_id, to_chat_message_id, amount, procent, clear_amount) "
            "VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)",
            uniq_id, user_id, from_chat_id, from_chat_message_id, to_chat_id,
            to_thread_id, to_chat_message_id, amount, procent, clear_amount
        )

    async def success_payment_transaction(
        self, uniq_id: int, crypto_amount_ltc: float, crypto_amount_btc: float, pay_in: str, status: str
    ):
        await self.db.execute(
            "UPDATE transactions SET crypto_amount_ltc = $1, crypto_amount_btc = $2, pay_in = $3, status = $4 WHERE uniq_id = $5",
            crypto_amount_ltc, crypto_amount_btc, pay_in, status, uniq_id
        )

    async def get_transaction_uniq_id(self, uniq_id: int) -> dict:
        response = await self.db.fetchrow("SELECT * FROM transactions WHERE uniq_id = $1", uniq_id)
        return response.to_dict()

    async def get_admins_role(self) -> List[dict]:
        response = await self.db.fetch("SELECT * FROM users WHERE role = 'admin'")
        return response

    async def add_new_chat(self, chat_id: int, chat_name: str) -> dict:
        if not await self.chat_admin_existence(chat_id):
            response = await self.db.fetchrow(
                "INSERT INTO chats(chat_id, chat_name) VALUES($1, $2) RETURNING *", chat_id, chat_name
            )
            return response.to_dict()
        return {"double": True}

    async def get_chat_info(self, chat_id: int) -> dict:
        response = await self.db.fetchrow("SELECT * FROM chats WHERE chat_id = $1", chat_id)
        return response.to_dict() if response else {}

    async def get_chat_info_uniq_id(self, _id: int) -> dict:
        response = await self.db.fetchrow("SELECT * FROM chats WHERE _id = $1", _id)
        return response.to_dict() if response else {}

    async def get_all_chats_admin(self, dict_: bool = False) -> List[dict]:
        response = await self.db.fetch("SELECT * FROM chats")
        return response

    async def chat_admin_existence(self, chat_id: int) -> bool:
        return await self.db.fetchval("SELECT EXISTS(SELECT 1 FROM chats WHERE chat_id=$1)", chat_id)

    async def get_user_info(self, user_id: int) -> dict:
        response = await self.db.fetchrow("SELECT * FROM users WHERE _id = $1", user_id)
        return response.to_dict() if response else {}

    async def get_user_info_dict(self, user_id: int) -> dict:
        response = await self.db.fetchrow("SELECT * FROM users WHERE _id = $1", user_id)
        return response

    async def get_all_admin_db(self):
        return await self.db.fetch("SELECT * FROM users WHERE role = 'admin' OR role = 'owner'")

    async def add_user(self, user_id: int, username: str, full_name: str, refferer: Optional[str]) -> dict:
        if not await self.user_existence(user_id):
            response = await self.db.fetchrow(
                "INSERT INTO users(_id, username, full_name, refferer) VALUES($1, $2, $3, $4) RETURNING *",
                user_id, username, full_name, refferer
            )
            return response.to_dict()
        await self.update_user_activity(user_id)
        return await self.get_user_info(user_id)

    async def update_user_role(self, user_id: int, role: str) -> dict:
        await self.db.execute("UPDATE users SET role = $1 WHERE _id = $2", role, user_id)
        return await self.get_user_info(user_id)

    async def update_connect_chat_id(self, user_id: int, connect_chat_id: int) -> dict:
        await self.db.execute("UPDATE users SET connect_chat_id = $1 WHERE _id = $2", connect_chat_id, user_id)
        return await self.get_user_info(user_id)

    async def update_connect_chat_clent(self, user_id: int, connect_chat_id: int, thread_id: int) -> dict:
        await self.db.execute(
            "UPDATE users SET connect_chat_id = $1, thread_id = $2 WHERE _id = $3",
            connect_chat_id, thread_id, user_id
        )
        return await self.get_user_info(user_id)

    async def update_user_procent(self, user_id: int, procent_work: int) -> dict:
        await self.db.execute("UPDATE users SET procent_work = $1 WHERE _id = $2", procent_work, user_id)
        return await self.get_user_info(user_id)

    async def update_user_requisits(self, user_id: int, requisits: str) -> dict:
        await self.db.execute("UPDATE users SET requisits = $1 WHERE _id = $2", requisits, user_id)
        return await self.get_user_info(user_id)

    async def get_user_is_thread(self, chat_id: int, thread_id: int):
        response = await self.db.fetchrow(
            "SELECT * FROM users WHERE connect_chat_id = $1 AND thread_id = $2", chat_id, thread_id
        )
        return response.to_dict() if response else {}

    async def update_chat_user(self, user_id: int, chat_id: int, chat_name: str) -> dict:
        await self.db.execute(
            "UPDATE users SET chat_id = $1, chat_name = $2 WHERE _id = $3", chat_id, chat_name, user_id
        )
        return await self.get_user_info(user_id)

    async def update_user_activity(self, user_id: int):
        if await self.user_existence(user_id):
            await self.db.execute("UPDATE users SET updated_at = $1 WHERE _id = $2", datetime.now(), user_id)

    async def user_existence(self, user_id: int) -> bool:
        return await self.db.fetchval("SELECT EXISTS(SELECT 1 FROM users WHERE _id=$1)", user_id)

    async def get_all_users(self) -> List[dict]:
        return await self.db.fetch("SELECT * FROM users")

    async def get_provider_users(self, provider_chat_id: int) -> List[dict]:
        return await self.db.fetch("SELECT * FROM users WHERE connect_chat_id = $1", provider_chat_id)

    async def negative_transacitions(
        self,
        uniq_id: int,
        user_id: int,
        from_chat_id: int,
        from_chat_message: int,
        to_chat_id: int,
        to_chat_message: int = 0,
        amount: int = 0,
        procent: int = 0,
        clear_amount: int = 0,
        crypto_amount_ltc: float = 0,
        crypto_amount_btc: float = 0,
        pay_in: Optional[str] = None,
        status: str = "success",
    ):
        await self.db.execute(
            "INSERT INTO transactions(uniq_id, user_id, from_chat_id, from_chat_message_id, to_chat_id, "
            "to_chat_message_id, amount, procent, clear_amount, crypto_amount_ltc, crypto_amount_btc, pay_in, status) "
            "VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)",
            uniq_id, user_id, from_chat_id, from_chat_message, to_chat_id, to_chat_message, amount, procent,
            clear_amount, crypto_amount_ltc, crypto_amount_btc, pay_in, status
        )