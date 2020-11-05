import tweepy
from mwclient import Site
import mwparserfromhell as mw
import datetime
import requests
import os
from PIL import Image, ImageOps
import schedule
import time
import nltk


def shorten_caption(caption, length):
    # Shorten the caption to a given length
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    if len(caption) > length:
        caption = tokenizer.tokenize(caption)
        new_caption = ""
        while len(new_caption) + len(caption[0]) < length and len(caption) > 1:
            new_caption += f"{caption.pop(0)} "
        caption = new_caption

    return caption


def normalize_title(title):
    title = title.strip()
    if title[0] == ":":
        title = title[1:]
    title = title[0].upper() + title[1:]
    title = title.replace(" ", "_")
    title = "en.wikipedia.org/wiki/{}".format(title)
    return title


def clean_text(page, item_to_get):
    parsed_text = mw.parse(page.text())
    if item_to_get == "link":
        link = parsed_text.filter_wikilinks()[0].title
        return normalize_title(link)
    wikicode = parsed_text.filter_templates()
    item = wikicode[0].get(item_to_get).value
    plain_text = item.strip_code()

    return plain_text


def resize_image(path):
    base = 2160
    img = Image.open(path)
    w, h = img.size
    if w > base:
        wpercent = base / float(w)
        hsize = int((float(h) * float(wpercent)))
        img = img.resize((base, hsize), Image.ANTIALIAS)
        w, h = img.size

    img.save(path)

    quality = 30
    while os.path.getsize(path) > 5242880 and quality > 0:
        print(os.path.getsize(path))
        img = Image.open(path)
        img.save(path, quality=quality)
        quality -= 5

    return img


def get_image(site, title):
    f = site.images[title]
    path = os.getcwd() + "/photos/" + title
    with open(path, "wb") as fd:
        f.download(fd)

    resize_image(path)

    return path


def post(caption, path, context):
    token = os.getenv("ACCESS_TOKEN")
    token_secret = os.getenv("ACCESS_TOKEN_SECRET")
    consumer_key = os.getenv("API_KEY")
    consumer_secret = os.getenv("API_SECRET_KEY")

    # authenticating to access the twitter API
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(token, token_secret)
    api = tweepy.API(auth)

    # Generate text tweet with media (image)
    short_caption = shorten_caption(caption, 280)
    status = api.update_with_media(filename=path, status=short_caption)
    # Add reply tweet with a link to the original article
    reply_text = "@WikiPicOfTheDay{} \noccurred in: {}"
    excess_caption = shorten_caption(
        caption[len(short_caption) :], 280 - len(reply_text.format(' "... "', context))
    )
    if excess_caption:
        reply_status = reply_text.format(f' "... {excess_caption}"', context)
    else:
        reply_status = reply_text.format("", context)

    api.update_status(
        status=reply_status,
        in_reply_to_status_id=status._json["id"],
    )

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

    caption = clean_text(page, "caption")
    image_title = clean_text(page, "image")
    first_link = clean_text(page, "link")

    path = get_image(site, image_title)

    posted = post(caption, path, first_link)
    print(date)
    return True


def schedule_task():
    schedule.every().day.at("09:30").do(run)

    while True:
        schedule.run_pending()
        time.sleep(60)  # wait minutes


run()
schedule_task()
