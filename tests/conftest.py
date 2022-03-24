from pathlib import Path

import pytest


@pytest.fixture()
def data_folder():
    return Path(__file__).parent / "data"
