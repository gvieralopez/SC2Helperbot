from sc2bot.controller import profile


def test_profile_user_not_found(db):
    response = profile(telegram_id=1)
    assert "register" in response.text
    assert response.image is None


def test_profile_without_ladders(user):
    response = profile(telegram_id=1)
    assert "No ladders" in response.text
    assert response.image is None


def test_profile(ladders):
    response = profile(telegram_id=1)
    assert "bar ladders" in response.text
    assert "3100" in response.text and "2500" in response.text
    assert "QuxEU" not in response.text
    assert response.image is not None and response.image.startswith(b"\x89PNG")
