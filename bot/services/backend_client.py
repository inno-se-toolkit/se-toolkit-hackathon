"""Backend API client adapted for the Restaurant Allergen service."""

import httpx
from typing import List, Optional
from .models import Dish

class BackendClient:
    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def get_dishes(self) -> List[Dish]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{self.base_url}/api/dishes")
            r.raise_for_status()
            data = r.json()
            return [Dish(**item) for item in data]

    async def check_dishes(self, message: str) -> List[Dish]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{self.base_url}/api/check", json={"message": message})
            r.raise_for_status()
            data = r.json()
            return [Dish(**item) for item in data.get("safe", [])]

    async def check_dishes_raw(self, message: str) -> List[dict]:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{self.base_url}/api/check", json={"message": message})
            r.raise_for_status()
            data = r.json()
            return data.get("safe", [])
