from twitter import Twitter, OAuth
from mwclient import Site
import mwparserfromhell as mw
import datetime
import requests
import os
from dotenv import load_dotenv
from PIL import Image, ImageOps
import schedule
import time


def shorten_caption(caption, length):
    # Shorten the caption to a given length
    if len(caption) > length:
        caption = caption.split(".")
        caption.reverse()
        new_caption = ""
        while len(new_caption) + len(caption[-1]) < length and len(caption) > 1:
            new_caption += f"{caption.pop()}. "
        caption = new_caption
    return caption


def get_caption(templates):
    parsed_wikicode = templates[0].get("caption").value
    caption = parsed_wikicode.strip_code()

    caption = shorten_caption(caption, 240)

    return caption


def get_image_title(templates):
    parsed_wikicode = templates[0].get("image").value
    title = parsed_wikicode.strip_code()
    return title


def resize_image(img, path):
    # vertical image: 1080x1350
    # horizontal image: 1080x566
    base = 1080
    img = Image.open(path)
    w, h = img.size
    wpercent = base / float(w)
    hsize = int((float(h) * float(wpercent)))
    img = img.resize((base, hsize), Image.ANTIALIAS)
    w, h = img.size

    if h > 1350:
        img = ImageOps.expand(img, border=(int((h - 1350) / 2), 0), fill="white")
        # img = img.crop((0, (h-1350)/2, w, h-((h-1350)/2)))
    elif h < 566:
        img = ImageOps.expand(img, border=(0, -int((h - 566) / 2)), fill="white")

    # img.save(path)
    return img


def get_image(site, title):
    f = site.images[title]
    path = os.getcwd() + "/photos/" + title
    with open(path, "wb") as fd:
        f.download(fd)
    return path


def post(caption, path):
    with open(path, "rb") as imagefile:
        imagedata = imagefile.read()
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    token = os.getenv("ACCESS_TOKEN")
    token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    consumer_key = os.getenv("API_KEY")
    consumer_secret = os.getenv("API_SECRET_KEY")

    t = Twitter(auth=OAuth(token, token_secret, consumer_key, consumer_secret))

    t_upload = Twitter(
        domain="upload.twitter.com",
        auth=OAuth(token, token_secret, consumer_key, consumer_secret),
    )

    id_img = t_upload.media.upload(media=imagedata)["media_id_string"]
    t.statuses.update(status=caption, media_ids=id_img)

    return True


def run():
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
    templates = mw.parse(page.text()).filter_templates()

    caption = get_caption(templates)
    image_title = get_image_title(templates)
    path = get_image(site, image_title)
    posted = post(caption, path)
    print(date)
    return True


def schedule_task():
    schedule.every().day.at("08:00").do(run)

    while True:
        schedule.run_pending()
        time.sleep(60)  # wait minutes


run()
schedule_task()
