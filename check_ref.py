"""Почему recraft отказывается от референса: python check_ref.py"""
import os
import requests
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GPTUNNEL_API_KEY")
ref = os.getenv("GT_STYLE_REF", "")
clean = ref.split("?")[0]  # обрезали хвост параметров

variants = {
    "1) роль edit_source + чистый URL": {"edit_source": [clean]},
    "2) ключ image + чистый URL":       {"image": [clean]},
    "3) роль edit_source + грязный URL": {"edit_source": [ref]},
}

for name, inputs in variants.items():
    body = {
        "model": "recraftv4_1",
        "prompt": "flat vector robot painter, orange and dark navy",
        "params": {"aspect_ratio": "1:1"},
        "inputs": inputs,
    }
    r = requests.post(
        "https://gptunnel.ru/api/v2/media/price",
        headers={"Authorization": f"Bearer {key}"},
        json=body, timeout=30,
    )
    print(f"\n{name} -> {r.status_code}")
    print(r.text[:400])