import bot
from datetime import datetime


def test_post():
    date = datetime(2022, 5, 17)
    caption, image_title, article_title = bot.go(date=date, post=True, test=True)
    assert True
