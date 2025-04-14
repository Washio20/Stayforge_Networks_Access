import os
import uuid
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.responses import PlainTextResponse, RedirectResponse
from pydantic import ValidationError
from starlette.responses import JSONResponse
from uvicorn.config import logger

from card import Card, CardIdentifyResponse, CardModel, CardQuery, CardAdd
from documents import load_master_doc
from env import (
    FOUNDRY_AUTH0_CLIENT_ID,
    AUTH0_API_IDENTIFIER, AUTH0_DOMAIN, FOUNDRY_AUTH0_CLIENT_SECRET
)
from src.auth.auth import require_permission

app = FastAPI(
    title="Stayforge Networks Access API",
    redoc_url="/docs",
    docs_url="/docs/swagger",
    version="1.0.0",
    description=load_master_doc(),
)


@app.get("/login", tags=['auth'])
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


@app.get("/logout", tags=['auth'])
async def logout(request: Request):
    base_url = str(request.base_url)

    params = {
        "client_id": FOUNDRY_AUTH0_CLIENT_ID,
        "returnTo": 'https://www.stayforge.io'
    }

    url = f"https://{AUTH0_DOMAIN}/v2/logout?{urlencode(params)}"

    return RedirectResponse(url=url, status_code=302)


@app.get("/callback")
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


@app.get("/", tags=["system"])
async def healthcheck():
    try:
        Card()
    except Exception as e:
        tracer_code = str(uuid.uuid4()).replace("-", "")
        logger.error(f"ERROR TRACER CODE '{tracer_code}': {e}", exc_info=True)
        return PlainTextResponse(f"HTTP 500 ERROR ({tracer_code})", status_code=500)
    return PlainTextResponse("ok")


@app.post("/card", tags=["card"])
async def get_a_card_information(card_info: CardQuery):
    card_number = card_info.get("card_number")
    try:
        return Card().get_a_card(card_number)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"message": str(e)}
        )


@app.post(
    "/card/add", response_model=CardModel, tags=["card"], description="Add a new card to the system.",
    # dependencies=[Depends(require_permission("read:access"))]
)
async def create_a_card(
        card: CardAdd,
        x_environment: str = Header("standard", alias="X-Environment")
):
    card.number = card.number.upper()
    card_obj = Card(environment=x_environment.upper())

    try:
        return card_obj.add_card(card)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"message": str(e)}
        )


@app.post("/card/add_many", tags=["card"])
async def create_many_cards(
        cards: list[CardModel],
        x_environment: str = Header("standard", alias="X-Environment")
):
    results = []
    card_obj = Card(environment=x_environment.upper())

    for card in cards:
        try:
            card.number = card.number.upper()
            result = card_obj.add_card(card)
            results.append({"number": card.number, "status": "success", "result": result})
        except (ValidationError, ValueError) as e:
            results.append({"number": card.number, "status": "error", "message": str(e)})

    return {"results": results}


@app.get(
    "/owner/{owner_client_id}",
    response_model=list[CardModel],
    tags=["card"],
    description="Get all cards owned by a specific owner (mark by `owner_client_id`). The owner ID is provided in the URL."
)
async def get_cards_by_owner(owner_client_id: str):
    try:
        return Card().get_cards_by_owner(owner_client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"message": str(e)}
        )


def verify_card(device_sn: str, card_number: str, environment: str = "STANDARD",
                client_id: Optional[str] = None) -> CardModel:
    card_obj = Card(environment=environment.upper())
    card_number = card_number.upper()

    card = card_obj.get_a_card(card_number)

    if not card_obj.is_card_active(card):
        raise HTTPException(status_code=400, detail={
            "message": "Card is not active yet (before start time)."
        })

    if client_id is not None and card.owner_client_id != client_id:
        raise HTTPException(status_code=400, detail={
            "message": "Unable to be identify because owner is not true. Please check your token."
        })

    if not card_obj.identify_by_sn_card(device_sn, card_number):
        raise HTTPException(status_code=400, detail={
            "message": "Unable to be identify successfully."
        })

    return card


@app.post(
    "/identify/json",
    response_model=CardIdentifyResponse,
    tags=["identify"],
    description="Identify a device by its serial number and card number. The serial number is provided in the X-Device-SN header."
)
@app.post(
    "/identify/json/{device_sn}",
    response_model=CardIdentifyResponse,
    tags=["identify"],
    description="Identify a device by its serial number and card number. The serial number is provided in the URL."
)
async def identify_json(
        card: CardQuery,
        device_sn: Optional[str] = None,
        x_device_sn: Optional[str] = Header(None, alias="X-Device-SN"),
        x_environment: str = Header("standard", alias="X-Environment")
):
    device_sn = device_sn or x_device_sn
    card_number = card.number.upper()

    try:
        card = verify_card(
            device_sn=device_sn,
            card_number=card_number,
            environment=x_environment,
            client_id=None
        )
        return CardIdentifyResponse(message="Successfully", **card.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)})


@app.post(
    "/identify/vguang-m350/{device_name}",
    tags=["identify", "identify:vguang"],
    description="API specifically open for vguang-m350. Only run in STANDARD environment."
)
async def vguang_identify(device_name: str, request: Request):
    raw_body = await request.body()
    try:
        text_content = raw_body.decode(request.headers.get('Content-Encoding', 'utf-8')).strip()
    except (LookupError, UnicodeDecodeError):
        text_content = None

    if text_content and all(
            c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            for c in text_content):
        card_number = text_content.upper()
    else:
        card_number = raw_body[::-1].hex().upper()

    try:
        verify_card(device_sn=device_name, card_number=card_number)
        return PlainTextResponse("code=0000")

    except ValueError as e:
        logger.info(f"{e}")
        raise HTTPException(status_code=404, detail={"message": str(e)})
