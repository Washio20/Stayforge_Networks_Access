import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from uvicorn.config import logger

from card import Card, CardIdentifyResponse, CardModel

app = FastAPI()


@app.get("/")
async def healthcheck():
    try:
        Card()
    except Exception as e:
        tracer_code = str(uuid.uuid4()).replace("-", "")
        logger.error(f"ERROR TRACER CODE '{tracer_code}': {e}", exc_info=True)
        return PlainTextResponse(f"HTTP 500 ERROR ({tracer_code})", status_code=500)

    return PlainTextResponse("ok")


@app.post("/card")
async def get_a_card_information(request: Request):
    json = await request.json()
    return Card().get_a_card(json.get("card_number"))


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


@app.post("/identify/json", response_model=CardIdentifyResponse)
@app.post("/identify/json/{device_sn}", response_model=CardIdentifyResponse)
async def identify_json(request: Request, device_sn: str = None):
    device_sn = device_sn or request.headers.get("X-Device-SN")
    json_data = await request.json()
    card_number = json_data.get("card_number").upper()

    card_obj = Card(environment=request.headers.get("X-Environment", "standard").upper())
    client_id = None

    print(device_sn, card_number)

    # Verify that the card owner or client_id is empty
    if client_id is not None and card_obj.get_a_card(card_number).owner_client_id != client_id:
        raise HTTPException(status_code=400, detail={
            "message": "Unable to be identify because owner is not true. Please check your token."
        })

    # Verify the card number paired the device SN
    if card_obj.identify_by_sn_card(device_sn, card_number):
        return CardIdentifyResponse(message="Successfully", **card_obj.get_a_card(card_number).model_dump())

    raise HTTPException(status_code=400, detail={
        "message": "Unable to be identify successfully."
    })


@app.post("/identify/vguang-m350/{device_sn}")
async def vguang_identify(device_sn: str, request: Request):
    raw_body = await request.body()
    text_content = raw_body.decode("utf-8")
    card_number = text_content.upper()

    print(device_sn, card_number)

    card_obj = Card(environment="standard".upper())

    # Verify the card number paired the device SN
    if card_obj.identify_by_sn_card(device_sn, card_number):
        return PlainTextResponse("code=0000")

    raise HTTPException(status_code=400, detail={
        "message": "Unable to be identify successfully."
    })
