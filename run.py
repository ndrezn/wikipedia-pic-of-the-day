import schedule
import time
import bot
from datetime import datetime

def post():
    bot.go()
    print(datetime.now())

def schedule_task():
    """
    Task scheduler
    """
    schedule.every().day.at("15:30").do(post)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # wait minutes


schedule_task()
