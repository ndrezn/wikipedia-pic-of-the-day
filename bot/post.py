from . import text_parsers, image_handler, twitter_creds
import datetime
from mwclient import Site


def upload_statuses(caption, path, title):
    """
    Upload two statuses to Twitter: One with a photo and most of the caption,
    and another replying to that tweet with more caption (if applicable) and context
    """
    api = twitter_creds.connect()
    short_caption = text_parsers.shorten_caption(caption, 280)
    status = api.PostUpdate(
        status=short_caption,
        media=path,
    )
    # Add reply tweet with a link to the original article
    link = text_parsers.generate_link(title)
    reply_text = '{} Appears in the article "{}": {}'
    excess_caption = text_parsers.shorten_caption(
        caption[len(short_caption) :],
        280 - len(reply_text.format(' "... "', title, link)),
    )
    if excess_caption:
        reply_text = reply_text.format(f' "... {excess_caption.strip()}"', title, link)
    else:
        reply_text = reply_text.format("", title, link)

    context_api = twitter_creds.connect_context()
    reply_status = context_api.PostUpdate(
        status=reply_text,
        in_reply_to_status_id=status.id,
        auto_populate_reply_metadata=True,
    )

    return status, reply_status


def go():
    """
    Gets the photo of the day, downloads the photo, and triggers posting
    """
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
    image_title = text_parsers.clean_text(page, "image")
    article_title = text_parsers.clean_text(page, "title")

    path = image_handler.get_image(site, image_title)

    upload_statuses(caption, path, article_title)

    return
