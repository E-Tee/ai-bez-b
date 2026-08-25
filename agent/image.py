"""Картинки поста: Recraft с брендовым образцом -> Pollinations -> Pillow на фирменном фоне."""
import os
import re
import time
import logging
import requests
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont
from agent.llm import ask
from agent.budget import spend_fixed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Бренд ─────────────────────────────────────────────────────────────
# ВСТАВЬ СВОЙ RAW-АДРЕС: GitHub -> файл в ветке -> кнопка Raw -> скопировать URL
BRAND_BG_URL = "https://raw.githubusercontent.com/E-Tee/ai-bez-b/Fix-post-img/template/brand_bg.png"
BRAND_BG_LOCAL = os.path.join("template", "brand_bg.png")
BRAND_BG_CACHE = os.path.join("data", "brand_bg.png")
BRAND_NAME = "ИИ просто и без затей"
NAVY = (24, 38, 63)      # последний запасной фон
ACCENT = (255, 122, 0)
BRAND_STYLE = ("dark teal-navy background, glowing neon cyan circuit board traces "
               "along the bottom edge, minimal flat vector tech aesthetic, "
               "no text, no letters")

# ── GPTunneL (фотоцех) ────────────────────────────────────────────────
GT_MEDIA = "https://gptunnel.ru/api/v2/media"
GT_MODEL = "recraftv4_1"
GT_MAX_PRICE = 10
GT_POLL_SEC = 5
GT_MAX_WAIT = 180


def _gt(method, url, key, **kw):
    """Запрос к GPTunneL: сначала Bearer, если 401/403 — голый ключ."""
    for h in ({"Authorization": f"Bearer {key}"}, {"Authorization": key}):
        r = requests.request(method, url, headers=h, timeout=30, **kw)
        if r.status_code not in (401, 403):
            return r
    return r


def _translate(prompt):
    """Если в промпте кириллица — переводим на английский (дешёвая страховка)."""
    if not re.search("[а-яё]", prompt, re.I):
        return prompt
    en = ask("planner",
             f"Translate to English, short, no comments: {prompt}",
             "Ты переводчик. Верни только перевод.")
    logger.info("[image] промпт переведён на английский")
    return en.strip()


def _gptunnel(prompt, path):
    """Recraft с брендовым образцом: прайс-чек -> задача -> поллинг -> файл."""
    key = os.getenv("GPTUNNEL_API_KEY")
    if not key:
        raise RuntimeError("Нет GPTUNNEL_API_KEY в .env")

    body = {
        "model": GT_MODEL,
        "prompt": prompt + ". Keep the background and overall look of the reference image",
        "params": {"aspect_ratio": "16:9", "strength": 0.6},
        "inputs": {"image": [BRAND_BG_URL]},
    }

    # 1. Цена ДО заказа
    price = 7
    p = _gt("post", f"{GT_MEDIA}/price", key, json=body)
    if p.ok:
        price = p.json().get("price", price)
        logger.info(f"[image] цена recraft: {price}₽")
    else:
        logger.warning(f"[image] прайс-чек: {p.status_code} {p.text[:200]}")
    if price and price > GT_MAX_PRICE:
        raise RuntimeError(f"recraft {price}₽ выше потолка {GT_MAX_PRICE}₽")

    # 2. Задача (если 16:9 не понял — пробуем без параметра)
    t = _gt("post", f"{GT_MEDIA}/tasks", key, json=body)
    if not t.ok:
        logger.warning(f"[image] tasks: {t.status_code} {t.text[:300]}")
        body.pop("params", None)
        t = _gt("post", f"{GT_MEDIA}/tasks", key, json=body)
    t.raise_for_status()
    tid = t.json().get("id")
    logger.info(f"[image] задача создана: {tid}")

    # 3. Поллинг «готово?»
    waited = 0
    while waited < GT_MAX_WAIT:
        time.sleep(GT_POLL_SEC)
        waited += GT_POLL_SEC
        g = _gt("get", f"{GT_MEDIA}/tasks/{tid}", key)
        g.raise_for_status()
        task = g.json()
        st = task.get("status")
        if st == "done":
            url = task["result"][0]["url"]
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            with open(path, "wb") as f:
                f.write(r.content)
            spend_fixed(GT_MODEL, float(price or 7))
            return path
        if st == "failed":
            raise RuntimeError(f"recraft задача умерла: {task}")
    raise RuntimeError(f"recraft не успел за {GT_MAX_WAIT}с")


def _pollinations(prompt, path):
    url = "https://image.pollinations.ai/prompt/" + quote(prompt)
    r = requests.get(url + "?width=1200&height=630&nologo=true", timeout=120)
    if r.ok and len(r.content) > 5000:
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    raise RuntimeError(f"pollinations {r.status_code}")


def _get_brand_bg():
    """Фон: файл из репо -> кэш -> скачать. Без сети карточка всё равно брендовая."""
    for p in (BRAND_BG_LOCAL, BRAND_BG_CACHE):
        if os.path.exists(p):
            logger.info(f"[image] брендовый фон из файла: {p}")
            return Image.open(p)
    try:
        r = requests.get(BRAND_BG_URL, timeout=30)
        r.raise_for_status()
        os.makedirs("data", exist_ok=True)
        with open(BRAND_BG_CACHE, "wb") as f:
            f.write(r.content)
        logger.info("[image] брендовый фон скачан в кэш")
        return Image.open(BRAND_BG_CACHE)
    except Exception as e:
        logger.warning(f"[image] фон недоступен: {e}")
        return None


def _crop_bg(bg, w=1200, h=630):
    """Вписать фон в карточку без искажений: масштаб + центр-кроп."""
    scale = max(w / bg.width, h / bg.height)
    bg = bg.resize((int(bg.width * scale), int(bg.height * scale)))
    left = (bg.width - w) // 2
    top = (bg.height - h) // 2
    return bg.crop((left, top, left + w, top + h))


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
    """Запаска: фирменный фон + заголовок. Всегда работает, 0₽."""
    bg = _get_brand_bg()
    if bg is not None:
        img = _crop_bg(bg).convert("RGBA")
        shade = Image.new("RGBA", img.size, (10, 16, 32, 110))  # чуть затемняем для читабельности
        img = Image.alpha_composite(img, shade).convert("RGB")
    else:
        img = Image.new("RGB", (1200, 630), NAVY)
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 54)
        small = ImageFont.truetype("arial.ttf", 30)
    except Exception:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 54)
        small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 30)
    title = text.replace("\n", " ").split(". ")[0][:90]
    y = 80
    for line in _wrap(title, 26):
        d.text((60, y), line, fill="white", font=font)
        y += 70
    d.text((60, 560), BRAND_NAME, fill=ACCENT, font=small)
    img.save(path)
    logger.info("[image] сработала запаска на фирменном фоне")
    return path


def get_image(prompt, text, path="data/post_image.png"):
    """Три ступени: Recraft (с образцом бренда) -> Pollinations -> Pillow."""
    os.makedirs("data", exist_ok=True)
    prompt = _translate(prompt)
    try:
        _gptunnel(prompt, path)
        logger.info("[image] recraft ok")
        return path
    except Exception as e:
        logger.warning(f"[image] gptunnel не вывез: {e}")
    try:
        _pollinations(prompt, path)
        logger.info("[image] pollinations ok")
        return path
    except Exception as e:
        logger.warning(f"[image] pollinations не вывез: {e}")
    return _template(text, path)