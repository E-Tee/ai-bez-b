"""Бюджет-гард: считает токены/рубли и стопает при дневном лимите."""
import os
import logging
import sqlite3
from datetime import date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "budget.db")

# ЦЕНЫ за 1 млн токенов: (вход, выход) в рублях.
PRICES = {
    "deepseek/deepseek-v4-flash": (15.75, 31.5),   # (вход, выход) ₽ за 1М токенов
    "moonshotai/kimi-k2.7-code": (78, 385),
    "gpt-5.4-mini": (140, 840)
}


class BudgetError(Exception):
    """Дневной лимит пробит. Машина стоп."""


def _conn():
    """Создание подключения к БД с индексом для оптимизации."""
    os.makedirs(DB_DIR, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS spend(
        day TEXT, model TEXT, tok_in INT, tok_out INT, rub REAL)""")
    # Создаём индекс для ускорения запросов по дню
    c.execute("CREATE INDEX IF NOT EXISTS idx_spend_day ON spend(day)")
    return c

def _price(model):
    """Ищет цену и по полному имени, и по короткому (deepseek/x -> x)."""
    if model in PRICES:
        return PRICES[model]
    return PRICES.get(model.split("/")[-1], (0, 0))

def spend(model, tok_in, tok_out):
    """Запись расходов и проверка лимита с уведомлением о 80%."""
    rub_in, rub_out = _price(model)
    rub = tok_in / 1_000_000 * rub_in + tok_out / 1_000_000 * rub_out
    c = _conn()
    c.execute("INSERT INTO spend VALUES (?,?,?,?,?)",
              (str(date.today()), model, tok_in, tok_out, rub))
    c.commit()
    total = c.execute("SELECT SUM(rub) FROM spend WHERE day=?",
                      (str(date.today()),)).fetchone()[0] or 0
    limit = float(os.getenv("DAILY_BUDGET_RUB", 100))
    
    # Уведомление о приближении к лимиту (80%)
    if total > limit * 0.8 and total <= limit:
        logger.warning(f"ВНИМАНИЕ: использовано {total:.2f}₽ из {limit}₽ (80%+)")
    
    c.close()
    
    if total > limit:
        raise BudgetError(f"Лимит {limit}₽/день пробит: уже {total:.2f}₽")
    return rub


def spend_image(model, rub=None):
    """Фиксированная стоимость генерации изображения (токены = 0).

    Цена берётся из переменной IMAGE_PRICE_RUB (по умолчанию 2₽),
    либо передаётся явно. Пишется в ту же таблицу spend, поэтому
    действует тот же дневной лимит DAILY_BUDGET_RUB.
    """
    if rub is None:
        rub = float(os.getenv("IMAGE_PRICE_RUB", 2.0))
    c = _conn()
    c.execute("INSERT INTO spend VALUES (?,?,?,?,?)",
              (str(date.today()), model, 0, 0, rub))
    c.commit()
    total = c.execute("SELECT SUM(rub) FROM spend WHERE day=?",
                      (str(date.today()),)).fetchone()[0] or 0
    limit = float(os.getenv("DAILY_BUDGET_RUB", 100))

    if total > limit * 0.8 and total <= limit:
        logger.warning(f"ВНИМАНИЕ: использовано {total:.2f}₽ из {limit}₽ (80%+)")

    c.close()

    if total > limit:
        raise BudgetError(f"Лимит {limit}₽/день пробит: уже {total:.2f}₽")
    return rub


def today_report():
    c = _conn()
    t = c.execute(
        "SELECT SUM(tok_in)+SUM(tok_out), SUM(rub) FROM spend WHERE day=?",
        (str(date.today()),)).fetchone()
    c.close()
    return f"токенов: {t[0] or 0}, рублей: {t[1] or 0:.2f}"