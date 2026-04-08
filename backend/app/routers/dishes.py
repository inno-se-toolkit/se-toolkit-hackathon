# Dishes router

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.database import get_session
from app.models.dish import DishCreate, DishPublic, DishUpdate, Dish
from app.db import dishes as dish_crud

router = APIRouter(prefix="/api/dishes", tags=["dishes"])

@router.get("/", response_model=List[DishPublic])
async def list_dishes(session: AsyncSession = Depends(get_session), skip: int = 0, limit: int = 100):
    return await dish_crud.get_dishes(session, skip, limit)

@router.post("/", response_model=DishPublic, status_code=status.HTTP_201_CREATED)
async def create_dish_endpoint(dish_in: DishCreate, session: AsyncSession = Depends(get_session)):
    return await dish_crud.create_dish(session, dish_in)

@router.put("/{dish_id}", response_model=DishPublic)
async def update_dish_endpoint(dish_id: int, dish_in: DishUpdate, session: AsyncSession = Depends(get_session)):
    updated = await dish_crud.update_dish(session, dish_id, dish_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Dish not found")
    return updated

@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish_endpoint(dish_id: int, session: AsyncSession = Depends(get_session)):
    ok = await dish_crud.delete_dish(session, dish_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Dish not found")
