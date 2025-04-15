"""
Card_models
"""
import json
import os
import uuid
from datetime import datetime, timezone
from typing import *

import redis
from fastapi.logger import logger
from pydantic import BaseModel, constr, model_validator, Field

from src import symbol


class CardModel(BaseModel):
    number: constr(pattern="^[a-zA-Z0-9]{8,128}$") = Field(
        ..., description="Card unique identification symbol"
    )
    name: Optional[constr(pattern="^[a-zA-Z0-9_-]{8,128}$")] = Field(
        None, description="Display name"
    )
    devices: List[str] = Field(
        ..., description="Bind the device list"
    )
    created_at: Optional[datetime] = Field(
        None,
        description="Created time. The system will automatically set to the current time."
    )
    start_at: datetime = Field(
        ...,
        description="Start time. The time when the card starts to take effect (judged by the application now >= start_at)"
    )
    end_at: Optional[datetime] = Field(
        None,
        description="End time."
    )
    owner_client_id: Optional[str] = Field(
        None,
        description="Client who owns the card. This is just a sign that is easy to manage and will not affect authentication."
    )

    @model_validator(mode="before")
    def fill_times(cls, values: dict) -> dict:
        now = datetime.now(tz=timezone.utc)
        # If 'created_at' is None, set it to the current time in UTC
        if values.get("created_at") is None:
            values["created_at"] = now
        # If 'start_at' is None, set it to the current time in UTC
        if values.get("start_at") is None:
            values["start_at"] = now
        return values

    @model_validator(mode="before")
    def uppercase_card_number(cls, values: dict) -> dict:
        # If 'number' exists and is not None, convert it to uppercase
        if "number" in values and values["number"]:
            values["number"] = values["number"].upper()
        return values

    @model_validator(mode="before")
    def validate_start_and_end(cls, values: dict) -> dict:
        start_at = values.get("start_at")
        end_at = values.get("end_at")
        # Validate that start_at is not later than end_at
        if start_at and end_at and start_at > end_at:
            raise ValueError("start_at cannot be later than end_at")
        return values


class CardAdd(CardModel):
    number: Optional[constr(min_length=8, max_length=128)]
    start_at: datetime | None = Field(
        None,
        description="Start time. The time when the card starts to take effect (judged by the application now >= start_at)"
    )
    end_at: datetime | None = Field(
        None,
        description="End time."
    )
    symbol_type: Optional[str] = Field(
        None,
        description=(
                "Barcode/QRCode type. After setting, the image base64 (default PNG) will be returned to the "
                "`symbol_image_base64` field. Supported types: " + ", ".join(
            symbol.SUPPORT_SYMBOLS) + " or null to disable."
        ),
        examples=symbol.SUPPORT_SYMBOLS
    )

    @model_validator(mode="before")
    def remove_created_at(cls, values: dict) -> dict:
        values.pop("created_at", None)
        return values


class CardQuery(BaseModel):
    number: str = Field(..., description="Card number to be queried")


class CardResponse(CardModel):
    symbol_image_base64: Optional[None] = Field(
        None,
        description="Card Barcode/QRCode image data in base64 format. Default PNG format."
    )


class CardIdentifyResponse(CardModel):
    message: str = Field(..., description="Response message")


class Card:
    def __init__(self, environment='STANDARD', redis_client=None):
        def _connect_to_redis(host=os.getenv('REDIS_HOST'), port=os.getenv("REDIS_PORT", 6379), db=0):
            try:
                connection = redis.StrictRedis(host=host, port=port, db=db)
                connection.ping()  # Test the connection
                logger.info("Successfully connected to Redis!")
                return connection
            except redis.ConnectionError as e:
                test_connection = redis.StrictRedis(host=host, port=port, db=db)
                if test_connection.ping():
                    logger.error("Redis connection test succeeded, but error occurred in primary connection.")
                print(f"Redis connection failed: {e}")
                raise

        self.environment = environment.upper()
        self.environment_config = {
            'STANDARD': 0,
            'SANDBOX': 1
        }
        if self.environment.upper() in self.environment_config:
            self.db = self.environment_config[self.environment]
        else:
            raise EnvironmentError(f"Invalid environment: {self.environment}")

        # Use provided redis client if available (for testing)
        if redis_client is not None:
            self.redis = redis_client
        else:
            self.redis = _connect_to_redis(
                db=self.db
            )

    def add_card(
            self,
            card: CardAdd,
    ) -> CardResponse:
        # Generate a card when there is no card number
        if not card.number:
            while True:
                card.number = f"{int(datetime.now().timestamp())}{uuid.uuid4().int % 10000:04}"
                if not self.redis.exists(card.number):
                    break
                else:
                    continue

        # If card exists
        if self.redis.exists(card.number):
            raise ValueError(f"Card with number {card.number} already exists.")

        # If `devices` field is empty list
        if len(card.devices) <= 0:
            raise ValueError("Devices cannot be empty.")

        card.name = card.name if card.name else card.number

        r = self.redis
        r.set(
            card.number, card.model_dump_json()
        )
        if card.owner_client_id:
            r.sadd(f"card_owner_cards:{card.owner_client_id.lower()}", card.number)

        return self.get_a_card(card.number, ignore_start_time=True)

    def get_a_card(self, card_number, allow_before_start: bool = False,
                   ignore_start_time: bool = False) -> CardResponse:
        """
        Retrieves and constructs a card object using the card number by fetching details
        from a Redis datastore. This function retrieves the data corresponding to the
        given card number and parses it to construct a CardModel instance containing
        the card details.

        For cards that do not reach start_at, they will not be returned.
        Unless you set param allow_before_start=True.

        :param ignore_start_time:
        :param allow_before_start:
        :param card_number: The card number used to fetch the card details
                           from the Redis datastore
        :type card_number: str
        :return: A CardModel object instantiated with the card details
        :rtype: CardModel
        """
        r = self.redis
        card_number = card_number.upper()

        if r.exists(card_number):
            card_data = json.loads(r.get(card_number))
            card = CardResponse(**card_data)
        else:
            raise ValueError(f"Card with number {card_number} not found.")

        # check start_time
        if not ignore_start_time:
            if not allow_before_start and not self.is_card_active(card):
                raise ValueError(f"Card with number {card_number} is not active.")

        return card

    def delete_a_card(self, card_number):
        r = self.redis
        card_number = card_number.upper()
        return r.delete(card_number)

    @staticmethod
    def is_card_active(card: CardModel) -> bool:
        """
        The cards used by the application layer enable judgment logic.
        Determines whether now has reached start_at.
        """
        # If card.start_at is naive (no tzinfo), assume its UTC
        if card.start_at.tzinfo is None:
            card_start_at = card.start_at.replace(tzinfo=timezone.utc)
        else:
            card_start_at = card.start_at

        # Compare current time in UTC with card_start_at
        return datetime.now(tz=timezone.utc) >= card_start_at

    def identify_by_sn_card(
            self,
            device_sn, card_number
    ):
        """
        Identifies whether a given device serial number is associated with a specific card
        number by checking the data stored in the Redis database. The function retrieves
        data associated with the card number from the Redis database. If such a record is
        found, it deserializes the stored JSON data and checks if the given device serial
        number is among the associated devices.

        :param device_sn: The serial number of the device to be checked.
        :type device_sn: str
        :param card_number: The card number serving as the key for the Redis database query.
        :type card_number: str
        :return: A boolean value indicating whether the device serial number is associated
                 with the card number.
        :rtype: bool
        """
        r = self.redis
        card_number = card_number.upper()

        if not r.exists(card_number):
            raise ValueError(f"Card with number {card_number} not found.")

        data = json.loads(r.get(card_number))
        return device_sn in data['devices']

    def get_cards_by_owner(self, owner_client_id: str) -> List[CardResponse]:
        key = f"card_owner_cards:{owner_client_id.lower()}"
        if not self.redis.exists(key):
            return []

        card_numbers = self.redis.smembers(key)
        cards = []
        for num in card_numbers:
            num = num.decode()
            try:
                cards.append(self.get_a_card(num))
            except Exception as e:
                logger.warning(f"Failed to load card {num}: {e}")
        return cards
