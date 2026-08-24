"""Цикл: идея -> исследование -> текст -> критик -> редактор -> картинка -> публикация."""
import json
import os
import logging
from datetime import date

from agent.llm import ask
from agent.image import get_image
from agent.vk import publish

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PLAN_PATH = os.path.join(os.path.dirname(__file__), "..", "content_plan.json")

# Пн-Сб — рубрики, Вс — выходной
WEEK = {0: "AI с нуля", 1: "Практика", 2: "Инструмент",
        3: "Словарь", 4: "Эксперимент", 5: "Кейсы"}

WRITER_SYS = ("Ты писатель паблика «ИИ просто и без затей». Живой язык, короткие "
              "предложения, умеренные эмодзи. БЕЗ мата, БЕЗ обещаний дохода, с умеренным юмором. Каждый "
              "термин при первом упоминании — с бытовой метафорой. В конце — крючок "
              "или вопрос к аудитории. Не используй markdown: без звёздочек ** и решёток ##, только обычный текст, абзацы и эмодзи.")

CRITIC_SYS = ("Ты строгий редактор паблика для новичков. Проверь: нет мата; нет "
              "обещаний дохода; нет терминов без объяснения; метафоры понятны. "
              "Ответ: OK или FIX: причина.")

EDITOR_SYS = ("Ты финальный редактор. Убери канцелярит, добавь ритм, проверь крючок. "
              "Не меняй смысл. Верни отредактированный текст целиком.")

RESEARCHER_SYS = ("Ты исследователь. Для темы найди: 1) бытовую метафору, 2) бытовой "
                  "пример, 3) распространённый миф, 4) практическое применение. "
                  "Ответ: МЕТАФОРА: ... ПРИМЕР: ... МИФ: ... ПРИМЕНЕНИЕ: ...")


def load_plan():
    with open(PLAN_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_plan(plan):
    with open(PLAN_PATH, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)


def get_next_topic():
    """Рубрика по дню недели -> первая неопубликованная тема."""
    rubric = WEEK.get(date.today().weekday())
    if rubric is None:
        return None
    for t in load_plan()["topics"].get(rubric, []):
        if not t.get("published"):
            return {"rubric": rubric, "topic": t["topic"], "level": t.get("level", "🟢")}
    return {"rubric": rubric, "topic": None, "level": "🟢"}


def mark_published(topic):
    plan = load_plan()
    for t in plan["topics"].get(topic["rubric"], []):
        if t["topic"] == topic["topic"]:
            t["published"] = True
            t["published_at"] = str(date.today())
    save_plan(plan)


def run(do_publish=True):
    topic = get_next_topic()
    if topic is None:
        logger.info("[plan] воскресенье — выходной")
        return None
    if topic["topic"] is None:
        topic["topic"] = ask("planner",
                             f"Придумай интересную тему для рубрики «{topic['rubric']}», аудитория — новички.",
                             "Ты контент-планёр паблика про ИИ.")
    logger.info(f"[plan] {topic['rubric']} | {topic['topic']}")

    research = ask("planner",
                   f"Тема: {topic['topic']}. Рубрика: {topic['rubric']}.",
                   RESEARCHER_SYS)
    text = ask("writer",
               f"Напиши пост. Тема: {topic['topic']}. Рубрика: {topic['rubric']}. "
               f"Уровень: {topic['level']}. Исследование: {research}",
               WRITER_SYS)

    verdict = ask("critic", f"Проверь пост:\n\n{text}", CRITIC_SYS)
    logger.info(f"[critic] {verdict}")
    if verdict.strip().upper().startswith("FIX"):
        text = ask("writer", f"Перепиши с учётом: {verdict}. Было:\n{text}", WRITER_SYS)

    text = ask("editor", f"Отредактируй текст, сохранив смысл:\n\n{text}", EDITOR_SYS)

    img_prompt = ask("planner",
                     f"Short English prompt for flat vector illustration, no text, "
                     f"no letters. Post topic: {topic['topic']}")
    path = get_image(img_prompt, text)

    if do_publish:
        res = publish(text, path)
        logger.info(f"[vk] опубликовано: {res}")
        mark_published(topic)
        logger.info("[plan] тема помечена. Если запустил локально — "
                    "git add content_plan.json && git commit && git push")
    else:
        print("----- ПОСТ (тест) -----")
        print(text)
    return text