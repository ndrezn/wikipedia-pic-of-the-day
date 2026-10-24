"""
Offline tests for caption and image parsing, using saved copies of POTD templates
"""

import re
from pathlib import Path

import pytest

from bot import post, text_parsers

FIXTURES = Path(__file__).parent / "fixtures"


class FakeSite:
    """
    Answers expandtemplates calls from the saved expansions in fixtures/
    """

    def __init__(self, date):
        self.date = date

    def get(self, action, text, prop):
        field = re.search(r"\|(\w+)\}\}$", text).group(1)
        expansion = (FIXTURES / f"{self.date}.{field}.wikitext").read_text()
        return {"expandtemplates": {"wikitext": expansion}}


class FakePage:
    def __init__(self, date):
        self.name = f"Template:POTD/{date}"
        self.site = FakeSite(date)

    def text(self):
        return (FIXTURES / f"{self.date}.wikitext").read_text()

    @property
    def date(self):
        return self.site.date


def test_basic_caption():
    page = FakePage("2022-05-17")
    assert text_parsers.clean_text(page, "caption").startswith(
        "Altolamprologus compressiceps is a species of fish"
    )
    assert text_parsers.clean_text(page, "image") == [
        "Altolamprologus compressiceps - Karlsruhe Zoo 01.jpg"
    ]
    assert text_parsers.clean_text(page, "title") == "Altolamprologus compressiceps"


def test_nested_templates():
    """
    Substituted {{Inflation}} markup stops mwparserfromhell finding the POTD template
    """
    page = FakePage("2026-10-06")
    caption = text_parsers.clean_text(page, "caption")
    assert caption.startswith("Thomas Mundy Peterson (October 6, 1824")
    assert "$70 ($2500 in 2024 dollars)" in caption
    assert text_parsers.clean_text(page, "image") == [
        "Thomas Mundy Peterson by William R. Tobias.jpg"
    ]
    assert text_parsers.clean_text(page, "title") == "Thomas Mundy Peterson"


def test_template_output_kept():
    """
    Numbers wrapped in templates like {{nowrap}} used to be dropped (#41)
    """
    caption = text_parsers.clean_text(FakePage("2025-03-07"), "caption")
    assert "1977 kilograms (4358 lbs) of cargo" in caption


def test_gallery_images():
    images = text_parsers.clean_text(FakePage("2022-08-28"), "image")
    assert images == [
        "US-$1-TN-1891-Fr-351.jpg",
        "US-$2-TN-1891-Fr-357.jpg",
        "US-$5-TN-1891-Fr.365.jpg",
        "US-$10-TN-1891-Fr-371.jpg",
    ]


def test_short_caption_unchanged():
    assert text_parsers.shorten_caption("One sentence.", 300) == "One sentence."


def test_long_caption_cut_at_sentence():
    caption = " ".join(f"Sentence number {i} is here." for i in range(40))
    short = text_parsers.shorten_caption(caption, 300)
    assert 0 < len(short) <= 300
    assert short.strip().endswith(".")
    assert caption.startswith(short.strip())


@pytest.mark.parametrize(
    "title, link",
    [
        ("Lake Tanganyika", "en.wikipedia.org/wiki/Lake_Tanganyika"),
        (":category thing", "en.wikipedia.org/wiki/Category_thing"),
    ],
)
def test_generate_link(title, link):
    assert text_parsers.generate_link(title) == link


def test_reply_fits_with_long_title():
    caption = " ".join(f"Sentence number {i} is quite a lot longer." for i in range(40))
    primary = post.generate_primary_caption(caption)
    title = "A very long article title " * 4
    reply = post.generate_secondary_caption(title.strip(), caption, primary)
    assert len(primary) <= post.MAX_POST_LENGTH
    assert len(reply) <= post.MAX_POST_LENGTH
    assert reply.endswith(
        "https://en.wikipedia.org/wiki/" + title.strip().replace(" ", "_")
    )


def test_gallery_attribution_trimmed(monkeypatch):
    monkeypatch.setattr(post, "Site", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        text_parsers,
        "get_image_information",
        lambda site, title: (
            "Someone",
            f"https://commons.wikimedia.org/wiki/File:{title}_{'x' * 60}.jpg",
        ),
    )
    caption = post.generate_attribution_caption(["A", "B", "C", "D"])
    assert len(caption) <= post.MAX_POST_LENGTH
    assert caption.startswith("Authored by Someone. Original images")
    # Links are dropped from the end, keeping the gallery's order
    assert "File:A_" in caption and "File:D_" not in caption
