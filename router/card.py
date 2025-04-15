"""
Card's Routers
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import ValidationError

from src.card import CardAdd, CardModel, Card, CardQuery, CardResponse

router = APIRouter(
    prefix="/card",
    tags=["Card"],
)


@router.post("/")
async def get_a_card_information(
        card_info: CardQuery,
        x_environment: str = Header("standard", alias="X-Environment")
):
    card_number = card_info.get("card_number")
    try:
        return Card().get_a_card(card_number)
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail={"message": str(e)}
        )


@router.post(
    "/add", response_model=CardResponse, description="Add a new card to the system.",
    # dependencies=[Depends(require_permission("read:access"))]
)
async def create_a_card(
        card: CardAdd
):
    card_obj = Card()

    try:
        result = card_obj.add_card(card)
        return CardResponse(
            **result.model_dump()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"message": str(e)}
        )


@router.post("/add_many")
async def create_many_cards(
        cards: list[CardAdd],
        x_environment: str = Header("standard", alias="X-Environment")
):
    results = []
    card_obj = Card(environment=x_environment.upper())

    for card in cards:
        try:
            result = card_obj.add_card(card)
            results.append({"number": card.number, "status": "success", "result": result})
        except (ValidationError, ValueError) as e:
            results.append({"number": card.number, "status": "error", "message": str(e)})

    return {"results": results}


@router.get(
    "/owner/{owner_client_id}",
    response_model=list[CardModel],
    description="Get all cards owned by a specific owner (mark by `owner_client_id`). The owner ID is provided in the URL.",
    # x_environment=Header("standard", alias="X-Environment")
)
async def get_cards_by_owner(owner_client_id: str):
    try:
        return Card().get_cards_by_owner(owner_client_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"message": str(e)}
        )
