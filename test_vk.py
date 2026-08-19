from dotenv import load_dotenv
load_dotenv()

from agent.vk import publish

print(publish("Пост №0. Агент на связи, проверка соединения. Манифест следующим."))