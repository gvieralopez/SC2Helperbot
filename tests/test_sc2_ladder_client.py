import json
from pathlib import Path

import pytest


@pytest.fixture()
def fake_battle_tag_response(data_folder):
    with Path(data_folder / "fake_battle_tag_info.json").open() as f:
        return json.load(f)


def test_battle_tag_info(fake_battle_tag_response, monkeypatch):
    pass
