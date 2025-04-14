"""
Routers
"""
from fastapi import APIRouter

from . import (
    card,
    identify,
    system
)

router = APIRouter()

router.include_router(system.router)
router.include_router(card.router)
router.include_router(identify.router)
