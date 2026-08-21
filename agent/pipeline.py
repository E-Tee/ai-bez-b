"""Полный цикл: тема -> текст -> критик -> картинка -> публикация."""
import os
from agent.llm import ask
from agent.image import get_image
from agent.vk import publish

WRITER_SYS = ("Ты писатель паблика «ИИ просто и без затей». Пиши просто и живо, "
              "без мата, без обещаний дохода, сложные слова объясняй метафорами. "
              "5-10 предложений.")


def run(do_publish=True):
    # 1. Тема
    plan = ask("planner",
               "Выбери рубрику и тему поста. Рубрики: словарь (термин на пальцах), "
               "дневник (как собирается агент), факап, цены, миф/реальность. "
               "Ответ: РУБРИКА | ТЕМА",
               "Ты контент-планёр паблика про ИИ для новичков.")
    print("[plan]", plan)

    # 2. Текст
    text = ask("writer", f"Напиши пост. План: {plan}", WRITER_SYS)

    # 3. Критик, одна правка максимум
    verdict = ask("critic",
                  f"Проверь пост для новичков: без мата, без обещаний дохода, приветствие должно начинаться с ИИ агент на связи"
                  f"без терминов без объяснения. Ответ: OK или FIX: причина.\n\n{text}",
                  "Ты строгий редактор паблика для новичков.")
    logger.info(f"[critic] {verdict}")
    
    # Более гибкий парсинг вердикта
    verdict_upper = verdict.strip().upper()
    verdict_lower = verdict.lower()
    if verdict_upper.startswith("FIX") or "fix" in verdict_lower:
        # Извлекаем причину после FIX: или просто используем весь текст
        reason = verdict.split(":", 1)[1].strip() if ":" in verdict else verdict
        text = ask("writer", f"Перепиши с учётом: {reason}. Было: {text}", WRITER_SYS)

    # 4. Картинка
    attach = os.getenv("ATTACH_IMAGES", "false").lower() == "true"
    path = None
    if attach:
        from agent.image import get_image
        prompt = f"иллюстрация для поста про ИИ: {plan}"
        path = get_image(prompt, text)
    
    if do_publish:
        res = publish(text, path if attach else None)
        print("[vk] опубликовано:", res)
        from agent import analytics
        analytics.save_post(res["post_id"], text)
    else:
        print("----- ПОСТ (тест) -----")
        print(text)
    return text