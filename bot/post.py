from . import text_parsers, image_handler, twitter_creds
import datetime
from mwclient import Site
import os
import time


def generate_primary_caption(caption):
    short_caption = text_parsers.shorten_caption(caption, 280)
    return short_caption


def generate_secondary_caption(title, caption, primary_caption):
    # Add reply tweet with a link to the original article
    link = text_parsers.generate_link(title)
    title = title.split("#")[0]  # Cut off any pageheadings
    reply_text = '{} Appears in "{}": {}'

    # Note that links are abbreviated to 23 characters
    excess_caption = text_parsers.shorten_caption(
        caption[len(primary_caption) :],
        280 - len(reply_text.format(' "... "', title, link[:23])),
    )

    if excess_caption:
        reply_text = reply_text.format(f' "... {excess_caption.strip()}"', title, link)
    else:
        reply_text = reply_text.format("", title, link)

    return reply_text


def generate_attribution_caption(image_titles):
    wm = Site("commons.wikimedia.org")
    authors, source_links = zip(
        *[text_parsers.get_image_information(wm, i) for i in image_titles]
    )
    authors = list(set(authors))
    source_links = list(set(source_links))

    caption = f"Authored by {', '.join(authors)}. " if authors[0] else ""
    caption += f"Original image{'s' if len(source_links)>1 else ''} and metadata can be found at: {', '.join(source_links)}"

    return caption


def upload_video(api, tweet_content, path):
    """
    Without chunking the video, length is capped at 30s. This way we can post up to 140s.
    """
    video_id = api.UploadMediaChunked(media=path, media_category="tweet_video")
    # Waits until the async processing of the uploaded media finishes and `video_id` becomes valid.
    # 100s is maybe gratuitous, but better safe than sorry 😊
    time.sleep(100)
    status = api.PostUpdate(status=tweet_content, media=video_id)
    return status


def upload_statuses(caption, paths, title, image_titles, test):
    """
    Upload two statuses to Twitter: One with a photo and most of the caption,
    and another replying to that tweet with more caption (if applicable) and context
    """
    if test:
        api = twitter_creds.connect_test()
    else:
        api = twitter_creds.connect()
    primary_caption = generate_primary_caption(caption)
    if not paths[0].endswith(".mp4"):
        status = api.PostUpdate(
            status=primary_caption,
            media=paths,
        )
    else:
        status = upload_video(api, primary_caption, paths[0])
    secondary_caption = generate_secondary_caption(title, caption, primary_caption)

    if test:
        context_api = twitter_creds.connect_test()
    else:
        context_api = twitter_creds.connect_context()

    reply_status = context_api.PostUpdate(
        status=secondary_caption,
        in_reply_to_status_id=status.id,
        auto_populate_reply_metadata=True,
    )

    attribution_status = context_api.PostUpdate(
        status=generate_attribution_caption(image_titles),
        in_reply_to_status_id=reply_status.id,
        auto_populate_reply_metadata=True,
    )

    return status.id, reply_status.id, attribution_status.id


def go(date=None, download=True, post=True, test=False):
    """
    Gets the photo of the day, downloads the photo, and triggers posting
    """
    if not date:
        date = datetime.datetime.now()
    title = (
        "Template:POTD/"
        + str(date.year)
        + "-"
        + str(date.month).zfill(2)
        + "-"
        + str(date.day).zfill(2)
    )
    site = Site("en.wikipedia.org")
    page = site.pages[title]

    caption = text_parsers.clean_text(page, "caption")
    image_titles = text_parsers.clean_text(page, "image")
    article_title = text_parsers.clean_text(page, "title")

    ids, paths = [], []
    if download or post:
        paths = [
            image_handler.get_image(site, title, date, i)
            for i, title in enumerate(image_titles)
        ]
    if post:
        ids = upload_statuses(caption, paths, article_title, image_titles, test)
    for p in paths:
        os.remove(p)

    return caption, [article_title, image_titles], ids
