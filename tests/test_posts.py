import bot
from datetime import datetime


def test_post():
    """
    Base case
    """
    date = datetime(2022, 5, 17)
    caption, article_title = bot.go(date=date, post=True, test=True)
    assert True


def test_gallery_post():
    """
    Tests an edge case where a gallery is provided as the picture of the day
    """
    date = datetime(2022, 8, 28)
    caption, article_title = bot.go(date=date, post=True, test=True)
    assert True


def test_gallery_post_2():
    date = datetime(2021, 12, 4)
    caption, article_title = bot.go(date=date, post=True, test=True)
    assert True


def test_multi_post():
    """
    Tests an edge case where multiple pictures are provided as the picture of the day
    """
    date = datetime(2022, 7, 25)
    caption, article_title = bot.go(date=date, post=True, test=True)
    assert True
