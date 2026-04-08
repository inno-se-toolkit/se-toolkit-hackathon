"""Natural language intent handler with LLM tool calling."""

import logging
from typing import List, Dict
from .base import HandlerContext, HandlerResult
from bot.services.llm_client import LLMClient, SYSTEM_PROMPT
from bot.services.backend_client import BackendClient
from bot.config import load_config

logger = logging.getLogger(__name__)

async def handle_natural_language(ctx: HandlerContext) -> HandlerResult:
    user_message = (ctx.args or "").strip()
    if not user_message:
        return HandlerResult.ok("Tell me your allergies or dietary preferences and I'll find safe dishes.")

    config = load_config(require_bot_token=False)

    # LLM path (if configured)
    if config.llm_api_key and config.llm_api_base_url:
        try:
            llm = LLMClient(config.llm_api_key, config.llm_api_base_url, config.llm_api_model or "qwen-coder")
            if await llm.health_check():
                messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_message}]
                response = await llm.chat_with_tools(messages)
                if response and len(response.strip()) > 5:
                    return HandlerResult.ok(response)
        except Exception as e:
            logger.exception("LLM call failed")

    # Fallback: direct API check
    if config.backend_api_url:
        try:
            client = BackendClient(config.backend_api_url, config.backend_api_key or "")
            safe = await client.check_dishes_raw(user_message)
            if safe:
                lines = []
                for d in safe:
                    tags = []
                    if d.get("is_vegan"): tags.append("Vegan")
                    if d.get("is_gluten_free"): tags.append("GF")
                    tagstr = f" [{', '.join(tags)}]" if tags else ""
                    line = f"• {d['name']}{tagstr}: {d['ingredients']}"
                    if d.get('allergens'): line += f"\n  Allergens: {d['allergens']}"
                    lines.append(line)
                return HandlerResult.ok("Safe dishes:\n" + "\n".join(lines))
            return HandlerResult.ok("No safe dishes found for your request.")
        except Exception as e:
            logger.exception("API check failed")
            return HandlerResult.ok(f"Could not check dishes: {e}")

    return HandlerResult.ok("Bot not fully configured (missing backend API or LLM keys).")
