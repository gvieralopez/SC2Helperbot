import json
from pathlib import Path

import pytest


@pytest.fixture()
def fake_ladder_info_response(data_folder):
    with Path(data_folder / "fake_ladder_info.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_ladder_summary_response(data_folder):
    with Path(data_folder / "fake_ladder_summary.json").open() as f:
        return json.load(f)


@pytest.fixture()
def fake_metadata_response(data_folder):
    with Path(data_folder / "fake_metadata.json").open() as f:
        return json.load(f)


def test_player_stats(fake_ladder_info_response, fake_ladder_summary_response, monkeypatch):
    pass


def test_player_display_name(fake_metadata_response, monkeypatch):
    pass


def test_obtain_token(monkeypatch):
    pass
