"""Быстрый отчёт расходов: python report.py"""
import sqlite3

c = sqlite3.connect("data/budget.db")
d = c.execute("SELECT COALESCE(SUM(tok_in+tok_out),0), COALESCE(ROUND(SUM(rub),2),0) "
              "FROM spend WHERE day=(SELECT MAX(day) FROM spend)").fetchone()
t = c.execute("SELECT COALESCE(SUM(tok_in+tok_out),0), COALESCE(ROUND(SUM(rub),2),0) "
              "FROM spend").fetchone()
print(f"Последний активный день: {d[0]} токенов, {d[1]} руб")
print(f"Всего за всё время: {t[0]} токенов, {t[1]} руб")
print("По моделям:")
for model, rub in c.execute("SELECT model, ROUND(SUM(rub),2) FROM spend "
                            "GROUP BY model ORDER BY 2 DESC"):
    print(f"  {model}: {rub} руб")