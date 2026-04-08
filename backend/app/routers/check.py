# Allergen check endpoint

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.database import get_session
from app.models.dish import Dish, DishPublic, dish_matches_query

router = APIRouter(prefix="/api", tags=["check"])

class CustomerQuery(BaseModel):
    message: str

class SafeResult(BaseModel):
    safe: List[DishPublic]
    total: int
    info: Optional[str] = None

@router.post("/check", response_model=SafeResult)
async def check_dishes(query: CustomerQuery, session: AsyncSession = Depends(get_session)):
    """Return dishes that are safe for the given allergy/diet query."""
    if not query.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    dishes = []
    async with session.begin():
        result = await session.execute("SELECT * FROM dish")
        dishes = result.scalars().all()

    matched = []
    for dish in dishes:
        ok, reason = dish_matches_query(dish, query.message)
        if ok:
            matched.append(dish)

    return {"safe": matched, "total": len(dishes)}
