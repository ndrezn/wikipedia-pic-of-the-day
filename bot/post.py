from . import text_parsers, image_handler, twitter_creds
import datetime
from mwclient import Site


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


def upload_statuses(caption, path, title):
    """
    Upload two statuses to Twitter: One with a photo and most of the caption,
    and another replying to that tweet with more caption (if applicable) and context
    """
    api = twitter_creds.connect()
    primary_caption = generate_primary_caption(caption)
    status = api.PostUpdate(
        status=primary_caption,
        media=path,
    )
    secondary_caption = generate_secondary_caption(title, caption, primary_caption)

    context_api = twitter_creds.connect_context()
    reply_status = context_api.PostUpdate(
        status=secondary_caption,
        in_reply_to_status_id=status.id,
        auto_populate_reply_metadata=True,
    )

    return status, reply_status


def go(date=None, post=True):
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
    image_title = text_parsers.clean_text(page, "image")
    article_title = text_parsers.clean_text(page, "title")

    path = image_handler.get_image(site, image_title)
    if post:
        upload_statuses(caption, path, article_title)

    return caption, image_title, article_title
