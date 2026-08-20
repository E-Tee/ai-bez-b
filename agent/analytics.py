"""Аналитика: посты и метрики в data/posts.json."""
import json
import os
from datetime import date, timedelta
from agent.vk import vk

PATH = os.path.join("data", "posts.json")


def _load():
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(d):
    os.makedirs("data", exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def save_post(post_id, headline):
    d = _load()
    d[str(post_id)] = {"day": str(date.today()), "headline": headline[:80],
                       "views": 0, "likes": 0, "comments": 0, "shares": 0}
    _save(d)


def refresh():
    gid = int(os.getenv("VK_GROUP_ID"))
    d = _load()
    for pid, rec in d.items():
        try:
            res = vk("stats.get", post_ids=f"-{gid}_{pid}")
        except Exception as e:
            print("[analytics]", e)
            continue
        if not res:
            continue
        s = res[0]
        fb = s.get("feedback", {}) or {}
        rec.update(views=(s.get("visitors", {}) or {}).get("views", 0),
                   likes=fb.get("likes", 0), comments=fb.get("comments", 0),
                   shares=fb.get("shares", 0))
    _save(d)


def week_report():
    d = _load()
    week = str(date.today() - timedelta(days=7))
    rows = [(r["headline"], r["views"], r["likes"], r["comments"], r["shares"])
            for r in d.values() if r["day"] >= week]
    rows.sort(key=lambda x: -x[2])
    if not rows:
        return "На неделе тишина: агент копил силы."
    lines = ["Посты за неделю:"]
    for h, v, l, cm, sh in rows:
        lines.append(f"- {h} | просмотры {v}, лайки {l}, комменты {cm}, репосты {sh}")
    lines.append(f"Топ недели: {rows[0][0]}")
    return "\n".join(lines)