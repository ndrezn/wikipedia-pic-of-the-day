from bot import creds


def test_main_connection():
    api = creds.connect()
    users = api.GetFriends()
    assert True


def test_reply_connection():
    api = creds.connect_context()
    users = api.GetFriends()
    assert True


def test_test_connection():
    api = creds.connect_test()
    users = api.GetFriends()
    assert True
