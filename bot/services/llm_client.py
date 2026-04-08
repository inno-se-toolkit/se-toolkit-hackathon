"""LLM API client for tool-calling style natural language understanding."""

import httpx, json, logging
from typing import Dict, List, Any, Optional

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "filter_dishes",
            "description": "Return dishes safe for given allergies/diet. Use when user asks about allergens, vegan, gluten-free, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User's allergy/diet query, e.g. 'no milk', 'vegan', 'gluten-free'"}
                },
                "required": ["query"]
            }
        }
    }
]

SYSTEM_PROMPT = """You are an assistant for a restaurant. Help guests find dishes that match their dietary needs (allergies, vegan, gluten-free, etc.). When asked, extract the restriction and call filter_dishes.

Keep replies concise and friendly."""

class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str = "qwen-coder"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self.base_url}/models", headers=self._headers)
                return r.status_code == 200
        except Exception:
            return False

    async def chat_with_tools(self, messages: List[Dict[str, Any]]) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto"
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=self._headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choice = data["choices"][0]["message"]
            if choice.get("tool_calls"):
                # For demo, we just echo back; real tool calling would execute filter_dishes
                return "I found some safe dishes for you! (tool call would happen here in production)"
            return choice.get("content", "")
