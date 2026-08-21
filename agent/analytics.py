"""Аналитика: посты и метрики в data/posts.json."""
import json
import os
import logging
from datetime import date, timedelta
from agent.vk import vk

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PATH = os.path.join("data", "posts.json")
MAX_POSTS_AGE_DAYS = 90  # Ротация: удаляем записи старше 90 дней


def _load():
    if os.path.exists(PATH):
        with open(PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(d):
    os.makedirs("data", exist_ok=True)
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def _rotate_old_posts(data):
    """Удаление записей старше MAX_POSTS_AGE_DAYS дней."""
    cutoff = str(date.today() - timedelta(days=MAX_POSTS_AGE_DAYS))
    old_keys = [k for k, v in data.items() if v.get("day", "") < cutoff]
    for k in old_keys:
        del data[k]
    if old_keys:
        logger.info(f"Ротация: удалено {len(old_keys)} старых записей")
    return data


def save_post(post_id, headline):
    """Сохранение поста с проверкой уникальности."""
    d = _load()
    
    # Проверка уникальности по заголовку (первые 50 символов)
    headline_short = headline[:50]
    for existing in d.values():
        if existing.get("headline", "")[:50] == headline_short:
            logger.warning(f"Пост с похожим заголовком уже существует: {headline_short}")
            return post_id  # Возвращаем ID, но не сохраняем дубликат
    
    d[str(post_id)] = {"day": str(date.today()), "headline": headline[:80],
                       "views": 0, "likes": 0, "comments": 0, "shares": 0}
    _save(d)
    return post_id


def refresh():
    """Обновление метрик постов с ротацией старых записей."""
    gid = int(os.getenv("VK_GROUP_ID"))
    d = _load()
    
    # Ротация старых записей
    d = _rotate_old_posts(d)
    
    for pid, rec in d.items():
        try:
            res = vk("stats.get", post_ids=f"-{gid}_{pid}")
        except Exception as e:
            logger.warning(f"[analytics] ошибка получения метрик для поста {pid}: {e}")
            continue
        if not res:
            continue
        s = res[0]
        fb = s.get("feedback", {}) or {}
        rec.update(views=(s.get("visitors", {}) or {}).get("views", 0),
                   likes=fb.get("likes", 0), comments=fb.get("comments", 0),
                   shares=fb.get("shares", 0))
    _save(d)
    logger.info("[analytics] метрики обновлены")


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