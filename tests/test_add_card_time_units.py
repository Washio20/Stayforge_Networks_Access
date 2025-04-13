"""
Test the situation where users enter time on different occasions
TTL, Start_at & End_at
"""

from typing import Optional

import pytest
from fakeredis import FakeStrictRedis

from card import Card, CardAdd


@pytest.fixture
def mock_redis():
    """
    Fixture to create a fake Redis instance
    """
    return FakeStrictRedis()


@pytest.fixture
def card(mock_redis):
    """
    Fixture to create a Card instance with mocked Redis
    """
    card_instance = Card()

    card_instance.redis = mock_redis
    return card_instance


def truncate_to_minute(dt):
    return dt.replace(second=0, microsecond=0)


from datetime import datetime, timedelta, timezone

expect_ttl = 3600
expect_start_at = datetime.now(timezone.utc)
expect_end_at = expect_start_at + timedelta(seconds=expect_ttl)

ttl_tolerance = 10


def output_comparison_data(
        result,
        expect_start_at: Optional[datetime] = None,
        expect_end_at: Optional[datetime] = None,
        expect_ttl: Optional[int] = None,
):
    print("\r\n")
    print(f"ttl_tolerance = {ttl_tolerance}\r\n")
    print(
        "[start_at] \n"
        f"Expect: {expect_start_at} \n"
        f"Result: {result.start_at} \n"
    )
    print(
        "[end_at] \n"
        f"Expect: {expect_end_at} \n"
        f"Result: {result.end_at} \n"
    )
    print(
        "[ttl] \n"
        f"Expect: {expect_ttl} \n"
        f"Result: {result.ttl} \n"
    )
    print("\r\n")


# Case ①: ttl provided, no start_at, no end_at
def test_case_1_ttl_only(card):
    """
    Case ①: ttl provided, no start_at, no end_at
    Expected: start_at = now, end_at = start_at + ttl, Redis TTL is set
    """

    card_data = CardAdd(
        number="TEST123456",
        devices=["device1"],
        ttl=expect_ttl
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert truncate_to_minute(result.start_at) == truncate_to_minute(expect_start_at)
    assert truncate_to_minute(result.end_at) == truncate_to_minute(expect_end_at)
    assert abs(result.ttl - expect_ttl) <= ttl_tolerance, "TTL is outside the tolerated range."


# Case ②: ttl and start_at provided, no end_at
def test_case_2_ttl_and_start_at(card):
    """
    Case ②: ttl and start_at provided, no end_at
    Expected: using provided start_at; end_at = start_at + ttl, Redis TTL is set
    """
    card_data = CardAdd(
        number="TEST123457",
        devices=["device1"],
        ttl=expect_ttl,
        start_at=expect_start_at
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert truncate_to_minute(result.start_at) == truncate_to_minute(expect_start_at)
    assert truncate_to_minute(result.end_at) == truncate_to_minute(expect_end_at)
    assert abs(result.ttl - expect_ttl) <= ttl_tolerance, "TTL is outside the tolerated range."


# Case ③: ttl and end_at provided, no start_at
def test_case_3_ttl_and_end_at(card):
    """
    Case ③: ttl and end_at provided, no start_at
    Expected: using provided end_at; start_at = end_at - ttl, Redis TTL is set
    """
    card_data = CardAdd(
        number="TEST123458",
        devices=["device1"],
        ttl=expect_ttl,
        end_at=expect_end_at
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert truncate_to_minute(result.start_at) == truncate_to_minute(expect_start_at)
    assert truncate_to_minute(result.end_at) == truncate_to_minute(expect_end_at)
    assert abs(result.ttl - expect_ttl) <= ttl_tolerance, "TTL is outside the tolerated range."


# Case ④: ttl, start_at, and end_at provided
def test_case_4_all_fields_provided(card):
    """
    Case ④: ttl, start_at, and end_at provided
    Expected: using provided start_at and end_at; Redis TTL is set as provided
    """
    card_data = CardAdd(
        number="TEST123459",
        devices=["device1"],
        ttl=expect_ttl,
        start_at=expect_start_at,
        end_at=expect_end_at
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert truncate_to_minute(result.start_at) == truncate_to_minute(expect_start_at)
    assert truncate_to_minute(result.end_at) == truncate_to_minute(expect_end_at)
    assert abs(result.ttl - expect_ttl) <= ttl_tolerance, "TTL is outside the tolerated range."


# Case ⑤: start_at and end_at provided, no ttl
def test_case_5_start_at_and_end_at(card):
    """
    Case ⑤: start_at and end_at provided, no ttl
    Expected: ttl is computed as (end_at - start_at)
    """
    card_data = CardAdd(
        number="TEST123460",
        devices=["device1"],
        start_at=expect_start_at,
        end_at=expect_end_at
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert truncate_to_minute(result.start_at) == truncate_to_minute(expect_start_at)
    assert truncate_to_minute(result.end_at) == truncate_to_minute(expect_end_at)
    assert abs(result.ttl - expect_ttl) <= ttl_tolerance, "TTL is outside the tolerated range."


# Case ⑥: start_at provided only
def test_case_6_start_at_only(card):
    """
    Case ⑥: start_at provided only, no ttl, no end_at
    Expected: start_at is used; ttl and end_at remain None
    """
    card_data = CardAdd(
        number="TEST123461",
        devices=["device1"],
        start_at=expect_start_at
    )

    try:
        card.add_card(card_data)
    except ValueError as e:
        print("\r\n")
        print(f"Expected exception caught: {e} ,This result is in line with expectations!")
        assert True


# Case ⑦: end_at provided only
def test_case_7_end_at_only(card):
    """
    Case ⑦: end_at provided only, no ttl, no start_at
    Expected: end_at is used; ttl and start_at remain None
    """
    card_data = CardAdd(
        number="TEST123462",
        devices=["device1"],
        end_at=expect_end_at
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert truncate_to_minute(result.start_at) == truncate_to_minute(expect_start_at)
    assert truncate_to_minute(result.end_at) == truncate_to_minute(expect_end_at)
    assert abs(result.ttl - expect_ttl) <= ttl_tolerance, "TTL is outside the tolerated range."


# Case ⑧: no time fields provided
def test_case_8_no_time_fields(card):
    """
    Case ⑧: no time fields provided
    Expected: start_at = now; ttl and end_at remain None
    """
    try:
        card_data = CardAdd(
            number="TEST123463",
            devices=["device1"]
        )
        card.add_card(card_data)
    except ValueError as e:
        print("\r\n")
        print(f"Expected exception caught: {e} ,This result is in line with expectations!")
        assert True


# persist flag is True
def test_persist_true(card):
    """
    Case: persist flag provided True
    Expected: persist is True and ttl is not set
    """
    card_data = CardAdd(
        number="TEST123464",
        devices=["device1"],
        persist=True
    )

    result = card.add_card(card_data)

    output_comparison_data(
        result,
        expect_start_at,
        expect_end_at,
        expect_ttl,
    )

    assert result.persist is True
    assert result.ttl is None


# Duplicate card number
def test_duplicate_card_number(card):
    """
    Case: duplicate card number
    Expected: adding a card with an existing number should raise an Exception
    """
    card_data = CardAdd(
        number="TEST123465",
        devices=["device1"],
        ttl=3600
    )

    card.add_card(card_data)

    try:
        card.add_card(card_data)
        assert False, "Duplicate card number did not raise an Exception."
    except Exception as e:
        print(f"Expected exception caught: {e}")
