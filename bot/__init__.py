import os

import nltk

from . import creds, post
from .post import go

__all__ = ["creds", "go", "post"]

# nltk 3.9+ loads the sentence tokenizer from punkt_tab rather than a pickle
if not os.path.exists("nltk_data/tokenizers/punkt_tab"):
    nltk.download("punkt_tab", download_dir="nltk_data/")
