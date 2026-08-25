"""Картинки для постов: gptunnel (платно) -> Pollinations (бесплатно) -> Pillow (0₽).

Цепочка провайдеров:
  1. gptunnel (если IMAGE_PROVIDER=gptunnel или не задан) — генерируем через
     OpenAI-совместимый endpoint /v1/images/generations, те же ключ и base_url,
     что и для LLM (SERVERSPACE_BASE_URL / SERVERSPACE_API_KEY).
  2. Pollinations — бесплатный fallback.
  3. Pillow-открытка — всегда работает, 0₽, последний рубеж.

ID моделей gptunnel настраиваются через IMAGE_MODELS (список через запятую).
Точные ID смотрите в панели провайдера: GET /v1/models.
"""
import os
import base64
import logging
import requests
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

from agent.budget import spend_image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PALETTE = [(255, 122, 0), (24, 38, 63), (46, 160, 90), (155, 48, 255)]

# Разумные значения по умолчанию для gptunnel. Переопределяются через IMAGE_MODELS.
DEFAULT_IMAGE_MODELS = [
    "gpt-image-1.5",
    "gpt-image-1",
    "gpt-image-2",
    "gpt-image-1-mini",
]

# Минимальный размер файла, чтобы не принять пустышку/ошибку за картинку.
MIN_SIZE = 5000


def _image_models():
    """Список моделей gptunnel: из IMAGE_MODELS или значения по умолчанию."""
    raw = os.getenv("IMAGE_MODELS", "")
    if raw.strip():
        return [m.strip() for m in raw.split(",") if m.strip()]
    return list(DEFAULT_IMAGE_MODELS)


def _provider():
    """Основной провайдер: gptunnel | pollinations | template."""
    return os.getenv("IMAGE_PROVIDER", "gptunnel").strip().lower()


def get_image(prompt, text, path="data/post_image.png"):
    """Сгенерировать картинку и сохранить по пути path.

    Цепочка: основной провайдер -> pollinations -> pillow-открытка.
    """
    os.makedirs("data", exist_ok=True)

    provider = _provider()
    if provider == "pollinations":
        try:
            return _pollinations(prompt, path)
        except Exception as e:
            logger.warning(f"[image] pollinations не вывез: {e}")
        return _template(text, path)

    # По умолчанию — gptunnel.
    if provider != "template":
        try:
            return _gptunnel(prompt, path)
        except Exception as e:
            logger.warning(f"[image] gptunnel не вывез, откатываюсь на pollinations: {e}")

    try:
        return _pollinations(prompt, path)
    except Exception as e:
        logger.warning(f"[image] pollinations не вывез: {e}")

    return _template(text, path)


def _gptunnel(prompt, path):
    """Генерация через gptunnel (OpenAI-совместимый клиент из agent.llm)."""
    from agent.llm import client as _gptunnel_client

    size = os.getenv("IMAGE_SIZE", "1024x1024")
    last = None
    for model in _image_models():
        try:
            resp = _gptunnel_client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=size,
            )
            item = resp.data[0]
            if getattr(item, "b64_json", None):
                data = base64.b64decode(item.b64_json)
            elif getattr(item, "url", None):
                data = requests.get(item.url, timeout=120).content
            else:
                raise RuntimeError("в ответе нет данных изображения")

            if len(data) < MIN_SIZE:
                raise RuntimeError(f"картинка слишком маленькая ({len(data)} байт)")

            with open(path, "wb") as f:
                f.write(data)

            # Стоимость генерации учитываем в дневном бюджете.
            spend_image(model)
            logger.info(f"[image] gptunnel ок: {model}")
            return path
        except Exception as e:
            logger.warning(f"[image] {model} не вывез: {e}")
            last = e

    raise RuntimeError(f"Все image-модели gptunnel легли: {last}")


def _pollinations(prompt, path):
    """Бесплатный генератор Pollinations."""
    url = "https://image.pollinations.ai/prompt/" + quote(prompt)
    r = requests.get(url + "?width=1200&height=630&nologo=true", timeout=120)
    if not r.ok or len(r.content) < MIN_SIZE:
        raise RuntimeError(f"неудачный ответ ({r.status_code}, {len(r.content)} байт)")
    with open(path, "wb") as f:
        f.write(r.content)
    print("[image] pollinations ок")
    return path


def _wrap(s, n=30):
    words, cur, out = s.split(), "", []
    for w in words:
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


def _template(text, path):
    """Запаска: цветная карточка с заголовком. Всегда работает, 0₽."""
    img = Image.new("RGB", (1200, 630), PALETTE[hash(text) % len(PALETTE)])
    d = ImageDraw.Draw(img)

    # Кроссплатформенные пути к шрифтам
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
        "/usr/share/fonts/TTF/DejaVuSans.ttf",               # Arch Linux
        "/System/Library/Fonts/Helvetica.ttc",               # macOS
        "C:/Windows/Fonts/arial.ttf",                        # Windows
        "arial.ttf",                                         # fallback
    ]

    font = small = None
    for fp in font_paths:
        try:
            font = ImageFont.truetype(fp, 54)
            small = ImageFont.truetype(fp, 30)
            break
        except Exception:
            continue

    if font is None:
        # Если ничего не найдено, используем дефолтный шрифт PIL
        font = ImageFont.load_default()
        small = font

    title = text.replace("\n", " ").split(". ")[0][:90]
    y = 80
    for line in _wrap(title, 26):
        d.text((60, y), line, fill="white", font=font)
        y += 70
    d.text((60, 560), "ИИ просто и без затей", fill="white", font=small)
    img.save(path)
    print("[image] сработала запаска Pillow")
    return path
