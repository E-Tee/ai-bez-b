from dotenv import load_dotenv
load_dotenv()
from agent.vk import publish

print(publish("🖼 Тест прикрепления картинки. Пост служебный, потом удалю.",
              "data/post_image.png"))