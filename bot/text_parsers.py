import mwparserfromhell as mw
import nltk
from bs4 import BeautifulSoup
from unidecode import unidecode


def shorten_caption(caption, length):
    # Shorten the caption to a given length
    nltk.data.path.append("nltk_data/")
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


def expand_param(page, name):
    """
    Ask Wikipedia to render a single POTD parameter, e.g. {{POTD/2026-10-06|caption}}
    """
    result = page.site.get(
        "expandtemplates", text=f"{{{{{page.name}|{name}}}}}", prop="wikitext"
    )
    return mw.parse(result["expandtemplates"]["wikitext"])


def get_param(page, potd, name):
    # Deeply nested markup (e.g. a substituted {{Inflation}}) can stop
    # mwparserfromhell from recognising the POTD template at all
    if potd is not None and potd.has(name):
        return potd.get(name).value
    return expand_param(page, name)


def clean_text(page, item_to_get):
    parsed_text = mw.parse(page.text())
    if item_to_get == "title":
        link = parsed_text.filter_wikilinks()[0].title
        title = BeautifulSoup(str(link), features="html.parser")
        title = title.prettify()
        title = unidecode(str(title)).strip()
        return title
    potd = next(
        (
            t
            for t in parsed_text.filter_templates(recursive=False)
            if t.name.strip().startswith("POTD")
        ),
        None,
    )

    if item_to_get == "image":
        if potd is not None:
            items = [i.name for i in potd.params if "image" in i.name]
        else:
            items = ["image"]
        item = [get_param(page, potd, i).strip_code().strip() for i in items]

        # Case in which the PoTD is a gallery
        if item[0] == "Blank300.png":
            item = []
            c = get_param(page, potd, "caption")
            for i in c.splitlines():
                j = i.split("|")[0]
                if j.endswith(".jpg") or j.endswith(".svg") or j.endswith(".png"):
                    if j.startswith("File:"):
                        j = j[5:]
                    item.append(j)
        # Truncate to four images
        item = item[:4]

    else:
        item = get_param(page, potd, item_to_get)
        item = item.strip_code()

    return item


def get_image_information(site, title):
    page = site.pages[f"File:{title}"]
    parsed_text = mw.parse(page.text())
    wikicode = parsed_text.filter_templates()

    author = None

    for i in wikicode:
        try:
            item = i.get("author").value
            author = item.strip_code()
            break
        except ValueError:
            pass

    source_link = f"https://commons.wikimedia.org/wiki/File:{title}".replace(" ", "_")

    return author, source_link
