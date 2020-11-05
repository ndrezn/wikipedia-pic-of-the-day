import twitter
import os


def connect():
    return twitter.Api(
        consumer_key=os.getenv("API_KEY"),
        consumer_secret=os.getenv("API_SECRET_KEY"),
        access_token_key=os.getenv("ACCESS_TOKEN"),
        access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"),
    )