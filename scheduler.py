"""Дирижёр v1: посты в 13:00 и 19:00, метрики в 22:00, отчёт в вс 18:00."""
from dotenv import load_dotenv
load_dotenv()

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from agent.pipeline import run
from agent import analytics


def job_post():
    try:
        run(do_publish=True)
    except Exception as e:
        print("[scheduler] пост не встал:", e)


def job_stats():
    try:
        analytics.refresh()
        print("[scheduler] метрики обновлены")
    except Exception as e:
        print("[scheduler] аналитика упала:", e)


def job_report():
    try:
        analytics.refresh()
        from agent.llm import ask
        from agent.vk import publish
        raw = analytics.week_report()
        text = ask("writer",
                   "Сделай из этих сухих цифр живой пост-отчёт для паблика. "
                   "Без мата, с юмором, в стиле «ИИ просто и без затей»:\n" + raw)
        publish(text)
        print("[scheduler] отчёт опубликован")
    except Exception as e:
        print("[scheduler] отчёт упал:", e)


if __name__ == "__main__":
    s = BlockingScheduler()
    s.add_job(job_post, CronTrigger(hour=13, minute=0))
    s.add_job(job_post, CronTrigger(hour=19, minute=0))
    s.add_job(job_stats, CronTrigger(hour=22, minute=0))
    s.add_job(job_report, CronTrigger(day_of_week="sun", hour=18, minute=0))
    print("Дирижёр на смене: посты 13:00/19:00, метрики 22:00, отчёт вс 18:00")
    s.start()