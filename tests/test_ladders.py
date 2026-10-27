from sc2bot.controller import ladders as ladders_command


def test_ladders_empty(db):
    assert "No ladders" in ladders_command(telegram_id=1).text


def test_ladders_lists_every_current_ladder(ladders):
    text = ladders_command(telegram_id=1).text
    assert text.index("3500") < text.index("3100") < text.index("2500")
    assert "#3" in text and "3000" not in text
