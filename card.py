"""
Redis Connector
"""
import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from typing import *

import redis
from fastapi.logger import logger
from pydantic import BaseModel, constr


class CardModel(BaseModel):
    number: constr(min_length=8, max_length=128)  # Key
    name: Optional[str]
    devices: List[str]
    ttl: int = 60 * 60 * 24
    persist: bool = False
    created_at: Optional[datetime] = datetime.now(tz=timezone.utc)
    owner_client_id: Optional[str] = None


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
            card: CardModel = CardModel(
                number=hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest(),
                name=None,
                devices=[],
                ttl=60 * 60 * 24,
                persist=False,
                created_at=datetime.now(tz=timezone.utc),
                owner_client_id=None,
            ),
            owner_client_id=None,
    ) -> CardModel:
        """
        Adds a new card to the system or updates an existing one based on the update_mode value.

        If the update_mode is set to False and a card with the same number already exists,
        a ValueError will be raised. Otherwise, the function stores the card in the Redis
        database. Optionally, the TTL (time-to-live) and persistence of the card can be
        configured.

        :param card: The card details to be added or updated. Defaults to a new dynamically
            created CardModel with a unique number, no name, empty devices list,
            24-hour TTL, and no persistence.
        :type card: CardModel

        :return: The CardModel object representing the added or updated card.
        :rtype: CardModel
        :raises ValueError: If `update_mode` is False and a card with the same
            number already exists in the database.
        """
        card.number = card.number.upper()

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

    def get_a_card(self, card_number) -> CardModel:
        """
        Retrieves and constructs a card object using the card number by fetching details
        from a Redis datastore. This function retrieves the data corresponding to the
        given card number and parses it to construct a CardModel instance containing
        the card details.

        :param card_number: The card number used to fetch the card details
                           from the Redis datastore
        :type card_number: str
        :return: A CardModel object instantiated with the card details
        :rtype: CardModel
        """
        r = self.redis
        card_number = card_number.upper()

        if r.exists(card_number):
            return CardModel(
                number=card_number,
                name=json.loads(r.get(card_number))['name'],
                devices=json.loads(r.get(card_number))['devices'],
                ttl=r.ttl(card_number),
                persist=json.loads(r.get(card_number))['persist']
            )
        else:
            raise ValueError(f"Card with number {card_number} not found.")

    def delete_a_card(self, card_number):
        r = self.redis
        card_number = card_number.upper()
        return r.delete(card_number)

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


class CardIdentifyResponse(CardModel):
    message: str
