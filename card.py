"""
Redis Connector
"""
import hashlib
import json
import os
import uuid

import redis
from fastapi.logger import logger


def _connect_to_redis(host=os.getenv('REDIS_HOST', "localhost"), port=os.getenv("REDIS_PORT", 6379), db=0):
    try:
        connection = redis.StrictRedis(host=host, port=port, db=db)
        connection.ping()  # Test the connection
        logger("Successfully connected to Redis!")
        return connection
    except redis.ConnectionError as e:
        print(f"Redis connection failed: {e}")
        raise


def add_card(
        card_number=hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest(),
        card_name=None,
        devices: list = None,
        ttl=60 * 60 * 24,
        persist: bool = False
) -> (str, dict):
    """
    Adds a card to the Redis database, storing associated information such as the
    name, associated devices, and optionally setting a time-to-live (TTL) or persisting
    the key indefinitely.

    This function generates a default card number if none is provided. The card name
    defaults to a lowercase value of the card number if it is not specified. Devices
    can optionally be listed and stored along with the card in the database. The key
    can have a TTL expressed in seconds or persist without expiry if specified.

    :param card_number: The unique identifier for the card. Defaults to a SHA256
        hash of a newly generated UUID if not provided.
    :param card_name: The human-readable name of the card. If not specified, it
        defaults to the lowercase version of 'card_number'.
    :param devices: A list of device identifiers associated with this card.
    :param ttl: The time-to-live for the card in the database, in seconds. Defaults
        to 24 hours (60 * 60 * 24). If set to 0 or `None`, the card will not expire
        unless 'persist' is set to True.
    :param persist: A flag indicating whether the card should be persisted
        indefinitely in the database regardless of TTL value. Defaults to False.

    :return: A tuple containing:
        - The card number as a string.
        - A dictionary representation of the card details, including associated
          devices and the card name.
        - The remaining TTL in milliseconds or -1 if the card does not expire.
    """
    card_name = card_name if card_name else card_number.lower()
    devices = devices if devices else []

    r = _connect_to_redis()
    r.set(
        card_number, json.dumps({
            "name": card_name,
            "devices": devices,
        })
    )

    if ttl:
        r.pexpire(card_number, ttl * 1000)

    if persist:
        r.persist(card_number)

    return card_number, json.loads(r.get(card_number)), int(r.ttl(card_number))


def identify_by_sn_card(device_sn, card_number):
    """
    Identify if a device serial number (device_sn) is associated with a card number.

    This function retrieves data associated with a given card number from a Redis
    database and determines if a specified device serial number (device_sn) is
    registered to that card. The function leverages JSON parsing to process the
    data stored in Redis and checks for membership of the device_sn in the
    associated list of devices.


    :param device_sn: The serial number of the device to check in association
        with the card number.
    :type device_sn: str
        :param card_number: The card number to be looked up in the Redis database.
    :type card_number: str
    :return: A boolean value indicating whether the given device serial number is
        associated with the provided card number.
    :rtype: bool
    """
    r = _connect_to_redis()
    data = json.loads(r.get(card_number))

    return device_sn in data['devices']
