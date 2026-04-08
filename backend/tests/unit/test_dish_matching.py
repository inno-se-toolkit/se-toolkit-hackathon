"""Unit tests for dish allergen matching."""

import pytest
from app.models.dish import Dish, dish_matches_query


def make_dish(name, ingredients, allergens="", vegan=False, gf=False):
    return Dish(
        id=1,
        name=name,
        ingredients=ingredients,
        allergens=allergens,
        is_vegan=vegan,
        is_gluten_free=gf,
    )


@pytest.mark.asyncio
async def test_vegan_filter():
    dish_vegan = make_dish("Buddha Bowl", "quinoa, chickpeas, avocado", vegan=True)
    dish_meat = make_dish("Steak", "beef, herbs", vegan=False)
    assert dish_matches_query(dish_vegan, "vegan")[0] is True
    assert dish_matches_query(dish_meat, "vegan")[0] is False


@pytest.mark.asyncio
async def test_gluten_free_filter():
    dish_gf = make_dish("Salmon", "salmon, lemon", gf=True)
    dish_wheat = make_dish("Pasta", "wheat, tomato", allergens="gluten")
    assert dish_matches_query(dish_gf, "gluten-free")[0] is True
    assert dish_matches_query(dish_wheat, "gluten-free")[0] is False


@pytest.mark.asyncio
async def test_milk_allergen():
    dish = make_dish("Cheese Pizza", "wheat, cheese, tomato", allergens="milk, gluten")
    ok, reason = dish_matches_query(dish, "no milk")
    assert ok is False
    assert "milk" in reason.lower()
