from dotenv import load_dotenv
load_dotenv()
from agent import analytics
analytics.refresh()
print("метрики обновлены")