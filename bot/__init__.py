import os

import nltk

from . import creds, post
from .post import go

__all__ = ["creds", "go", "post"]

if not os.path.exists("nltk_data"):
    nltk.download("punkt", download_dir="nltk_data/")
