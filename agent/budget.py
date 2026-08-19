"""Бюджет-гард: считает токены/рубли и стопает при дневном лимите."""
import os
import sqlite3
from datetime import date

DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "budget.db")

# ЦЕНЫ за 1 млн токенов: (вход, выход) в рублях.
# ЗАПОЛНИ из тарифов Serverspace! Пока нули — считаем только токены.
PRICES = {
    "deepseek-v4-flash": (0, 0),
    "gpt-5.4-mini": (0, 0),
    "deepseek-v3.2": (0, 0),
}


class BudgetError(Exception):
    """Дневной лимит пробит. Машина стоп."""


def _conn():
    os.makedirs(DB_DIR, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.execute("""CREATE TABLE IF NOT EXISTS spend(
        day TEXT, model TEXT, tok_in INT, tok_out INT, rub REAL)""")
    return c


def spend(model, tok_in, tok_out):
    rub_in, rub_out = PRICES.get(model, (0, 0))
    rub = tok_in / 1_000_000 * rub_in + tok_out / 1_000_000 * rub_out
    c = _conn()
    c.execute("INSERT INTO spend VALUES (?,?,?,?,?)",
              (str(date.today()), model, tok_in, tok_out, rub))
    c.commit()
    total = c.execute("SELECT SUM(rub) FROM spend WHERE day=?",
                      (str(date.today()),)).fetchone()[0] or 0
    c.close()
    limit = float(os.getenv("DAILY_BUDGET_RUB", 100))
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