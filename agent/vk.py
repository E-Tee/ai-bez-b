"""Паблишер ВК: загрузить фото + выложить пост на стену."""
import os
import time
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VK_API = "https://api.vk.com/method/"


def vk(method, **params):
    """Вызов VK API с ретраями."""
    params["access_token"] = os.getenv("VK_TOKEN")
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


def publish(text, image_path=None):
    gid = int(os.getenv("VK_GROUP_ID"))
    att = ""
    if image_path:
        logger.info(f"[vk] файл весит: {os.path.getsize(image_path)} байт")
        srv = vk("photos.getMessagesUploadServer", group_id=gid)
        with open(image_path, "rb") as f:
            up = requests.post(srv["upload_url"], files={"photo": f},
                               timeout=30).json()
        saved = vk("photos.saveMessagesPhoto",
                   photo=up["photo"], server=up["server"], hash=up["hash"])[0]
        key = saved.get("access_key")
        att = f"photo{saved['owner_id']}_{saved['id']}" + (f"_{key}" if key else "")
    return vk("wall.post", owner_id=-gid, from_group=1,
              message=text, attachments=att)