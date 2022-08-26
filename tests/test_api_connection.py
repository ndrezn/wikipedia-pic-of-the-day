from bot import twitter_creds


def test_main_connection():
    api = twitter_creds.connect()
    users = api.GetFriends()
    assert True


def test_reply_connection():
    api = twitter_creds.connect_context()
    users = api.GetFriends()
    assert True


def test_test_connection():
    api = twitter_creds.connect_test()
    users = api.GetFriends()
    assert True
