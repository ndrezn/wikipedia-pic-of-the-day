import nltk
import mwparserfromhell as mw
from bs4 import BeautifulSoup
from unidecode import unidecode


def shorten_caption(caption, length):
    # Shorten the caption to a given length
    nltk.data.path.append("/nltk_data/")
    tokenizer = nltk.data.load("tokenizers/punkt/english.pickle")
    if len(caption) > length:
        caption = tokenizer.tokenize(caption)
        new_caption = ""
        while len(new_caption) + len(caption[0]) < length and len(caption) > 1:
            new_caption += f"{caption.pop(0)} "
        caption = new_caption

    return caption


def generate_link(title):
    if title[0] == ":":
        title = title[1:]
    title = title[0].upper() + title[1:]
    title = title.replace(" ", "_")
    title = "en.wikipedia.org/wiki/{}".format(title)
    return title


def clean_text(page, item_to_get):
    parsed_text = mw.parse(page.text())
    if item_to_get == "title":
        link = parsed_text.filter_wikilinks()[0].title
        title = BeautifulSoup(str(link), features="html.parser")
        title = title.prettify()
        title = unidecode(str(title)).strip()
        return title
    wikicode = parsed_text.filter_templates()
    item = wikicode[0].get(item_to_get).value
    plain_text = item.strip_code()

    return plain_text