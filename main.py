from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

from card import identify_by_sn_card, add_card

app = FastAPI()


@app.post("/identify/json/{device_sn}")
async def identify_json(device_sn: str, request: Request):
    body = await request.json()
    card_number = body.get("card_number")

    if identify_by_sn_card(device_sn, card_number):
        return True

    raise False


@app.post("/identify/card_number_text/{device_sn}")
async def identify_json(device_sn: str, request: Request):
    body = await request.json()
    card_number = body.get("card_number")

    return identify_by_sn_card(device_sn, card_number)


@app.post("/identify/vguang/{device_sn}")
async def vguang_identify(device_sn: str, request: Request):
    body = await request.json()
    card_number = body.get("card_number")

    if identify_by_sn_card(device_sn, card_number):
        return PlainTextResponse(
            "code=0000"
        )

    raise False


@app.post("/add")
async def identify_json(request: Request):
    body = await request.json()
    return {
        'result': add_card(
            card_number=body.get("card_number"),
            card_name=body.get("card_name"),
            devices=body.get("devices"),
            ttl=body.get("ttl", 60 * 60 * 24),
            persist=body.get("persist", False)
        )
    }
