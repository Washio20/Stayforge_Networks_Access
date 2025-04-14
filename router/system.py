"""
System routers
"""
import os
import uuid
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.responses import JSONResponse
from starlette.responses import PlainTextResponse
from uvicorn.config import logger

from card import Card
from env import (
    FOUNDRY_AUTH0_CLIENT_ID,
    AUTH0_API_IDENTIFIER, AUTH0_DOMAIN, FOUNDRY_AUTH0_CLIENT_SECRET
)

router = APIRouter(
    tags=["System"]
)


@router.get("/", include_in_schema=False)
async def healthcheck():
    try:
        Card()
    except Exception as e:
        tracer_code = str(uuid.uuid4()).replace("-", "")
        logger.error(f"ERROR TRACER CODE '{tracer_code}': {e}", exc_info=True)
        return PlainTextResponse(f"HTTP 500 ERROR ({tracer_code})", status_code=500)
    return PlainTextResponse("ok")


@router.get("/login", tags=['Auth'])
async def login(request: Request, org: Optional[str] = None):
    base_url = str(request.base_url)
    redirect_target = base_url + "callback"

    params = {
        "response_type": "code",
        "client_id": FOUNDRY_AUTH0_CLIENT_ID,
        "redirect_uri": redirect_target,
        "audience": AUTH0_API_IDENTIFIER,
        "scope": "openid profile email offline_access",
        "prompt": "consent"
    }

    if org:
        params["organization"] = org

    url = f"https://{AUTH0_DOMAIN}/authorize?{urlencode(params)}"

    return RedirectResponse(url=url, status_code=302)


@router.get("/logout", tags=['Auth'])
async def logout(request: Request):
    base_url = str(request.base_url)

    params = {
        "client_id": FOUNDRY_AUTH0_CLIENT_ID,
        "returnTo": 'https://www.stayforge.io'
    }

    url = f"https://{AUTH0_DOMAIN}/v2/logout?{urlencode(params)}"

    return RedirectResponse(url=url, status_code=302)


@router.get("/callback")
async def callback(request: Request, code: str = None):
    base_url = str(request.base_url)
    redirect_target = base_url + "callback"

    token_url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "grant_type": "authorization_code",
        "client_id": FOUNDRY_AUTH0_CLIENT_ID,
        "client_secret": FOUNDRY_AUTH0_CLIENT_SECRET,
        "code": code,
        "redirect_uri": redirect_target
    }

    token_data: dict = requests.post(token_url, json=payload).json()

    response = JSONResponse(token_data)
    access_token = token_data.get("access_token")
    access_token_expires_in = token_data.get("expires_in")
    refresh_token = token_data.get("refresh_token")
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=not os.getenv("DEBUG", False),
            path="/",
            max_age=30 * 24 * 60 * 60
        )

    if access_token:
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=not os.getenv("DEBUG", False),
            path="/",
            max_age=access_token_expires_in
        )

    return response
