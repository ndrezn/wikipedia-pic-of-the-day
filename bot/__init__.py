import nltk
import os

from .post import go
from . import post
from . import creds

import dotenv

from dotenv import load_dotenv


load_dotenv()

if not os.path.exists("nltk_data"):
    nltk.download("punkt", download_dir="nltk_data/")
