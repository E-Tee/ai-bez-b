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
    for m in r.json().get("data", []):
        print("  ", m.get("id"))
else:
    print(r.text[:500])