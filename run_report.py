from dotenv import load_dotenv
load_dotenv()
from agent import analytics
from agent.llm import ask
from agent.vk import publish
analytics.refresh()
text = ask("writer", "Сделай из этих цифр живой пост-отчёт, без мата, с юмором:\n"
                     + analytics.week_report())
publish(text)
print("отчёт опубликован")