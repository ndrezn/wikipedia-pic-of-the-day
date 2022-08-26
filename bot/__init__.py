import nltk
import os

if not os.path.exists("/nltk_data"):
    nltk.download("punkt", download_dir="/nltk_data/")

from .post import go
