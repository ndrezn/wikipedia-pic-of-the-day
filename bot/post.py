from . import creds, text_parsers, image_handler
import datetime
from mwclient import Site
import os
import time
from datetime import timezone
import requests

import re

from PIL import Image
from io import BytesIO

BLUESKY_BASE_URL = "https://bsky.social/xrpc"


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
    link = "https://" + link

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


def get_image_bytes(path):
    photo = Image.open(path)

    wc_width, wc_height = photo.size
    long_edge = int(1.1 * max(wc_width, wc_height))

    paste_x = int(long_edge / 2 - wc_width / 2)
    paste_y = int(long_edge / 2 - wc_height / 2)

    bg = Image.new("RGB", (long_edge, long_edge), (255, 252, 233))
    bg.paste(photo, (paste_x, paste_y))

    image_io = BytesIO()

    bg.save(image_io, format="jpeg")

    # Twitter upload, tweet

    image_io.seek(0)

    return image_io


def post_bluesky(
    bsky_jwt,
    bsky_did,
    bluesky_base_url,
    caption,
    images=[],
    reply_uri=None,
    reply_cid=None,
):
    headers = {"Authorization": "Bearer " + bsky_jwt}

    img_blobs = []
    for image in images:
        bsky_media_resp = requests.post(
            bluesky_base_url + "/com.atproto.repo.uploadBlob",
            data=image,
            headers={**headers, "Content-Type": "image/jpg"},
        )

        img_blobs.append(bsky_media_resp.json().get("blob"))

    iso_timestamp = datetime.datetime.now(timezone.utc).isoformat()
    iso_timestamp = iso_timestamp[:-6] + "Z"

    def extract_urls(string):
        url_pattern = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        urls = re.findall(url_pattern, string)
        url_positions = [
            (match.start(), match.end()) for match in re.finditer(url_pattern, string)
        ]
        return urls, url_positions

    if not reply_uri:
        post_data = {
            "repo": bsky_did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": caption,
                "createdAt": iso_timestamp,
                "embed": {
                    "$type": "app.bsky.embed.images",
                    "images": [{"image": img, "alt": caption} for img in img_blobs],
                },
            },
        }

    else:
        uris, positions = extract_urls(caption)

        post_data = {
            "repo": bsky_did,
            "collection": "app.bsky.feed.post",
            "record": {
                "text": caption,
                "createdAt": iso_timestamp,
                "reply": {
                    "parent": {
                        "uri": reply_uri,
                        "cid": reply_cid,
                    },
                    "root": {
                        "uri": reply_uri,
                        "cid": reply_cid,
                    },
                },
                "facets": [
                    {
                        "index": {"byteStart": pos[0], "byteEnd": pos[1]},
                        "features": [
                            {"$type": "app.bsky.richtext.facet#link", "uri": uri}
                        ],
                    }
                    for uri, pos in zip(uris, positions)
                ],
            },
        }

    resp = requests.post(
        BLUESKY_BASE_URL + "/com.atproto.repo.createRecord",
        json=post_data,
        headers=headers,
    )

    return resp.json()


def upload_statuses(
    caption,
    paths,
    title,
    image_titles,
    test,
    post_to_twitter=False,
    post_to_bluesky=True,
):
    """
    Upload our statuses and replies to Twitter, Bsky, Mastodon
    """
    primary_caption = generate_primary_caption(caption)
    secondary_caption = generate_secondary_caption(title, caption, primary_caption)
    attribution_caption = generate_attribution_caption(image_titles)

    if post_to_twitter:
        if test:
            api = creds.connect_test()
        else:
            api = creds.connect()
        if not paths[0].endswith(".mp4"):
            status = api.PostUpdate(
                status=primary_caption,
                media=paths,
            )
        else:
            status = upload_video(api, primary_caption, paths[0])

        if test:
            context_api = creds.connect_test()
        else:
            context_api = creds.connect_context()

        reply_status = context_api.PostUpdate(
            status=secondary_caption,
            in_reply_to_status_id=status.id,
            auto_populate_reply_metadata=True,
        )

        attribution_status = context_api.PostUpdate(
            status=attribution_caption,
            in_reply_to_status_id=reply_status.id,
            auto_populate_reply_metadata=True,
        )

    if post_to_bluesky:
        images = [get_image_bytes(path) for path in paths]

        bluesky_status = post_bluesky(
            *creds.connect_bluesky(
                BLUESKY_BASE_URL, os.getenv("BSKY_USERNAME"), os.getenv("BSKY_PASSWORD")
            ),
            BLUESKY_BASE_URL,
            primary_caption,
            images=images,
        )

        reply_creds = creds.connect_bluesky(
            BLUESKY_BASE_URL,
            os.getenv("BSKY_CONTEXT_USERNAME"),
            os.getenv("BSKY_CONTEXT_PASSWORD"),
        )

        bluesky_reply = post_bluesky(
            *reply_creds,
            BLUESKY_BASE_URL,
            secondary_caption,
            reply_uri=bluesky_status["uri"],
            reply_cid=bluesky_status["cid"],
        )

        bluesky_attribution = post_bluesky(
            *reply_creds,
            BLUESKY_BASE_URL,
            attribution_caption,
            reply_uri=bluesky_reply["uri"],
            reply_cid=bluesky_reply["cid"],
        )

    return


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
