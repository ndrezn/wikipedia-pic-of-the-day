import schedule
import time
import bot


def schedule_task():
    """
    Task scheduler
    """
    schedule.every().day.at("10:00").to("11:00").do(bot.go)

    while True:
        schedule.run_pending()
        time.sleep(60)  # wait minutes


schedule_task()
