# tests/test_add_card_api.py
import json
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from router.card import router
from src.card import Card

app.include_router(router)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_card(mock_redis_connection):
    """Create a Card instance with mocked Redis."""
    with patch("router.card.Card", return_value=Card(redis_client=mock_redis_connection)):
        yield


tolerance = 1


def test_start_time_end_time(client, mock_card):
    delay_start = 5  # seconds
    alive = 5
    card_number = "312BB66A69E6457CAC6EE51719ECAAF2"
    device_id = f"omg-my-room-{random.randint(101, 909)}"

    ### First, Create a card
    request_data = {
        "number": card_number,
        "name": f"omg_my_card_{card_number}",
        "devices": [
            device_id
        ],
        "start_at": (datetime.now(tz=timezone.utc) + timedelta(seconds=delay_start)).isoformat(),
        "end_at": (datetime.now(tz=timezone.utc) + timedelta(seconds=delay_start + alive)).isoformat()
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    response_timestamp = time.time()

    print(json.dumps(response.json(), indent=2))

    # Verify them: Normalize date strings to avoid format issues
    response_start_at = response.json()["start_at"].replace("Z", "+00:00")
    response_end_at = response.json()["end_at"].replace("Z", "+00:00")

    request_start_at = request_data["start_at"].replace("Z", "+00:00")
    request_end_at = request_data["end_at"].replace("Z", "+00:00")

    # Use normalized date strings for comparison
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["devices"] == request_data["devices"]
    assert response_start_at == request_start_at
    assert response_end_at == request_end_at

    ### Next, Test the availability of cards at different times
    v_request_data = response.json()["number"]
    v_header = {}

    # Before Start
    verify_before_start = client.post(
        f"/identify/vguang-m350/{device_id}", data=v_request_data, headers=v_header
    )
    # After Start
    time.sleep(
        delay_start
    )
    verify_after_start = client.post(
        f"/identify/vguang-m350/{device_id}", data=v_request_data, headers=v_header
    )
    # Before the End
    time.sleep(
        alive - tolerance
    )
    verify_before_end = client.post(
        f"/identify/vguang-m350/{device_id}", data=v_request_data, headers=v_header
    )
    # After the End
    time.sleep(
        tolerance
    )
    verify_after_end = client.post(
        f"/identify/vguang-m350/{device_id}", data=v_request_data, headers=v_header
    )

    print(verify_before_start.text)
    print(verify_after_start.text)
    print(verify_before_end.text)
    print(verify_after_end.text)

    assert verify_before_start.status_code != 200
    assert verify_after_start.status_code == 200
    assert verify_before_end.status_code == 200
    assert verify_after_end.status_code != 200
