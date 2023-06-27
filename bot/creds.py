import twitter
import os
import requests


def connect():
    return twitter.Api(
        consumer_key=os.getenv("API_KEY"),
        consumer_secret=os.getenv("API_SECRET_KEY"),
        access_token_key=os.getenv("ACCESS_TOKEN"),
        access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"),
    )


def connect_context():
    return twitter.Api(
        consumer_key=os.getenv("CONTEXT_API"),
        consumer_secret=os.getenv("CONTEXT_API_SECRET"),
        access_token_key=os.getenv("CONTEXT_ACCESS"),
        access_token_secret=os.getenv("CONTEXT_ACCESS_SECRET"),
    )


def connect_test():
    return twitter.Api(
        consumer_key=os.getenv("TEST_API"),
        consumer_secret=os.getenv("TEST_API_SECRET"),
        access_token_key=os.getenv("TEST_ACCESS"),
        access_token_secret=os.getenv("TEST_ACCESS_SECRET"),
    )


def connect_bluesky(bluesky_base_url, username, password):
    resp = requests.post(
        bluesky_base_url + "/com.atproto.server.createSession",
        json={
            "identifier": username,
            "password": password,
        },
    )
    resp_data = resp.json()

    jwt = resp_data["accessJwt"]
    did = resp_data["did"]
    return jwt, did
