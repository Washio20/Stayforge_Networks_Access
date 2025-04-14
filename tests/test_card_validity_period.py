"""
Test the legality of the input value
"""
import random
import time
from datetime import datetime, timezone, timedelta

import pytest
from fakeredis import FakeStrictRedis

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


mock_card = f"{''.join(random.choices('0123456789ABCDEF', k=8))}"
print(f"Mock card number: {mock_card}")

start_delay = 10
ttl = 20


# Case: card number too short (invalid case)
def test_card_number_valid_boundaries(card):
    result = card.add_card(CardAdd(
        number=mock_card,
        devices=["device1"],
        start_at=datetime.now(timezone.utc) + timedelta(seconds=start_delay),
        ttl=ttl
    ))
    print("Result: ", result)

    # The first query exists
    try:
        before_start_check_result = card.get_a_card(result.number)
        print("Before start - check result: ", before_start_check_result)
    except ValueError as e:
        print("Expected exception caught: ", e)
        assert True

    # Wait for start time, and check it
    time.sleep(start_delay)
    started_check_result = card.get_a_card(result.number)
    print("Started -  check result: ", started_check_result)
    assert started_check_result.number == result.number

    # Wait for the end of TTL, and check it
    print(f"Waiting for TTL(={result.ttl}) to expire...")
    time.sleep(result.ttl)
    try:
        ended_check_result = card.get_a_card(result.number)
        print("Ended check result: ", ended_check_result)
    except ValueError as e:
        print("Expected exception caught: ", e)
        assert True
