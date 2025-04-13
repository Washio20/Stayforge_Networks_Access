"""
.env
"""
import os

from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv('AUTH0_DOMAIN', 'auth.stayforge.io')
AUTH0_API_IDENTIFIER = os.getenv('AUTH0_API_IDENTIFIER', 'https://api.networks.stayforge.io')
AUTH0_ALGORITHMS = ['RS256']
AUTH0_NAMESPACE = os.getenv('AUTH0_NAMESPACE', 'https://identify.access.networks.stayforge.io')
FOUNDRY_AUTH0_CLIENT_ID = os.getenv('FOUNDRY_AUTH0_CLIENT_ID')
FOUNDRY_AUTH0_CLIENT_SECRET = os.getenv('FOUNDRY_AUTH0_CLIENT_SECRET')
AUTH0_AUDIENCE = os.getenv('AUTH0_AUDIENCE', 'https://api.networks.stayforge.io')