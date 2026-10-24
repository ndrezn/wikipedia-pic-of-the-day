from datetime import datetime

import bot


def test_main_caption_length():
    for date in [
        datetime(2022, 5, 17),
        datetime(2021, 5, 17),
        datetime(2022, 2, 17),
        datetime(2022, 4, 1),
        datetime(2026, 9, 17),
        datetime(2026, 9, 18),
        datetime(2026, 9, 22),
    ]:
        caption, titles, ids = bot.go(date=date, post=False, download=False)
        primary_caption = bot.post.generate_primary_caption(caption)
        secondary_caption = bot.post.generate_secondary_caption(
            titles[0], caption, primary_caption
        )
        assert len(primary_caption) <= 300 and len(secondary_caption) <= 300


def test_gallery_attribution_length():
    date = datetime(2022, 8, 28)
    caption, titles, ids = bot.go(date=date, post=False, download=False)
    attribution_caption = bot.post.generate_attribution_caption(titles[1])
    assert len(attribution_caption) <= 300


def test_caption_with_nested_templates():
    """
    Substituted {{Inflation}} markup stops mwparserfromhell finding the POTD template
    """
    date = datetime(2026, 10, 6)
    caption, titles, ids = bot.go(date=date, post=False, download=False)
    assert caption.startswith("Thomas Mundy Peterson (October 6, 1824")
    assert titles == [
        "Thomas Mundy Peterson",
        ["Thomas Mundy Peterson by William R. Tobias.jpg"],
    ]


def test_main_caption():
    date = datetime(2022, 5, 17)
    caption, titles, ids = bot.go(date=date, post=False, download=False)
    primary_caption = bot.post.generate_primary_caption(caption)
    assert primary_caption == (
        "Altolamprologus compressiceps is a species of fish in the "
        "family Cichlidae, endemic to the shallow rocky areas of Lake "
        "Tanganyika. The lake holds at least 250 species of cichlid fish, "
        "including species yet to be described. "
    )


def test_secondary_caption():
    date = datetime(2022, 5, 17)
    caption, titles, ids = bot.go(date=date, post=False, download=False)
    primary_caption = bot.post.generate_primary_caption(caption)
    secondary_caption = bot.post.generate_secondary_caption(
        titles[0], caption, primary_caption
    )
    assert secondary_caption == (
        ' "... Almost all (98 percent) of Tanganyika cichlid species '
        "are endemic to the lake, and it is thus an important biological "
        'resource for the study of speciation in evolution." Appears '
        'in "Altolamprologus compressiceps": https://en.wikipedia.org/wiki/Altolamprologus_compressiceps'
    )


def test_caption_keeps_template_output():
    """
    Numbers wrapped in templates like {{nowrap}} used to be dropped (#41)
    """
    date = datetime(2025, 3, 7)
    caption, titles, ids = bot.go(date=date, post=False, download=False)
    assert "1977 kilograms (4358 lbs) of cargo" in caption


def test_attribution_caption():
    date = datetime(2022, 5, 17)
    caption, titles, ids = bot.go(date=date, post=False, download=False)
    attribution_caption = bot.post.generate_attribution_caption(titles[1])

    assert attribution_caption == (
        "Authored by H. Zell. Original image and metadata can be found at: "
        "https://commons.wikimedia.org/wiki/File:Altolamprologus_compressiceps_-_Karlsruhe_Zoo_01.jpg"
    )
