from collections import defaultdict
from aiogram.types import Message

from data.config import STATUS_QUEUE, STATUS_TRANSACTIONS
from loader import *
from utils.misc_func.bot_models import FSM


def calculate_queue_statistics(queue_data, statuses):
    stats = {
        "total_entries": len(queue_data),
        "status_counts": defaultdict(int),
        "user_stats": defaultdict(lambda: {"count": 0, "statuses": defaultdict(int)}),
        "worker_stats": defaultdict(lambda: {"count": 0, "statuses": defaultdict(int)}),
    }
    for entry in queue_data:
        status = entry["status"]
        user_id = entry["user_id"]
        worker_id = entry["worker_id"]
        stats["status_counts"][status] += 1
        stats["user_stats"][user_id]["count"] += 1
        stats["user_stats"][user_id]["statuses"][status] += 1
        if worker_id:
            stats["worker_stats"][worker_id]["count"] += 1
            stats["worker_stats"][worker_id]["statuses"][status] += 1
    for status, data in statuses.items():
        if status in stats["status_counts"]:
            stats["status_counts"][f"{data['symbol']} {data['name']}"] = stats["status_counts"].pop(status)
    return stats


def calculate_statistics(transactions, statuses):
    stats = {
        "total_transactions": len(transactions),
        "total_amount": 0,
        "status_counts": defaultdict(int),
        "user_stats": defaultdict(lambda: {"count": 0, "amount": 0}),
    }
    for transaction in transactions:
        status = transaction["status"]
        amount = transaction["amount"]
        user_id = transaction["user_id"]
        stats["total_amount"] += amount
        stats["status_counts"][status] += 1
        stats["user_stats"][user_id]["count"] += 1
        stats["user_stats"][user_id]["amount"] += amount
    for status, data in statuses.items():
        if status in stats["status_counts"]:
            stats["status_counts"][f"{data['symbol']} {data['name']}"] = stats["status_counts"].pop(status)
    return stats


@adminRouter.message(F.text == "📊 Статистика")
async def admin_statistics_page(msg: Message, state: FSM):
    transactions_list = await db.get_all_transactions()
    hold = await db.get_all_hold()
    sum_hold = sum(row["amount"] for row in hold)
    queue_list = await db.get_all_queue()
    users = await db.get_all_users()
    user_text = (
        f"<b>👤 О пользователях:</b>\n"
        f"Всего юзеров: <code>{len(users)} чел.</code>\n"
        f"Сумма всех балансов: <code>{sum(item['balance'] for item in users)}$</code>\n"
        f"Всего на выводе: <code>{sum_hold}$</code>\n"
    )
    statistics = calculate_statistics(transactions_list, STATUS_TRANSACTIONS)
    queue_statistics = calculate_queue_statistics(queue_list, STATUS_QUEUE)
    user_text += (
        f"\n<b>💱 О транзакциях:</b>\n"
        f"Всего транзакций: {statistics['total_transactions']}\n\n"
        "<b>По статусам:</b>"
    )
    for status, count in statistics["status_counts"].items():
        user_text += f"\n{status}: {count}"
    user_text += f"\n\n<b>📄 Номера:</b>\nВсего записей: {queue_statistics['total_entries']}\n\n<b>По статусам:</b>"
    for status, count in queue_statistics["status_counts"].items():
        user_text += f"\n{status}: {count}"
    return msg.answer(user_text)