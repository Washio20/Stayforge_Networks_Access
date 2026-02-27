"""
Identify Routers
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request
from starlette.responses import PlainTextResponse
from uvicorn.config import logger

from src.card import Card, CardIdentifyResponse, CardModel, CardQuery

router = APIRouter(
    prefix="/identify",
    tags=["Identify"],
)


def verify_card(device_sn: str, card_number: str, environment: str = "STANDARD",
                client_id: Optional[str] = None) -> CardModel:
    card_obj = Card(environment=environment.upper())
    card_number = card_number.upper() if card_number else None

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


@router.post(
    "/json",
    response_model=CardIdentifyResponse,
    description="Identify a device by its serial number and card number. The serial number is provided in the X-Device-SN header."
)
@router.post(
    "/json/{device_sn}",
    response_model=CardIdentifyResponse,
    description="Identify a device by its serial number and card number. The serial number is provided in the URL."
)
async def identify_json(
        card: CardQuery,
        device_sn: Optional[str] = None,
        x_device_sn: Optional[str] = Header(None, alias="X-Device-SN"),
        x_environment: str = Header("standard", alias="X-Environment")
):
    device_sn = device_sn or x_device_sn

    try:
        card = verify_card(
            device_sn=device_sn,
            card_number=card.number,
            environment=x_environment,
            client_id=None
        )
        return CardIdentifyResponse(message="Successfully", **card.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)})


@router.post(
    "/vguang-m350/{device_name}",
    tags=["Identify:vguang"],
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

