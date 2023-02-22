from pathlib import Path

import pytest

from wacksbywarby.db import Wackabase
from wacksbywarby.models import SquareCredentials


@pytest.fixture
def square_token():
    return '{"access_token": "xxx", "refresh_token": "yyy", "short_lived": false, "expires_at": "2023-03-07T04:32:14Z", "merchant_id": "zzz", "token_type": "bearer"}'


@pytest.fixture
def temp_database(tmp_path_factory: pytest.TempPathFactory):
    return tmp_path_factory.mktemp("test_data")


def test_square_creds_marshalling(square_token: str):
    """Can marshall back and forth"""
    creds = SquareCredentials.from_string(square_token)
    # just make sure we can call a timestamp func on this to assert it's been
    # successfully converted to a timestamp
    creds.expires_at.isoformat()
    as_string = creds.to_string()
    assert as_string == square_token


def test_square_creds_io(temp_database: Path, square_token: str):
    """Can read and write square creds from a file"""
    db = Wackabase(str(temp_database))
    creds = SquareCredentials.from_string(square_token)
    db.write_square_creds(creds)
    read_creds = db.get_square_creds()
    assert read_creds.to_string() == square_token
