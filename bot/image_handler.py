import os
from PIL import Image
from cairosvg import svg2png
from moviepy.editor import VideoFileClip
import moviepy
import io

# Configure PIL to allow bigger images
Image.MAX_IMAGE_PIXELS = 1000000000

def get_image_bytes(input_file_path, max_size_kb=900, quality=85):
    '''
    Compresses the image to the required size and adds a border to make it square
    '''
    # Open the input image file
    with Image.open(input_file_path) as img:
        # Continue attempting to compress until we hit the desired size
        while True:
            # Calculate the dimensions of the square canvas
            wc_width, wc_height = img.size
            long_edge = int(1.1 * max(wc_width, wc_height))
            
            # Calculate coordinates to paste the original image onto the center of the canvas
            paste_x = int(long_edge / 2 - wc_width / 2)
            paste_y = int(long_edge / 2 - wc_height / 2)
            
            # Create a new square canvas with a white background
            bg = Image.new("RGB", (long_edge, long_edge), (255, 252, 233))
            
            # Paste the original image onto the center of the canvas
            bg.paste(img, (paste_x, paste_y))
            
            # Create a BytesIO object to store the image bytes
            image_io = io.BytesIO()
            
            # Save the compressed and padded image to the BytesIO object with quality
            bg.save(image_io, format="JPEG", quality=quality)
            
            # Calculate the size of the saved image
            saved_size_kb = len(image_io.getvalue()) / 1024
            
            # Check if the size is within the desired range
            if saved_size_kb <= max_size_kb:
                return image_io.getvalue()  # Return the compressed image as bytes
            
            # Reduce the quality and continue compressing
            quality -= 5
            if quality <= 0:
                raise Exception("Unable to compress image to the desired size.")


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
