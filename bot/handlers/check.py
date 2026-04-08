"""Handler for /check command — find safe dishes."""

import asyncio
from .base import HandlerContext, HandlerResult
from bot.services.backend_client import BackendClient
from bot.config import load_config

def handle_check(ctx: HandlerContext) -> HandlerResult:
    query = (ctx.args or "").strip()
    if not query:
        return HandlerResult.ok("Usage: /check <allergy or diet>\nExample: /check no milk")
    return HandlerResult.ok(f"Query: '{query}'\n(Full check runs in async/production mode)")

async def handle_check_async(ctx: HandlerContext) -> HandlerResult:
    query = (ctx.args or "").strip()
    if not query:
        return HandlerResult.ok("Please provide a query. Example: /check no milk")
    config = load_config(require_bot_token=False)
    if not config.backend_api_url:
        return HandlerResult.ok("Backend not configured.")
    client = BackendClient(config.backend_api_url, config.backend_api_key or "")
    safe_dishes = await client.check_dishes(query)
    if not safe_dishes:
        return HandlerResult.ok(f"No dishes match your request: '{query}'")
    lines = []
    for d in safe_dishes:
        tags = []
        if d.is_vegan: tags.append("Vegan")
        if d.is_gluten_free: tags.append("GF")
        tagstr = f" [{', '.join(tags)}]" if tags else ""
        line = f"• {d.name}{tagstr}: {d.ingredients}"
        if d.allergens:
            line += f"\n  Allergens: {d.allergens}"
        lines.append(line)
    return HandlerResult.ok("Safe dishes:\n" + "\n".join(lines))
