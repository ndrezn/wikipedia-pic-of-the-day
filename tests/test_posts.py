from datetime import datetime
import pytest

import bot
from bot.creds import connect_test


api = connect_test()


def post_on_date(date, post=False, download=True):
    caption, title, posted = bot.go(date=date, post=post, download=download, test=True)

    return posted == post


def test_post():
    """
    Base case
    """
    date = datetime(2022, 5, 17)
    posted = post_on_date(date)

    assert posted


def test_gallery_post():
    """
    Tests an edge case where a gallery is provided as the picture of the day
    """
    date = datetime(2022, 8, 28)
    posted = post_on_date(date)

    assert posted


def test_gallery_post_2():
    date = datetime(2021, 12, 4)
    posted = post_on_date(date, download=True)

    # Not expexting any IDs, but expecting a list
    assert posted


def test_multi_post():
    """
    Tests an edge case where multiple pictures are provided as the picture of the day
    """
    date = datetime(2022, 7, 25)
    posted = post_on_date(date, download=True)

    assert posted


def test_svg_post():
    """
    Tests posting using SVG image
    """
    date = datetime(2022, 8, 25)
    posted = post_on_date(date)

    assert posted


def test_png_post():
    """
    Tests posting using PNG image
    """
    date = datetime(2022, 6, 14)
    posted = post_on_date(date, download=True)

    assert posted


def test_large_post():
    """
    Tests posting using a large image. This image is 77mb.
    """
    date = datetime(2022, 8, 17)
    posted = post_on_date(date)

    assert posted


def test_video_post():
    """
    Tests posting using a .webm video file
    """
    date = datetime(2022, 9, 1)
    posted = post_on_date(date)

    assert posted


def test_short_video_post():
    """
    Tests posting using a .webm video file
    """
    date = datetime(2022, 10, 14)
    posted = post_on_date(date)

    assert posted
