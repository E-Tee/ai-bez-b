"""Паблишер ВК: загрузить фото + выложить пост на стену."""
import os
import time
import logging
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VK_API = "https://api.vk.com/method/"


def _check_env():
    """Проверка наличия обязательных переменных окружения для VK."""
    required = ["VK_TOKEN", "VK_GROUP_ID"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise RuntimeError(f"Отсутствуют обязательные переменные окружения VK: {', '.join(missing)}")
    logger.info("Все обязательные переменные окружения VK найдены")


def vk(method, **params):
    """Вызов метода VK API с retry-логикой."""
    params["access_token"] = os.getenv("VK_TOKEN")
    params["v"] = "5.131"
    
    max_retries = 3
    base_delay = 1  # секунды
    
    for attempt in range(max_retries):
        try:
            r = requests.post(VK_API + method, data=params, timeout=10).json()
            if "error" in r:
                error_msg = r['error'].get('error_msg', 'Неизвестная ошибка')
                logger.warning(f"VK ошибка: {error_msg}")
                # Если ошибка связана с лимитами, пробуем подождать
                if 'rate limit' in error_msg.lower() or attempt == max_retries - 1:
                    raise RuntimeError(f"VK ошибка: {error_msg}")
                time.sleep(base_delay * (2 ** attempt))  # Экспоненциальная задержка
                continue
            return r["response"]
        except requests.exceptions.RequestException as e:
            logger.warning(f"Попытка {attempt + 1}/{max_retries} не удалась: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))
    
    raise RuntimeError("VK API не ответил после всех попыток")


def publish(text, image_path=None):
    """Публикация поста в ВК с опциональным изображением."""
    gid = int(os.getenv("VK_GROUP_ID"))
    att = ""
    if image_path:
        logger.info(f"[vk] файл весит: {os.path.getsize(image_path)} байт")
        srv = vk("photos.getWallUploadServer", group_id=gid)
        with open(image_path, "rb") as f:
            up = requests.post(srv["upload_url"], files={"photo": f}).json()
        saved = vk("photos.saveWallPhoto", group_id=gid,
                   photo=up["photo"], server=up["server"], hash=up["hash"])[0]
        logger.info(f"[vk] ответ загрузки: {up}")
        key = saved.get("access_key")
        att = f"photo{saved['owner_id']}_{saved['id']}" + (f"_{key}" if key else "")
    return vk("wall.post", owner_id=-gid, from_group=1,
              message=text, attachments=att)