"""
Tests for posting to Bluesky, with the Bluesky API stubbed out
"""

import pytest
import requests
from moviepy import ColorClip
from PIL import Image

from bot import creds, post


class FakeBluesky:
    """
    Records calls to requests.post and answers like the Bluesky API
    """

    def __init__(self, fail_content_type=None):
        self.calls = []
        self.fail_content_type = fail_content_type

    def __call__(self, url, data=None, json=None, headers=None):
        endpoint = url.rsplit(".", 1)[1]
        content_type = (headers or {}).get("Content-Type")
        self.calls.append({"endpoint": endpoint, "type": content_type, "json": json})

        response = requests.Response()
        response.url = url
        response.status_code = 200
        if content_type and content_type == self.fail_content_type:
            response.status_code = 413
        n = len(self.calls)
        body = {"blob": {"n": n}, "uri": f"at://post/{n}", "cid": f"cid{n}"}
        response._content = requests.compat.json.dumps(body).encode()
        return response

    def records(self):
        return [c["json"]["record"] for c in self.calls if c["json"]]

    def uploads(self):
        return [c["type"] for c in self.calls if c["endpoint"] == "uploadBlob"]


@pytest.fixture
def bluesky(monkeypatch):
    def install(**kwargs):
        fake = FakeBluesky(**kwargs)
        monkeypatch.setattr(post.requests, "post", fake)
        return fake

    monkeypatch.setattr(creds, "connect_bluesky", lambda *args: ("jwt", "did"))
    monkeypatch.setattr(
        post,
        "generate_attribution_caption",
        lambda titles: "Original image: https://commons.wikimedia.org/wiki/File:X.jpg",
    )
    return install


@pytest.fixture(scope="session")
def jpg(tmp_path_factory):
    path = tmp_path_factory.mktemp("media") / "image.jpg"
    Image.new("RGB", (800, 600), (30, 120, 200)).save(path)
    return str(path)


@pytest.fixture(scope="session")
def mp4(tmp_path_factory):
    path = tmp_path_factory.mktemp("media") / "video.mp4"
    clip = ColorClip((64, 64), color=(200, 0, 0), duration=2).with_fps(5)
    clip.write_videofile(str(path), codec="libx264", audio=False, logger=None)
    return str(path)


CAPTION = "A caption. " * 50


def test_image_post_and_replies(bluesky, jpg):
    fake = bluesky()
    post.upload_statuses(CAPTION, [jpg], "Lake Tanganyika", ["X.jpg"], test=False)

    assert fake.uploads() == ["image/jpg"]
    main, reply, attribution = fake.records()
    assert main["embed"]["$type"] == "app.bsky.embed.images"
    assert all(len(r["text"]) <= post.MAX_POST_LENGTH for r in fake.records())
    assert "https://en.wikipedia.org/wiki/Lake_Tanganyika" in reply["text"]


def test_replies_thread_from_main_post(bluesky, jpg):
    fake = bluesky()
    post.upload_statuses(CAPTION, [jpg], "Lake Tanganyika", ["X.jpg"], test=False)

    main, reply, attribution = fake.records()
    main_post, first_reply = "at://post/2", "at://post/3"
    assert reply["reply"]["parent"]["uri"] == main_post
    assert reply["reply"]["root"]["uri"] == main_post
    assert attribution["reply"]["parent"]["uri"] == first_reply
    # Every reply in a thread points at the same root post
    assert attribution["reply"]["root"]["uri"] == main_post


def test_video_post(bluesky, mp4):
    fake = bluesky()
    post.upload_statuses(
        CAPTION, [mp4], "Man with a Movie Camera", ["X.webm"], test=False
    )

    assert fake.uploads() == ["video/mp4"]
    assert fake.records()[0]["embed"]["$type"] == "app.bsky.embed.video"


def test_video_falls_back_to_still_frame(bluesky, mp4):
    fake = bluesky(fail_content_type="video/mp4")
    post.upload_statuses(
        CAPTION, [mp4], "Man with a Movie Camera", ["X.webm"], test=False
    )

    assert fake.uploads() == ["video/mp4", "image/jpg"]
    assert fake.records()[0]["embed"]["$type"] == "app.bsky.embed.images"
    assert len(fake.records()) == 3


def test_link_facets_use_byte_offsets(bluesky):
    fake = bluesky()
    url = "https://en.wikipedia.org/wiki/Saint-Étienne"
    text = f'"... café – naïve" Appears in "Saint-Étienne": {url}'
    post.post_bluesky(
        "jwt", "did", post.BLUESKY_BASE_URL, text, reply_uri="u", reply_cid="c"
    )

    facet = fake.records()[0]["facets"][0]
    start, end = facet["index"]["byteStart"], facet["index"]["byteEnd"]
    assert text.encode()[start:end].decode() == url


def test_comma_separated_links(bluesky):
    fake = bluesky()
    links = [
        "https://commons.wikimedia.org/wiki/File:A,_b.jpg",
        "https://commons.wikimedia.org/wiki/File:Человек_с_киноаппаратом_(1929).webm",
    ]
    text = f"Original images and metadata can be found at: {', '.join(links)}"
    post.post_bluesky(
        "jwt", "did", post.BLUESKY_BASE_URL, text, reply_uri="u", reply_cid="c"
    )

    facets = fake.records()[0]["facets"]
    assert [f["features"][0]["uri"] for f in facets] == links
    for facet, link in zip(facets, links):
        start, end = facet["index"]["byteStart"], facet["index"]["byteEnd"]
        assert text.encode()[start:end].decode() == link


def test_failed_post_raises(monkeypatch):
    def reject(url, **kwargs):
        response = requests.Response()
        response.status_code = 400
        response.url = url
        response._content = b'{"error": "InvalidRequest"}'
        return response

    monkeypatch.setattr(post.requests, "post", reject)
    with pytest.raises(requests.exceptions.HTTPError):
        post.post_bluesky("jwt", "did", post.BLUESKY_BASE_URL, "text")
