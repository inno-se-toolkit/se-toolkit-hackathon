"""Handler for /help command."""

from .base import HandlerContext, HandlerResult

def handle_help(ctx: HandlerContext) -> HandlerResult:
    msg = (
        "MenuMate — Restaurant Allergen Assistant\n\n"
        "Commands:\n"
        "/start — Welcome message\n"
        "/help — This help\n"
        "/menu — Show all dishes\n"
        "/check <query> — Find safe dishes (e.g. /check no milk, vegan)\n\n"
        "Or just type a question in plain English, e.g.\n"
        "  \"I'm allergic to nuts and gluten\"\n"
        "  \"Show me vegan options\""
    )
    return HandlerResult.ok(msg)
