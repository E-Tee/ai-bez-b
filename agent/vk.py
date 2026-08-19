"""Паблишер ВК: загрузить фото + выложить пост на стену."""
import os
import requests

VK_API = "https://api.vk.com/method/"


def vk(method, **params):
    params["access_token"] = os.getenv("VK_TOKEN")
    params["v"] = "5.131"
    r = requests.post(VK_API + method, data=params).json()
    if "error" in r:
        raise RuntimeError(f"VK ошибка: {r['error']}")
    return r["response"]


def publish(text, image_path=None):
    gid = int(os.getenv("VK_GROUP_ID"))
    att = ""
    if image_path:
        srv = vk("photos.getWallUploadServer", group_id=gid)
        with open(image_path, "rb") as f:
            up = requests.post(srv["upload_url"], files={"photo": f}).json()
        saved = vk("photos.saveWallPhotos", group_id=gid,
                   photo=up["photo"], server=up["server"], hash=up["hash"])[0]
        att = f"photo{saved['owner_id']}_{saved['id']}"
    return vk("wall.post", owner_id=-gid, from_group=1,
              message=text, attachments=att)