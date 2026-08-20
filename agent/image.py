"""Картинки: Pollinations, а если он косячит — фирменная Pillow-открытка."""
import os
import requests
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

PALETTE = [(255, 122, 0), (24, 38, 63), (46, 160, 90), (155, 48, 255)]


def get_image(prompt, text, path="data/post_image.png"):
    os.makedirs("data", exist_ok=True)
    try:
        url = "https://image.pollinations.ai/prompt/" + quote(prompt)
        r = requests.get(url + "?width=1200&height=630&nologo=true", timeout=120)
        if r.ok and len(r.content) > 5000:
            open(path, "wb").write(r.content)
            print("[image] pollinations ок")
            return path
    except Exception as e:
        print(f"[image] pollinations не вывез: {e}")
    return _template(text, path)


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
    d.text((60, 560), "ИИ просто и без затей", fill="white", font=small)
    print("[image] сработала запаска Pillow")
    img.save(path)
    print("[image] сработала запаска Pillow")
    return path