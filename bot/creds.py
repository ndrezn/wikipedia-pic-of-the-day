import requests


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
