import os
from PIL import Image, ImageOps
from cairosvg import svg2png
import time


def resize_image(path):
    """
    Resize a local image to conform to Twitter restrictions
    """
    base = 2160
    if path.endswith("svg"):
        svg_file = open(path)
        svg_code = svg_file.read()
        os.remove(path)
        path = path.replace("svg", "png")
        svg2png(bytestring=svg_code, write_to=path)
    if path.endswith("png"):
        im = Image.open(path)
        rgb_im = im.convert("RGB")
        os.remove(path)
        path = path.replace("png", "jpg")
        rgb_im.save(path)
    img = Image.open(path)
    w, h = img.size
    # Shrink the image. Makes it quicker to upload and generally smaller. 2k is more than enough
    if w > base:
        wpercent = base / float(w)
        hsize = int((float(h) * float(wpercent)))
        img = img.resize((base, hsize), Image.ANTIALIAS)
        w, h = img.size

    img.save(path)

    # Check to make sure file is twitter compatable size, and if not, reduce it until it is
    quality = 30
    while os.path.getsize(path) > 5242880:
        img = Image.open(path)
        img.save(path, quality=quality)

    return path


def get_image(site, title):
    """
    Download an image from Wikipedia to a local folder
    """
    f = site.images[title]
    if not os.path.isdir(os.getcwd() + "/photos"):
        os.mkdir(os.getcwd() + "/photos")
    path = f"{os.getcwd()}/photos/{str(round(time.time() * 1000))}.{title.rsplit('.', 1)[1]}"
    with open(path, "wb") as fd:
        f.download(fd)

    path = resize_image(path)

    return path
