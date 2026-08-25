"""Проверка, что ВК принимает картинку от Recraft: python test_photo.py"""
from dotenv import load_dotenv
load_dotenv()
from agent.vk import publish

print(publish("🤖 Проверка связи: гоняю картинку через все замки ВК.",
              "data/post_image.png"))