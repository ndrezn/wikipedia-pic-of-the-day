import bot
from datetime import datetime


def test_main_caption_length():
    for date in [
        datetime(2022, 5, 17),
        datetime(2021, 5, 17),
        datetime(2022, 2, 17),
        datetime(2022, 4, 1),
    ]:
        caption, image_title, article_title = bot.go(date=date, post=False)
        primary_caption = bot.post.generate_primary_caption(caption)
        secondary_caption = bot.post.generate_secondary_caption(
            article_title, caption, primary_caption
        )
        assert len(primary_caption) < 280 and len(secondary_caption) < 280


def test_main_caption():
    date = datetime(2022, 5, 17)
    caption, image_title, article_title = bot.go(date=date, post=False)
    primary_caption = bot.post.generate_primary_caption(caption)
    assert primary_caption == (
        "Altolamprologus compressiceps is a species of fish in the "
        "family Cichlidae, endemic to the shallow rocky areas of Lake "
        "Tanganyika. The lake holds at least 250 species of cichlid fish, "
        "including species yet to be described. "
    )


def test_secondary_caption():
    date = datetime(2022, 5, 17)
    caption, image_title, article_title = bot.go(date=date, post=False)
    primary_caption = bot.post.generate_primary_caption(caption)
    secondary_caption = bot.post.generate_secondary_caption(
        article_title, caption, primary_caption
    )
    assert secondary_caption == (
        ' "... Almost all (98 percent) of Tanganyika cichlid species '
        "are endemic to the lake, and it is thus an important biological "
        'resource for the study of speciation in evolution." Appears '
        'in "Altolamprologus compressiceps": en.wikipedia.org/wiki/Altolamprologus_compressiceps'
    )
