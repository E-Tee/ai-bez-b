"""Тест Recraft: две картинки — без референса и с референсом.
Стоит ~14₽ при установленном референсе! Запуск: python test_image.py"""
import os
from dotenv import load_dotenv
load_dotenv()
from agent.image import get_image

PROMPT = ("flat vector illustration, small robot painter holding a brush, "
          "minimal, clean, no text")
TEXT = "Проверка качества Recraft"

ref = os.getenv("GT_STYLE_REF")
print("Референс в .env:", ref or "НЕ задан")

# 1) БЕЗ референса — базовая линия
os.environ.pop("GT_STYLE_REF", None)  # временно убираем, код читает env на лету
p1 = get_image(PROMPT, TEXT, path="data/test_no_ref.png")
print("\nБЕЗ референса:", os.path.abspath(p1))

# 2) С референсом — возвращаем переменную на место
if ref:
    os.environ["GT_STYLE_REF"] = ref
    p2 = get_image(PROMPT, TEXT, path="data/test_ref.png")
    print("С референсом: ", os.path.abspath(p2))
    print("\nОткрой обе картинки и сравни влёт: стиль/палитра/настроение.")
else:
    print("\nGT_STYLE_REF пустой — вставь публичную ссылку на образец в .env, "
          "чтобы увидеть разницу.")