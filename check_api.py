from dotenv import load_dotenv
load_dotenv()
import os
import requests

base = os.getenv("SERVERSPACE_BASE_URL").rstrip("/")
key = os.getenv("SERVERSPACE_API_KEY")
h = {"Authorization": f"Bearer {key}"}

print("base_url:", base)

r = requests.get(base + "/models", headers=h)
print("GET /models ->", r.status_code)
if r.ok:
    data = r.json().get("data", [])
    print(f"Всего моделей: {len(data)}")
    print("--- Все доступные модели ---")
    for m in data:
        print("  ", m.get("id"))
    print("--- Похожие на генерацию изображений ---")
    img_terms = ("image", "flux", "seedream", "imagen", "banana", "midjourney",
                 "recraft", "dall-e", "dalle", "gpt-image", "grom", "uzor",
                 "pixel", "playground")
    for m in data:
        mid = str(m.get("id", ""))
        title = str(m.get("title", ""))
        hay = (mid + " " + title).lower()
        if any(t in hay for t in img_terms):
            print("  ", m.get("id"), "|", m.get("title"))
else:
    print(r.text[:800])
