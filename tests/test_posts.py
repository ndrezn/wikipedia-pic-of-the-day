"""
Downloads real Pictures of the Day and checks they come out ready to post
"""

from datetime import datetime

import pytest
from moviepy import VideoFileClip
from mwclient import Site
from PIL import Image

from bot import image_handler, text_parsers

pytestmark = pytest.mark.network


def download(date):
    site = Site("en.wikipedia.org")
    page = site.pages[f"Template:POTD/{date:%Y-%m-%d}"]
    image_titles = text_parsers.clean_text(page, "image")
    return [
        image_handler.get_image(site, title, date, i)
        for i, title in enumerate(image_titles)
    ]


@pytest.fixture(autouse=True)
def photos_in_tmp(tmp_path, monkeypatch):
    # get_image saves into ./photos
    monkeypatch.chdir(tmp_path)


@pytest.mark.parametrize(
    "date, count",
    [
        pytest.param(datetime(2022, 5, 17), 1, id="jpg"),
        pytest.param(datetime(2022, 8, 28), 4, id="gallery"),
        pytest.param(datetime(2021, 12, 4), None, id="gallery-2"),
        pytest.param(datetime(2022, 7, 25), 2, id="multiple-images"),
        pytest.param(datetime(2022, 8, 25), 1, id="svg"),
        pytest.param(datetime(2022, 6, 14), 1, id="png"),
        pytest.param(datetime(2022, 8, 17), 1, id="77mb-image"),
    ],
)
def test_images_ready_to_post(date, count):
    paths = download(date)

    assert paths and (count is None or len(paths) == count)
    for path in paths:
        assert path.endswith(".jpg")
        with Image.open(path) as image:
            assert image.format == "JPEG"
        compressed = image_handler.get_image_bytes(path)
        assert len(compressed) <= 900 * 1024


@pytest.mark.parametrize(
    "date",
    [
        pytest.param(datetime(2022, 9, 1), id="video"),
        pytest.param(datetime(2022, 10, 14), id="short-video"),
    ],
)
def test_videos_ready_to_post(date):
    (path,) = download(date)

    assert path.endswith(".mp4")
    with VideoFileClip(path) as video:
        assert 0 < video.duration <= 140
    assert image_handler.get_video_frame(path)
