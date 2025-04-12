import uuid
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import ValidationError
from uvicorn.config import logger

from card import Card, CardIdentifyResponse, CardModel

app = FastAPI(
    title="Stayforge Networks Access API",
    docs_url="/docs",
)


@app.get("/", tags=["system"])
async def healthcheck():
    try:
        Card()
    except Exception as e:
        tracer_code = str(uuid.uuid4()).replace("-", "")
        logger.error(f"ERROR TRACER CODE '{tracer_code}': {e}", exc_info=True)
        return PlainTextResponse(f"HTTP 500 ERROR ({tracer_code})", status_code=500)

    return PlainTextResponse("ok")


@app.post("/card", tags=["card", "information"])
async def get_a_card_information(request: Request):
    json = await request.json()
    card_number = json.get("card_number")
    try:
        return Card().get_a_card(card_number)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"message": str(e)}
        )


@app.post("/card/add", response_model=CardModel, tags=["card", "add"])
async def create_a_card(request: Request):
    body = await request.json()
    body["number"] = body["number"].upper()

    card_obj = Card(
        environment=request.headers.get("X-Environment", "standard").upper(),
    )

    try:
        return card_obj.add_card(
            CardModel(
                **body
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"message": str(e)}
        )


@app.post("/card/add_many", tags=["card", "add", "many"])
async def create_many_cards(request: Request):
    body = await request.json()
    results = []
    environment = request.headers.get("X-Environment", "standard").upper()

    if not isinstance(body, list):
        raise HTTPException(status_code=400, detail={"message": "Payload must be a list of cards."})

    for item in body:
        try:
            item["number"] = item["number"].upper()
            card_obj = Card(environment=environment)
            card = CardModel(**item)
            result = card_obj.add_card(card)
            results.append({"number": card.number, "status": "success", "result": result})
        except (ValidationError, ValueError) as e:
            results.append({"number": item.get("number", "UNKNOWN"), "status": "error", "message": str(e)})

    return {"results": results}


@app.get(
    "/owner/{owner_client_id}", response_model=list[CardModel], tags=["card", "get"],
    description="Get all cards owned by a specific owner (mark by `owner_client_id`). The owner ID is provided in the URL."
)
async def get_cards_by_owner(
        owner_client_id: str
):
    card_obj = Card()
    try:
        return card_obj.get_cards_by_owner(owner_client_id)
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
    "/identify/json", response_model=CardIdentifyResponse, tags=["identify"],
    description="Identify a device by its serial number and card number. The serial number is provided in the X-Device-SN header."
)
@app.post(
    "/identify/json/{device_sn}", response_model=CardIdentifyResponse, tags=["identify"],
    description="Identify a device by its serial number and card number. The serial number is provided in the URL.")
async def identify_json(request: Request, device_sn: str = None):
    device_sn = device_sn or request.headers.get("X-Device-SN")
    json_data = await request.json()
    card_number = json_data.get("card_number").upper()

    try:
        card = verify_card(
            device_sn=device_sn,
            card_number=card_number,
            environment=request.headers.get("X-Environment", "standard"),
            client_id=None
        )
        return CardIdentifyResponse(message="Successfully", **card.model_dump())

    except ValueError as e:
        raise HTTPException(status_code=404, detail={"message": str(e)})


@app.post(
    "/identify/vguang-m350/{device_name}", tags=["identify", "vguang"],
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
