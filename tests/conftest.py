import sys
import os
import pytest
import fakeredis
from unittest.mock import patch

# Add the project root directory to Python's import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_redis_connection():
    """Create a fake Redis server for testing."""
    fake_redis = fakeredis.FakeStrictRedis()
    with patch('redis.StrictRedis', return_value=fake_redis):
        yield fake_redis 