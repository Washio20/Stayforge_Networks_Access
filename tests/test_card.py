import pytest
from card import CardModel
from datetime import datetime, timedelta, timezone


@pytest.fixture
def default_card_data():
    return {
        "number": "CARD123456",
        "devices": ["device1", "device2"],
    }


def test_fill_times_set_start_and_created_at(default_card_data):
    card_data = CardModel(**default_card_data)
    now = datetime.now(tz=timezone.utc)
    assert card_data.created_at is not None
    assert card_data.start_at is not None
    assert abs((card_data.created_at - now).total_seconds()) < 1
    assert abs((card_data.start_at - now).total_seconds()) < 1


def test_fill_times_end_at_based_on_ttl(default_card_data):
    ttl = 3600
    card_data = CardModel(**default_card_data, ttl=ttl)
    now = card_data.start_at
    expected_end_at = now + timedelta(seconds=ttl)
    assert card_data.ttl == ttl
    assert card_data.end_at == expected_end_at


def test_fill_times_ttl_calculated_from_end_at(default_card_data):
    end_at = datetime.now(tz=timezone.utc) + timedelta(hours=2)
    card_data = CardModel(**default_card_data, end_at=end_at)
    now = datetime.now(tz=timezone.utc)
    expected_ttl = int((end_at - now).total_seconds())
    assert card_data.ttl == pytest.approx(expected_ttl, abs=1)
    assert card_data.end_at == end_at


def test_fill_times_persistent_card(default_card_data):
    card_data = CardModel(**default_card_data, persist=True)
    assert card_data.ttl is None
    assert card_data.end_at is None


def test_fill_times_invalid_end_at_in_past(default_card_data):
    end_at = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    with pytest.raises(ValueError, match="end_at must be in the future when ttl is not provided"):
        CardModel(**default_card_data, end_at=end_at)


def test_fill_times_invalid_end_at_format(default_card_data):
    with pytest.raises(ValueError, match="Invalid datetime format for end_at"):
        CardModel(**default_card_data, end_at="invalid_format")
