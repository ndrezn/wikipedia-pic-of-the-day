from datetime import datetime
import pytest

import bot
from bot.twitter_creds import connect_test


api = connect_test()


def post_on_date(date):
    caption, title, ids = bot.go(date=date, post=True, test=True)

    return ids


def test_post():
    """
    Base case
    """
    date = datetime(2022, 5, 17)
    ids = post_on_date(date)

    assert len(ids) == 2


def test_gallery_post():
    """
    Tests an edge case where a gallery is provided as the picture of the day
    """
    date = datetime(2022, 8, 28)
    ids = post_on_date(date)

    assert len(ids) == 2


def test_gallery_post_2():
    date = datetime(2021, 12, 4)
    ids = post_on_date(date)

    assert len(ids) == 2


def test_multi_post():
    """
    Tests an edge case where multiple pictures are provided as the picture of the day
    """
    date = datetime(2022, 7, 25)
    ids = post_on_date(date)

    assert len(ids) == 2


def test_svg_post():
    """
    Tests posting using SVG image
    """
    date = datetime(2022, 8, 25)
    ids = post_on_date(date)

    assert len(ids) == 2


def test_png_post():
    """
    Tests posting using PNG image
    """
    date = datetime(2022, 6, 14)
    ids = post_on_date(date)

    assert len(ids) == 2


def test_large_image():
    """
    Tests posting using a large image. This image is 77mb.
    """
    date = datetime(2022, 8, 17)
    ids = post_on_date(date)

    assert len(ids) == 2
