"""
Redis Connector
"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
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
    ttl: Optional[int] = Field(
        None, description="TTL (seconds) in Redis. If there is a setting, it is the priority basis."
    )
    start_at: Optional[datetime] = Field(
        None, description="The time when the card starts to take effect (judged by the application now >= start_at)"
    )
    end_at: Optional[datetime] = Field(
        None,
        description="End time (if there is no TTL, it is used to calculate TTL). If TTL is set, then the value of TTL will be preferred."
    )
    persist: bool = Field(
        False, description="Whether to persist the card (if True, TTL is not set)"
    )
    created_at: Optional[datetime] = Field(
        None, description="Create time"
    )
    owner_client_id: Optional[str] = Field(
        None,
        description="Client who owns the card. This is just a sign that is easy to manage and will not affect authentication."
    )

    @model_validator(mode="before")
    def fill_times(cls, values: dict) -> dict:
        now = datetime.now(tz=timezone.utc)

        # If created_at is None, set it to now
        if values.get("created_at") is None:
            values["created_at"] = now

        # If start_at is None, set it to now
        if values.get("start_at") is None:
            values["start_at"] = now

        start_at = values["start_at"]
        end_at = values.get("end_at")
        ttl = values.get("ttl")
        persist = values.get("persist", False)

        # Convert end_at from string to datetime if necessary
        if isinstance(end_at, str):
            try:
                end_at = datetime.fromisoformat(end_at)
                values["end_at"] = end_at
            except ValueError:
                raise ValueError("Invalid datetime format for end_at")

        if persist:
            values["ttl"] = None
            return values

        if ttl is not None:
            values["end_at"] = start_at + timedelta(seconds=ttl)
            return values

        if end_at is not None:
            if end_at <= now:
                raise ValueError("end_at must be in the future when ttl is not provided")
            delta = (end_at - now).total_seconds()
            values["ttl"] = int(delta)
            return values

        values["ttl"] = None
        return values

    @model_validator(mode="before")
    def uppercase_card_number(cls, values: dict) -> dict:
        if "number" in values and values["number"]:
            values["number"] = values["number"].upper()
        return values

    @model_validator(mode="before")
    def validate_start_and_end(cls, values: dict) -> dict:
        start_at = values.get("start_at")
        end_at = values.get("end_at")

        if start_at and end_at and start_at > end_at:
            raise ValueError("start_at cannot be later than end_at")
        return values


class CardAdd(CardModel):
    number: Optional[constr(min_length=8, max_length=128)]
    symbol_type: Optional[str] = Field(
        None,
        description=f"Barcode/QRCode type. "
                    f"After setting, the image base64 (default PNG) will be returned to the `symbol_image_base64` field. "
                    f"\rSupported types: `{'`, `'.join(symbol.SUPPORT_SYMBOLS)}` or `null` to disable.",
        examples=symbol.SUPPORT_SYMBOLS
    )


class CardQuery(BaseModel):
    number: str = Field(..., description="Card number to be queried")


class CardResponse(CardModel):
    symbol_image_base64: str = Field(
        ...,
        description="Card Barcode/QRCode image data in base64 format. Default PNG format."
    )


class CardIdentifyResponse(CardModel):
    message: str = Field(..., description="Response message")


class Card:
    def __init__(self, environment='STANDARD'):
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

        self.redis = _connect_to_redis(
            db=self.db
        )

    def add_card(
            self,
            card: CardAdd = CardAdd(
                number=None,
                name=None,
                devices=[],
                ttl=60 * 60 * 24,
                persist=False,
                created_at=datetime.now(tz=timezone.utc),
                owner_client_id=None
            ),
    ) -> CardModel:
        """
        Adds a new card to the storage system, updating or validating its details as necessary.

        The function ensures the card has a unique number, validates required fields, and stores
        the card data into the Redis database. Additionally, it associates the card with an owner
        if provided, manages the card's expiration or persistence based on the configuration, and
        guarantees adherence to the constraints defined.

        :param card: The card object containing the properties such as number, name, associated devices,
            time-to-live duration, persistence flag, creation time, and owner client ID.
        :type card: CardAdd

        :return: The card object as created and stored in the system.
        :rtype: CardModel
        """
        card.number = card.number.upper()

        # Check whether the time unit has been transmitted
        if card.ttl in [None, 0, -1] \
                and card.persist == False \
                and card.end_at is None:
            raise ValueError(
                "TTL, Persist and End_at cannot all be None. "
                "You must provide a time unit for the card to expire. Or set persist = true."
            )

        # If ttl does not exist and persist is not true, ensure end_at is provided
        if card.ttl is None and not card.persist and card.end_at is None:
            raise ValueError("When ttl is not set and persist is False, end_at must be provided.")

        # Generate a card when there is no card number
        if not card.number:
            for i in range(10):
                card.number = f"{int(datetime.now().timestamp())}{uuid.uuid4().int % 10000:04}"
                if not self.redis.exists(card.number):
                    break
                else:
                    continue
            else:
                raise ValueError("Failed to generate a unique card number.")

        # If card exists
        if self.redis.exists(card.number):
            raise ValueError(f"Card with number {card.number} already exists.")

        card.name = card.name if card.name else card.number.upper()

        r = self.redis
        r.set(
            card.number.upper(), card.model_dump_json()
        )
        if card.owner_client_id:
            r.sadd(f"card_owner_cards:{card.owner_client_id.lower()}", card.number.upper())
        if card.ttl:
            r.pexpire(card.number, card.ttl * 1000)

        if card.persist:
            r.persist(card.number)

        return self.get_a_card(card.number)

    def get_a_card(self, card_number, allow_before_start: bool = False) -> CardModel:
        """
        Retrieves and constructs a card object using the card number by fetching details
        from a Redis datastore. This function retrieves the data corresponding to the
        given card number and parses it to construct a CardModel instance containing
        the card details.

        For cards that do not reach start_at, they will not be returned.
        Unless you set param allow_before_start=True.

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
            card = CardModel(
                number=card_number,
                name=json.loads(r.get(card_number))['name'],
                devices=json.loads(r.get(card_number))['devices'],
                ttl=r.ttl(card_number),
                persist=json.loads(r.get(card_number))['persist']
            )
        else:
            raise ValueError(f"Card with number {card_number} not found.")

        # check start_time
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
        return datetime.now(tz=timezone.utc) >= card.start_at

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

    def get_cards_by_owner(self, owner_client_id: str) -> List[CardModel]:
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
