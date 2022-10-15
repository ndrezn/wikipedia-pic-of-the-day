import os
from PIL import Image
from cairosvg import svg2png
from moviepy.editor import VideoFileClip, AudioFileClip
import moviepy

import time

# Configure PIL to allow bigger images
Image.MAX_IMAGE_PIXELS = 1000000000


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
    if path.endswith("webm"):
        video = VideoFileClip(path)
        duration = video.duration

        if duration > 140:
            video = video.subclip(
                0, 140
            )  # Trim the clip to 140s, i.e. max length allowed by Twitter
            video = moviepy.video.fx.all.fadeout(
                video, 2, final_color=None
            )  # Add a short fadeout

        new_path = path.replace(".webm", ".mp4")
        # Store the file as .mp4; Twitter does not support .webm
        video.write_videofile(
            new_path,
            temp_audiofile=new_path.replace(".mp4", ".m4a"),
            remove_temp=True,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
        )
        # Remove the .webm file
        os.remove(path)
        return new_path

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


def get_image(site, title, date, i):
    """
    Download an image from Wikipedia to a local folder
    """
    f = site.images[title]
    if not os.path.isdir(os.getcwd() + "/photos"):
        os.mkdir(os.getcwd() + "/photos")
    path = f"{os.getcwd()}/photos/{date.year}_{date.month}_{date.day}_{i}.{title.rsplit('.', 1)[1]}"
    if not os.path.exists(path):
        with open(path, "wb") as fd:
            f.download(fd)
    path = resize_image(path)

    return path
