# Dish model

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column, JSON
from pydantic import validator
import re

class DishBase(SQLModel):
    name: str = Field(index=True)
    ingredients: str
    allergens: str = Field(default="", description="Comma-separated allergens")
    is_vegan: bool = False
    is_gluten_free: bool = False

class Dish(DishBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class DishCreate(DishBase):
    pass

class DishUpdate(SQLModel):
    name: Optional[str] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    is_vegan: Optional[bool] = None
    is_gluten_free: Optional[bool] = None

class DishPublic(DishBase):
    id: int
    created_at: datetime
    updated_at: datetime

ALLERGEN_PATTERNS = {
    "milk": r"\bmilk\b|\bcheese\b|\bbutter\b|\byogurt\b|\bcream\b",
    "eggs": r"\begg\b|\beggs\b",
    "nuts": r"\bnut\b|\bnuts\b|\bpeanut\b|\bwalnut\b|\balmond\b|\bcashew\b",
    "gluten": r"\bgluten\b|\bwheat\b|\bbarley\b|\brye\b",
    "soy": r"\bsoy\b|\bsoya\b|\btofu\b",
}

def extract_allergens(allergen_str: str) -> set[str]:
    if not allergen_str:
        return set()
    return {a.strip().lower() for a in allergen_str.split(",") if a.strip()}

def dish_matches_query(dish: Dish, query: str) -> tuple[bool, str]:
    """Check if a dish is safe given an allergy/diet query.
    Returns (is_safe, reason)."""
    q = query.lower()
    # Vegan request
    if "vegan" in q and not dish.is_vegan:
        return False, "not vegan"
    # Gluten-free request
    if "gluten-free" in q or "gluten free" in q:
        if not dish.is_gluten_free:
            return False, "contains gluten"
    # Specific allergen exclusions
    for allergen, pattern in ALLERGEN_PATTERNS.items():
        if allergen in q:
            if re.search(pattern, dish.ingredients.lower()) or allergen in extract_allergens(dish.allergens.lower()):
                return False, f"contains {allergen}"
    return True, "safe"
