from dotenv import load_dotenv
load_dotenv()  # ДО импортов агента, иначе ключи не подхватятся

from agent.llm import ask
from agent.budget import today_report

if __name__ == "__main__":
    text = ask(
        "writer",
        "Короткий пост: что такое токен. Метафора — жетончик в автомойке. "
        "5-7 предложений, живо, без мата.",
        system="Ты писатель паблика «ИИ с нуля и без понтов». "
               "Пиши просто и живо, без мата и инфоцыганства.",
    )
    print("----- ПОСТ -----")
    print(text)
    print("----- ПОТРАЧЕНО СЕГОДНЯ -----")
    print(today_report())