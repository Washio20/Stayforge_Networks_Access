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
    A pytest fixture that creates and returns a mock instance of a
    FakeStrictRedis. This can be used to simulate Redis operations
    in tests without requiring a real Redis server.

    :return: An instance of FakeStrictRedis
    :rtype: FakeStrictRedis
    """
    return FakeStrictRedis()


@pytest.fixture
def card(mock_redis):
    """
    This pytest fixture provides a pre-configured instance of the `Card` class for testing purposes.
    It sets up the `Card` instance with a mocked Redis backend to facilitate isolated and controlled
    testing of the functionality associated with Redis interactions in the `Card` class.

    :param mock_redis: A mocked Redis instance used to emulate Redis backend operations.
    :return: A `Card` instance configured with a mocked Redis backend.
    """
    card_instance = Card()

    card_instance.redis = mock_redis
    return card_instance


def truncate_to_minute(dt):
    """
    Truncate a given datetime object to the nearest minute, discarding
    seconds and microseconds.

    :param dt: A datetime object to be truncated
    :type dt: datetime.datetime
    :return: A datetime object with seconds and microseconds truncated
    :rtype: datetime.datetime
    """
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
    """
    Compares and outputs differences between the provided result data and the expected
    values for a specified start time, end time, and time-to-live (TTL). This function
    prints the comparison details for each parameter to the standard output.

    :param result: The result object containing properties `start_at`, `end_at`, and `ttl`.
    :type result: Any
    :param expect_start_at: The expected start time value.
    :type expect_start_at: Optional[datetime]
    :param expect_end_at: The expected end time value.
    :type expect_end_at: Optional[datetime]
    :param expect_ttl: The expected time-to-live value.
    :type expect_ttl: Optional[int]
    :return: None
    :rtype: None
    """
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
    Tests the addition of a card with only Time-to-Live (TTL) specified.

    This function validates that the card is added correctly with the given TTL
    and ensures that the output time parameters (`start_at`, `end_at`, and `ttl`)
    match the expected values provided in the test case. It allows verifying
    the card's lifecycle management logic in scenarios where only a TTL is defined.

    :param card: The card object or service to which a card will be added.
    :type card: CardService or similar
    :return: None
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
    Tests the functionality of adding a card with specified properties such as TTL
    (Time-To-Live) and start time, comparing the result to expected values for
    validation.

    :param card: The card object or system where the card is being added
    :type card: Card or similar system object
    :return: None, as this is a test function without return.
    :raises AssertionError: If the result does not match the expected TTL,
        start_at, or end_at values within the tolerances.
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
    Tests the functionality of adding a card with a specific time-to-live (TTL) and end time, and
    validates the resulting data against expected values. This function ensures the card's lifespan
    matches the expected parameters and tolerances.

    :param card: The card management object used to perform the add card operation.
    :type card: Card
    :return: None
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
    Tests the scenario where all fields required for a card are provided and
    valid. This function verifies the correctness of the card creation and
    ensures all computed values match the expected outcomes. The results
    are compared with the expected values, including `start_at`, `end_at`,
    and `ttl`.

    :param card: Instance of the Card-related class responsible for adding
        and managing cards.
    :return: None
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
    Tests the `add_card` function by providing a card with specific start and end times,
    then verifying if the returned card data matches the expected values. This includes
    checking the start time, end time, and time-to-live (ttl) against expected parameters.

    :param card: Instance of the class where the `add_card` method is being tested.
    :type card: Card
    :return: None
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
    This function tests the behavior of adding a card with specified `start_at`
    but without additional required attributes, ensuring proper exception
    handling for unsupported operations. The test ensures the system raises
    a ValueError when the card data provided does not meet the expected
    requirements.

    :param card: The card object used to perform the add operation.
    :type card: Any
    :return: None
    :rtype: NoneType
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
    Tests the creation of a card with specific `end_at` parameter using the provided
    card service. This function validates if the resulting card data meets the expected
    values for `start_at`, `end_at`, and `ttl`. Additionally, it ensures that the `ttl`
    is within a defined tolerance range, verifying proper behavior of the system.

    :param card: Instance of card service used to add and manage cards.
                 Must support `add_card` method that accepts card data.
    :type card: Object
    :return: None
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
    Test case to verify behavior when no time fields are provided during card addition.

    This function checks the scenario when a card is attempted to be added without
    time-related fields. It ensures that the appropriate exception is raised, and the
    expected message is printed to confirm that the system behaves as intended in this case.

    :param card: Instance of the card class used to manage card operations.
    :type card: Card
    :return: None
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
    Tests the functionality of adding a card with the `persist` flag set to True.

    This function verifies that when a card is added with the `persist` property set
    to True, it adheres to the expected behavior, such as ensuring that the `persist`
    attribute of the result is True and the `ttl` attribute is None. Additionally, it
    compares the output data with the expected start, end, and TTL values to ensure
    behavioral correctness. Assertions are used to validate the conditions.

    :param card: The card object to perform the addition operation on.
    :type card: Card
    :return: None
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
    Tests the functionality to ensure that adding a card with a duplicate card number
    raises an exception. This validates that the system properly handles cases where
    there is an attempt to add a card that already exists.

    :param card: The card management system instance being tested
    :type card: object
    :return: None
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


# Boundary test cases
def test_boundary_ttl_zero(card):
    """
    Verifies that the card addition functionality does not allow a `ttl` value of zero. The function
    attempts to add a card with a time-to-live (TTL) of zero and ensures the appropriate exception
    is raised, confirming the boundary condition is handled as expected.

    :param card: The object that implements the interface to add a card to the system.
    :type card: CardAdd
    :return: None
    :rtype: NoneType
    """
    card_data = CardAdd(
        number="TEST123466",
        devices=["device1"],
        ttl=0
    )

    try:
        card.add_card(card_data)
        assert False, "Zero TTL should raise an Exception"
    except AssertionError as e:
        print(f"Expected exception caught: {e}")
        assert True


def test_boundary_ttl_negative(card):
    """
    Tests the behavior of the `add_card` method when a card with a negative TTL is
    provided. Ensures that the method raises a ValueError, validating the
    appropriate handling of invalid TTL values.

    :param card: The `card` object under test which provides the `add_card`
        method to test card addition functionality with TTL constraints.
    :return: None
    """
    card_data = CardAdd(
        number="TEST123467",
        devices=["device1"],
        ttl=-1
    )

    try:
        card.add_card(card_data)
        assert False, "Negative TTL should raise an Exception"
    except ValueError as e:
        print(f"Expected exception caught: {e}")
        assert True


def test_boundary_ttl_large_value(card):
    """
    Tests the functionality of adding a card with a large TTL value to ensure the system handles
    large integer values for time-to-live (TTL) correctly. A 10-year TTL value is used in the
    test to verify boundary conditions.

    :param card: The card object on which the add_card method is being tested.
    :type card: Card
    :return: None
    """
    large_ttl = 10 * 365 * 24 * 3600  # 10 years in seconds
    card_data = CardAdd(
        number="TEST123468",
        devices=["device1"],
        ttl=large_ttl
    )

    result = card.add_card(card_data)
    assert result.ttl == large_ttl


# Invalid time combinations
def test_invalid_time_combination_end_before_start(card):
    """
    Test the scenario where the end time is set before the start time in the card
    data. This function attempts to add a card with an invalid time combination
    and expects a `ValidationError` to be raised.

    :param card: Card manager object responsible for handling card operations
                 and card data validation.
    :type card: Any
    :return: None
    """
    start_at = datetime.now(timezone.utc)
    end_at = start_at - timedelta(hours=1)

    try:
        card_data = CardAdd(
            number="TEST123469",
            devices=["device1"],
            start_at=start_at,
            end_at=end_at
        )

        card.add_card(card_data)
        assert False, "End time before start time should raise an Exception"
    except ValueError as e:
        print(f"Expected exception caught: {e}")
        assert True


# Timezone tests
def test_timezone_handling_utc(card):
    """
    Tests if the card addition process correctly handles `datetime` objects with
    UTC timezone information. This ensures that both the `start_at` and `end_at`
    fields in the card data retain the `timezone.utc` timezone information.

    :param card: The card object to which the card data is being added. This is
        expected to have a method `add_card` that processes a `CardAdd` object and
        returns an object containing `start_at` and `end_at` fields.
    :return: None. The function asserts that the timezone information for `start_at`
        and `end_at` in the card data are `timezone.utc`.
    """
    utc_time = datetime.now(timezone.utc)
    card_data = CardAdd(
        number="TEST123470",
        devices=["device1"],
        start_at=utc_time,
        ttl=3600
    )

    result = card.add_card(card_data)
    assert result.start_at.tzinfo == timezone.utc
    assert result.end_at.tzinfo == timezone.utc


def test_timezone_handling_different_timezones(card):
    """
    Tests the timezone handling for adding a card with a start time specified
    in a different timezone. Ensures the start and end times are correctly
    converted to UTC during the operation and verifies the correctness of
    the hour offset after conversion.

    :param card: The card service or object to be used for performing the
        card addition and retrieval operations. This should be an object
        that supports adding a card and provides the resulting card data.
    :return: None
    """
    # Create time in different timezone
    jst = timezone(timedelta(hours=9))
    jst_time = datetime.now(jst)

    card_data = CardAdd(
        number="TEST123472",
        devices=["device1"],
        start_at=jst_time,
        ttl=3600
    )

    result = card.add_card(card_data)
    assert result.start_at.tzinfo == timezone.utc
    assert result.end_at.tzinfo == timezone.utc
    # Verify the time was correctly converted to UTC
    assert result.start_at.hour == (jst_time.hour - 9) % 24
