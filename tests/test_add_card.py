# test_card_add.py
import pytest
from fakeredis import FakeStrictRedis
from pydantic import ValidationError

from card import Card, CardAdd


@pytest.fixture
def mock_redis():
    # Setup fake redis instance for testing without a real Redis server
    return FakeStrictRedis()


@pytest.fixture
def card(mock_redis):
    # Create and configure a Card instance with mocked redis backend
    card_instance = Card()
    card_instance.redis = mock_redis
    return card_instance


# Case: card number too short (invalid case)
def test_card_number_too_short(card):
    with pytest.raises(ValidationError):
        card_data = CardAdd(
            number="1234",  # Less than 8 characters, should be invalid
            devices=["device1"],
            ttl=60
        )
        card.add_card(card_data)


# Case: card number too long (invalid case)
def test_card_number_too_long(card):
    with pytest.raises(ValidationError):
        card_data = CardAdd(
            number="A" * 129,
            devices=["device1"],
            ttl=60
        )
        # Assume that ValueError will be thrown out when the card number does not meet the requirements
        card.add_card(card_data)


# Case: card number contains illegal characters (invalid case)
def test_card_number_illegal_characters(card):
    with pytest.raises(ValidationError):
        card_data = CardAdd(
            number="TEST#123",  # Contains illegal characters '#'
            devices=["device1"],
            ttl=60
        )
        # Assuming that illegal characters cause an error, throw out ValueError
        card.add_card(card_data)


# Case: valid card number using boundary of allowed characters count (8 and 128 characters)
def test_card_number_valid_boundaries(card):
    # Test 8 characters
    card_data_min = CardAdd(
        number="A1B2C3D4",  # Exactly 8 characters
        devices=["device1"],
        ttl=60
    )
    result_min = card.add_card(card_data_min)
    assert result_min.number == "A1B2C3D4"


    # Test 128 characters
    card_number_128 = "A" * 128
    card_data_max = CardAdd(
        number=card_number_128,
        devices=["device1"],
        ttl=60
    )
    result_max = card.add_card(card_data_max)
    assert result_max.number == card_number_128
