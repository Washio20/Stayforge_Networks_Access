# tests/test_add_card_api.py
import json
import random
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


def test_like_normal(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_at": (datetime.now() + timedelta(days=2)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": None
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["devices"] == request_data["devices"]
    assert response.json()["start_at"] == request_data["start_at"]
    assert response.json()["end_at"] == request_data["end_at"]
    assert response.json()["owner_client_id"] == request_data["owner_client_id"]


def test_only_number_devices(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ]
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["devices"] == request_data["devices"]
    assert datetime.fromisoformat(response.json()["start_at"]).replace(second=0, microsecond=0) == datetime.now(
        tz=timezone.utc).replace(second=0, microsecond=0)
    assert response.json()["end_at"] is None
    assert response.json()["owner_client_id"] is None


def test_only_number_devices_start_at(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": (datetime.now() + timedelta(days=1)).isoformat(),
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["devices"] == request_data["devices"]
    assert response.json()["start_at"] == request_data["start_at"]
    assert response.json()["end_at"] is None
    assert response.json()["owner_client_id"] is None


def test_only_number_devices_start_at_end_at(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_at": (datetime.now() + timedelta(days=2)).isoformat(),
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["devices"] == request_data["devices"]
    assert response.json()["start_at"] == request_data["start_at"]
    assert response.json()["end_at"] == request_data["end_at"]
    assert response.json()["owner_client_id"] is None


### About Number

def test_number_none(client, mock_card):
    request_data = {
        "number": None,
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": None
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] is not None


def test_number_too_short(client, mock_card):
    request_data = {
        "number": ''.join(random.choices('ABCDE12345', k=7)),
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": None
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_short"


def test_number_too_long(client, mock_card):
    request_data = {
        "number": ''.join(random.choices('ABCDE12345', k=129)),
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": None
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "string_too_long"


def test_number_invalid_character(client, mock_card):
    request_data = {
        "number": "ABCD_12345",
        "name": f"omg_my_card{uuid.uuid4().hex}",
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": datetime.now().isoformat(),
        "end_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "owner_client_id": "test_client",
        "symbol_type": None
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 400


### About Name

def test_name_none(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "name": None,
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ]
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["name"] == response.json()["number"]
    assert response.json()["devices"] == request_data["devices"]
    assert datetime.fromisoformat(response.json()["start_at"]).replace(second=0, microsecond=0) == datetime.now(
        tz=timezone.utc).replace(second=0, microsecond=0)
    assert response.json()["end_at"] is None
    assert response.json()["owner_client_id"] is None


### About Devices

def test_with_out_devices(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        # "devices": [
        #     f"omg-my-room-{random.randint(101, 909)}"
        # ]
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 422


def test_invalid_contact_devices_string(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": f"omg-my-room-{random.randint(101, 909)}"
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "list_type"


def test_invalid_contact_devices_empty_list(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": []
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 400


### About Start At & End_At

def test_only_end_at(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "start_at": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_at": (datetime.now() + timedelta(days=2)).isoformat(),
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["devices"] == request_data["devices"]
    assert response.json()["start_at"] == request_data["start_at"]
    assert response.json()["end_at"] == request_data["end_at"]
    assert response.json()["owner_client_id"] is None


### About Owner Client ID
def test_owner_client_none(client, mock_card):
    request_data = {
        "number": uuid.uuid4().hex,
        "devices": [
            f"omg-my-room-{random.randint(101, 909)}"
        ],
        "owner_client_none": None
    }
    headers = {"X-Environment": "standard"}
    response = client.post("/card/add", json=request_data, headers=headers)
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200
    assert response.json()["number"] == request_data["number"].upper()
    assert response.json()["owner_client_id"] == None
