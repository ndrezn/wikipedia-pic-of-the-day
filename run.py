import schedule
import time
import bot
from dotenv import load_dotenv


def schedule_task():
    """
    Task scheduler
    """
    schedule.every().day.at("09:30").do(bot.go)

    while True:
        schedule.run_pending()
        time.sleep(60)  # wait minutes


load_dotenv()
bot.go()
schedule_task()
