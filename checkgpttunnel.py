"""Список всех моделей GPTunneL для картинок с ценами."""
from dotenv import load_dotenv
load_dotenv()
import os
import requests

API_KEY = os.getenv("GPTUNNEL_API_KEY")
if not API_KEY:
    print("❌ GPTUNNEL_API_KEY не найден в .env")
    exit(1)

headers = {"Authorization": f"Bearer {API_KEY}"}
url = "https://gptunnel.ru/api/v2/media/models"

print("Запрашиваю каталог моделей GPTunneL...\n")
r = requests.get(url, headers=headers, timeout=30)

if not r.ok:
    print(f"❌ Ошибка {r.status_code}")
    print(r.text[:500])
    print("\n💡 Возможно, формат авторизации другой. Попробуем без Bearer...")
    headers2 = {"Authorization": API_KEY}
    r = requests.get(url, headers=headers2, timeout=30)
    if not r.ok:
        print(f"❌ И так не работает: {r.status_code}")
        print(r.text[:500])
        exit(1)

data = r.json()
models = data if isinstance(data, list) else data.get("data", data.get("models", []))

print(f"Всего моделей в каталоге: {len(models)}\n")
print("=" * 70)
print("📸 МОДЕЛИ ДЛЯ КАРТИНОК (type=IMAGE):")
print("=" * 70)

image_models = [m for m in models if m.get("type", "").upper() == "IMAGE"]
if not image_models:
    # Если type другой — покажем все и их типы
    print("\n⚠️ Не нашёл моделей с type=IMAGE. Показываю все:")
    types = {}
    for m in models:
        t = m.get("type", "???")
        types.setdefault(t, []).append(m)
    for t, ms in types.items():
        print(f"\n📂 Тип: {t} ({len(ms)} моделей)")
        for m in ms[:5]:
            print(f"  - {m.get('id')}: цена={m.get('price')}₽")
else:
    for m in image_models:
        print(f"\n🎨 ID: {m.get('id')}")
        print(f"   Цена: {m.get('price')} ₽")
        if m.get("params"):
            params = m["params"]
            if isinstance(params, list):
                for p in params[:3]:
                    print(f"   Параметр: {p.get('key')} = {p.get('default')}")
        if m.get("inputs"):
            print(f"   Входы: {m['inputs']}")

print("\n" + "=" * 70)
print("📹 ВСЕ ТИПЫ МОДЕЛЕЙ В КАТАЛОГЕ:")
print("=" * 70)
types_summary = {}
for m in models:
    t = m.get("type", "???")
    types_summary[t] = types_summary.get(t, 0) + 1
for t, c in types_summary.items():
    print(f"  {t}: {c} моделей")