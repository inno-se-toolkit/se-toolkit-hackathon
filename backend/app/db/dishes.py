# CRUD operations for Dish model

from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Optional

from .models.dish import Dish, DishCreate, DishUpdate

async def get_dishes(session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Dish]:
    result = await session.execute(select(Dish).offset(skip).limit(limit))
    return result.scalars().all()

async def get_dish(session: AsyncSession, dish_id: int) -> Optional[Dish]:
    return await session.get(Dish, dish_id)

async def create_dish(session: AsyncSession, dish_in: DishCreate) -> Dish:
    dish = Dish.from_orm(dish_in)
    session.add(dish)
    await session.commit()
    await session.refresh(dish)
    return dish

async def update_dish(session: AsyncSession, dish_id: int, dish_in: DishUpdate) -> Optional[Dish]:
    dish = await get_dish(session, dish_id)
    if not dish:
        return None
    dish_data = dish_in.dict(exclude_unset=True)
    for field, value in dish_data.items():
        setattr(dish, field, value)
    dish.updated_at = datetime.utcnow()
    session.add(dish)
    await session.commit()
    await session.refresh(dish)
    return dish

async def delete_dish(session: AsyncSession, dish_id: int) -> bool:
    dish = await get_dish(session, dish_id)
    if not dish:
        return False
    await session.delete(dish)
    await session.commit()
    return True
