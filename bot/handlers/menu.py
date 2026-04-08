"""Handler for /menu command — list all dishes."""

import asyncio
from .base import HandlerContext, HandlerResult
from bot.services.backend_client import BackendClient
from bot.config import load_config

def handle_menu(ctx: HandlerContext) -> HandlerResult:
    # Sync placeholder; async called in production
    return HandlerResult.ok("Use `/menu` or send a query to see dishes from our live menu.")

async def handle_menu_async(ctx: HandlerContext) -> HandlerResult:
    config = load_config(require_bot_token=False)
    if not config.backend_api_url:
        return HandlerResult.ok("Menu not available — backend not configured.")
    client = BackendClient(config.backend_api_url, config.backend_api_key or "")
    dishes = await client.get_dishes()
    if not dishes:
        return HandlerResult.ok("No dishes on the menu yet.")
    lines = [f"- {d.name} ({d.ingredients})" for d in dishes]
    return HandlerResult.ok("Menu:\n" + "\n".join(lines))
