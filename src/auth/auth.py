"""
For auth0
"""

import requests
from fastapi import Request, HTTPException
from jose import jwt



from env import (
    AUTH0_DOMAIN,
    AUTH0_ALGORITHMS,
    AUTH0_API_IDENTIFIER
)

jwks_url = f'https://{AUTH0_DOMAIN}/.well-known/jwks.json'
jwks = requests.get(jwks_url).json()


def get_token_auth_header(request: Request):
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise HTTPException(status_code=401, detail="Authorization header is expected.")
    parts = auth.split()
    if parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization header must start with Bearer.")
    elif len(parts) == 1:
        raise HTTPException(status_code=401, detail="Token not found.")
    elif len(parts) > 2:
        raise HTTPException(status_code=401, detail="Authorization header must be Bearer token.")
    return parts[1]


def verify_jwt(token: str):
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = jwt.construct_rsa_public_key(key)
            break
    if not rsa_key:
        raise HTTPException(status_code=401, detail="Unable to find appropriate key.")
    return jwt.decode(token, rsa_key, algorithms=AUTH0_ALGORITHMS, audience=AUTH0_API_IDENTIFIER,
                      issuer=f'https://{AUTH0_DOMAIN}/')


def require_permission(permission: str):
    async def wrapper(request: Request):
        token = get_token_auth_header(request)
        payload = verify_jwt(token)
        permissions = payload.get("permissions", [])
        if permission not in permissions:
            raise HTTPException(status_code=403, detail="Permission not found.")

    return wrapper
