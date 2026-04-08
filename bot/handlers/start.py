"""Handler for /start command."""

from .base import HandlerContext, HandlerResult

def handle_start(ctx: HandlerContext) -> HandlerResult:
    username = ctx.username or "friend"
    return HandlerResult.ok(
        f"Hey {username}! I'm MenuMate — your restaurant allergen assistant.\n\n"
        "I can help you:\n"
        "• /menu — list all dishes\n"
        "• /check <allergy> — find safe dishes\n"
        "• Ask in plain English: \"I'm allergic to milk\"\n\n"
        "Try: `/check no milk` or say \"What's vegan?\""
    )
