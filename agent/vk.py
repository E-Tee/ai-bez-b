"""Паблишер ВК: загрузить фото + выложить пост на стену."""
import os
import time
import logging
import requests
from PIL import Image

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VK_API = "https://api.vk.com/method/"

# камуфляж под браузер: приёмщики ВК не любят голый python-requests
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"}


def _check_env():
    required = ["VK_TOKEN", "VK_GROUP_ID"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        raise RuntimeError(f"Нет переменных окружения: {', '.join(missing)}")
    logger.info("VK-переменные на месте")


_check_env()


def vk(method, token=None, **params):
    """Вызов VK API с ретраями. token — переопределение (личный токен)."""
    params["access_token"] = token or os.getenv("VK_TOKEN")
    params["v"] = "5.131"
    for attempt in range(3):
        try:
            r = requests.post(VK_API + method, data=params, timeout=10).json()
            if "error" not in r:
                return r["response"]
            msg = r["error"].get("error_msg", "неизвестная ошибка")
            logger.warning(f"VK ошибка: {msg}")
            if attempt == 2:
                raise RuntimeError(f"VK ошибка: {msg}")
            time.sleep(2 ** attempt)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Попытка {attempt + 1}/3 не удалась: {e}")
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("VK API не ответил")


def _prepare_jpeg(image_path):
    """Лёгкий JPEG 1280px: ВК глотает его без вопросов."""
    os.makedirs("data", exist_ok=True)
    jpg = os.path.join("data", "upload_1280.jpg")
    with Image.open(image_path) as im:
        im = im.convert("RGB")
        if im.width > 1280:
            im = im.resize((1280, int(im.height * 1280 / im.width)))
        im.save(jpg, "JPEG", quality=85)
    return jpg


def _upload_wall(image_path, gid, token):
    """Парадная дверь: wall-сервер под личным токеном. Фотка клеится к посту."""
    jpg = _prepare_jpeg(image_path)
    srv = vk("photos.getWallUploadServer", group_id=gid, token=token)
    with open(jpg, "rb") as f:
        up = requests.post(srv["upload_url"], files={"photo": f},
                           headers=UA, timeout=60).json()
    logger.info(f"[vk] wall-загрузка: {str(up)[:120]}")
    saved = vk("photos.saveWallPhoto", token=token, group_id=gid,
               photo=up["photo"], server=up["server"], hash=up["hash"])[0]
    key = saved.get("access_key")
    att = f"photo{saved['owner_id']}_{saved['id']}" + (f"_{key}" if key else "")
    logger.info(f"[vk] attachment (wall-путь): {att}")
    return att


def _upload_messages(image_path, gid):
    """Запасная калитка: messages-путь под групповым токеном."""
    jpg = _prepare_jpeg(image_path)
    for attempt in range(3):
        srv = vk("photos.getMessagesUploadServer", group_id=gid)
        with open(jpg, "rb") as f:
            r = requests.post(srv["upload_url"], files={"photo": f},
                              headers=UA, timeout=60)
        logger.info(f"[vk] messages-загрузка: {r.status_code}")
        if not (r.ok and r.text.strip().startswith("{")):
            continue
        up = r.json()
        if not up.get("photo"):
            continue
        saved = vk("photos.saveMessagesPhoto", photo=up["photo"],
                   server=up["server"], hash=up["hash"])[0]
        if saved.get("sizes"):
            key = saved.get("access_key")
            return f"photo{saved['owner_id']}_{saved['id']}" + (f"_{key}" if key else "")
    raise RuntimeError("ВК не принял файл")


def publish(text, image_path=None):
    gid = int(os.getenv("VK_GROUP_ID"))
    att = ""
    if image_path:
        logger.info(f"[vk] файл весит: {os.path.getsize(image_path)} байт")
        utoken = os.getenv("VK_USER_TOKEN")
        if utoken:
            try:
                att = _upload_wall(image_path, gid, utoken)
            except Exception as e:
                logger.warning(f"[vk] wall-путь не пустил ({e}), иду в messages")
                att = _upload_messages(image_path, gid)
        else:
            att = _upload_messages(image_path, gid)
    return vk("wall.post", owner_id=-gid, from_group=1,
              message=text, attachments=att)