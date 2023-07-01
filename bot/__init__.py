import nltk
import os

from .post import go
from . import post
from . import creds

if not os.path.exists("nltk_data"):
    nltk.download("punkt", download_dir="nltk_data/")
