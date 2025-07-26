from utils.postgres_db import DB

db_host = "localhost"
db_port = 5432
db_user = "postgres"
db_passwd = "123"
db_name = "postgres"

db = DB(db_host, db_port, db_user, db_passwd, db_name)

TOKEN = "8336658896:AAFR7JViR38cpzAm6cSj2i8fBaHfARpkWW4" 
DOMAIN = ""
ADMIN = [973816744]
BOT_TIMEZONE = "Europe/Moscow"

NAME_PROJECT = 'wazupp'
CHAT_ID = -1002822480963
WORK_THREAD_ID = -1002822480963
PAYMENT_THREAD_ID = -1002822480963

STATUS_TYPE = {
    "success": "выполнено",
    "close": "отменен",
    "proccess": "в процессе",
}

ROLES = {
    "provider": "оператор",
    "admin": "администратор",
    "user": "пользователь",
    "owner": "главный администратор",
    "ban": "бан",
}

STATUS_QUEUE = {
    "in_queue": {"name": "в очереди", "symbol": "⏳"},
    "wait_auth": {"name": "ожидание кода подтверждения", "symbol": "📱"},
    "user_auth": {"name": "ожидание входа на стороне пользователя", "symbol": "📱"},
    "in_proccess": {"name": "в процессе", "symbol": "♻️"},
    "start": {"name": "взято администратором", "symbol": "▶️"},
    "done": {"name": "успешно", "symbol": "✅"},
    "cancel": {"name": "слет", "symbol": "❌"},
    "deleted": {"name": "удален", "symbol": "🗑"},
    "false": {"name": "отмена до начала аренды", "symbol": "❌"},
    "false_user": {"name": "отменено пользователем", "symbol": "❌"},
}

STATUS_TRANSACTIONS = {
    "replenishment": {"name": "пополнение", "symbol": "✅"},
    "refferal": {"name": "реферальная выплата", "symbol": "✅"},
    "wait_withdraft": {"name": "ожидание выода средств", "symbol": "⏳"},
    "finish_withdraft": {"name": "успешный вывод", "symbol": "✅"},
    "false_withdraft": {"name": "отмена вывода", "symbol": "❌"},
}
