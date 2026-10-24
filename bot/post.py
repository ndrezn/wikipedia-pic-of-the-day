import datetime
import os
import re
from datetime import timezone

import requests
from mwclient import Site

from . import creds, image_handler, text_parsers

BLUESKY_BASE_URL = "https://bsky.social/xrpc"
# Bluesky counts graphemes; len() counts code points, which is never fewer
MAX_POST_LENGTH = 300
# Wikimedia asks bots to identify themselves with a way to get in touch:
# https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
USER_AGENT = (
    "WikipediaPicOfTheDay/1.0 (https://github.com/ndrezn/wikipedia-pic-of-the-day)"
)


def generate_primary_caption(caption):
    short_caption = text_parsers.shorten_caption(caption, MAX_POST_LENGTH)
    return short_caption


def generate_secondary_caption(title, caption, primary_caption):
    # Add reply post with a link to the original article
    link = "https://" + text_parsers.generate_link(title)
    title = title.split("#")[0]  # Cut off any pageheadings
    reply_text = '{} Appears in "{}": {}'

    # Bluesky doesn't shorten links, so the full link counts towards the limit
    excess_caption = text_parsers.shorten_caption(
        caption[len(primary_caption) :],
        MAX_POST_LENGTH - len(reply_text.format(' "... "', title, link)),
    )

    if excess_caption:
        reply_text = reply_text.format(f' "... {excess_caption.strip()}"', title, link)
    else:
        reply_text = reply_text.format("", title, link)

    return reply_text


def generate_attribution_caption(image_titles):
    wm = Site("commons.wikimedia.org", clients_useragent=USER_AGENT)
    authors, source_links = zip(
        *[text_parsers.get_image_information(wm, i) for i in image_titles]
    )
    # Dedupe while keeping gallery order, so trimming drops the last images
    authors = list(dict.fromkeys(authors))
    source_links = list(dict.fromkeys(source_links))

    caption = f"Authored by {', '.join(authors)}. " if authors[0] else ""
    caption += f"Original image{'s' if len(source_links) > 1 else ''} and metadata can be found at: "

    # Galleries can have more source links than fit in one post
    links = source_links
    while len(links) > 1 and len(caption + ", ".join(links)) > MAX_POST_LENGTH:
        links = links[:-1]
    caption += ", ".join(links)

    return caption


def post_bluesky(
    bsky_jwt,
    bsky_did,
    bluesky_base_url,
    caption,
    images=[],
    video=None,
    reply_uri=None,
    reply_cid=None,
):
    headers = {"Authorization": "Bearer " + bsky_jwt}

    video_blob = None
    if video:
        bsky_media_resp = requests.post(
            bluesky_base_url + "/com.atproto.repo.uploadBlob",
            data=video,
            headers={**headers, "Content-Type": "video/mp4"},
        )
        bsky_media_resp.raise_for_status()
        video_blob = bsky_media_resp.json().get("blob")

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
        # Facets index into the UTF-8 bytes, not the characters
        url_positions = [
            (
                len(string[: match.start()].encode()),
                len(string[: match.end()].encode()),
            )
            for match in re.finditer(url_pattern, string)
        ]
        return urls, url_positions

    if video_blob:
        post_data = {
            "repo": bsky_did,
            "collection": "app.bsky.feed.post",
            "record": {
                "$type": "app.bsky.feed.post",
                "text": caption,
                "createdAt": iso_timestamp,
                "embed": {
                    "$type": "app.bsky.embed.video",
                    "video": video_blob,
                    "alt": caption,
                },
            },
        }

    elif not reply_uri:
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
    try:
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Request failed with response: {resp.json()}")
        raise e

    return resp.json()


def upload_statuses(
    caption,
    paths,
    title,
    image_titles,
    post_to_bluesky=True,
):
    """
    Upload our post and replies to Bluesky
    """
    primary_caption = generate_primary_caption(caption)
    secondary_caption = generate_secondary_caption(title, caption, primary_caption)
    attribution_caption = generate_attribution_caption(image_titles)

    if post_to_bluesky:
        main_creds = creds.connect_bluesky(
            BLUESKY_BASE_URL, os.getenv("BSKY_USERNAME"), os.getenv("BSKY_PASSWORD")
        )

        bluesky_status = None
        if paths[0].endswith(".mp4"):
            try:
                with open(paths[0], "rb") as f:
                    video = f.read()
                bluesky_status = post_bluesky(
                    *main_creds, BLUESKY_BASE_URL, primary_caption, video=video
                )
            except requests.exceptions.RequestException as e:
                # Fall back to posting a still from the video
                print(f"Video post failed, posting a still frame instead: {e}")
                images = [image_handler.get_video_frame(paths[0])]
        else:
            images = [image_handler.get_image_bytes(path) for path in paths]

        if not bluesky_status:
            bluesky_status = post_bluesky(
                *main_creds,
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

        post_bluesky(
            *reply_creds,
            BLUESKY_BASE_URL,
            attribution_caption,
            reply_uri=bluesky_reply["uri"],
            reply_cid=bluesky_reply["cid"],
        )

    return True


def go(date=None, download=True, post=True):
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
    site = Site("en.wikipedia.org", clients_useragent=USER_AGENT)
    page = site.pages[title]

    caption = text_parsers.clean_text(page, "caption")
    image_titles = text_parsers.clean_text(page, "image")
    article_title = text_parsers.clean_text(page, "title")

    posted, paths = False, []
    if download or post:
        paths = [
            image_handler.get_image(site, title, date, i)
            for i, title in enumerate(image_titles)
        ]
    if post:
        posted = upload_statuses(caption, paths, article_title, image_titles)
    for p in paths:
        os.remove(p)

    return caption, [article_title, image_titles], posted
