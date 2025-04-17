# tests/test_add_card_api.py
import json
import random
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app
from router.card import router
from src.card import Card
from src.symbol import SUPPORT_SYMBOLS

app.include_router(router)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_card(mock_redis_connection):
    """Create a Card instance with mocked Redis."""
    with patch("router.card.Card", return_value=Card(redis_client=mock_redis_connection)):
        yield


def test_pd429f_417(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": "pdf417"
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))

    assert response.json()
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()


@pytest.mark.parametrize("symbol", SUPPORT_SYMBOLS)
def test_like_with_symbols(client, mock_card, symbol):
    request_data = {
        "number": f"{uuid.uuid4().hex}",
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": symbol
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["symbol_image_base64"] is None
