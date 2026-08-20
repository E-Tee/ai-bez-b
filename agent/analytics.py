"""Аналитика: копим посты и снимаем метрики ВК."""
import os
import sqlite3
from datetime import date
from agent.vk import vk

DB = os.path.join("data", "analytics.db")


def _conn():
    os.makedirs("data", exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS posts(
        post_id INT PRIMARY KEY, day TEXT, headline TEXT,
        views INT, likes INT, comments INT, shares INT)""")
    return c


def save_post(post_id, headline):
    c = _conn()
    c.execute("INSERT OR IGNORE INTO posts VALUES (?,?,?,?,0,0,0)",
              (post_id, str(date.today()), headline[:80]))
    c.commit()
    c.close()


def refresh():
    """Обновить метрики по всем постам."""
    gid = int(os.getenv("VK_GROUP_ID"))
    c = _conn()
    for (pid,) in c.execute("SELECT post_id FROM posts").fetchall():
        try:
            res = vk("stats.get", post_ids=f"-{gid}_{pid}")
        except Exception as e:
            print("[analytics] ошибка:", e)
            continue
        if not res:
            continue
        s = res[0]
        fb = s.get("feedback", {}) or {}
        c.execute("UPDATE posts SET views=?, likes=?, comments=?, shares=? WHERE post_id=?",
                  ((s.get("visitors", {}) or {}).get("views", 0),
                   fb.get("likes", 0), fb.get("comments", 0),
                   fb.get("shares", 0), pid))
    c.commit()
    c.close()


def week_report():
    c = _conn()
    rows = c.execute("""SELECT headline, views, likes, comments, shares
        FROM posts WHERE day >= date('now','-7 days')
        ORDER BY likes DESC""").fetchall()
    c.close()
    if not rows:
        return "На неделе тишина: агент копил силы."
    lines = ["Посты за неделю:"]
    for h, v, l, cm, sh in rows:
        lines.append(f"- {h} | просмотры {v}, лайки {l}, комменты {cm}, репосты {sh}")
    lines.append(f"Топ недели: {rows[0][0]}")
    return "\n".join(lines)