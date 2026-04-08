"""Restaurant Allergen Telegram Bot — entry point."""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from bot.config import Config, load_config

# Command dispatch tables
CMD_HANDLERS = {}
ASYNC_CMD_HANDLERS = {}

# Import handlers after config is defined (at end of file)

from bot.handlers.start import handle_start
from bot.handlers.help import handle_help
from bot.handlers.menu import handle_menu, handle_menu_async
from bot.handlers.check import handle_check, handle_check_async
from bot.handlers.intent import handle_natural_language

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CMD_HANDLERS = {
    "start": handle_start,
    "help": handle_help,
    "menu": handle_menu,
    "check": handle_check,
}

ASYNC_CMD_HANDLERS = {
    "start": handle_start,
    "help": handle_help,
    "menu": handle_menu_async,
    "check": handle_check_async,
}


def parse_command(input_text: str) -> tuple[str, Optional[str]]:
    """Parse '/command args' into ('command', 'args')."""
    text = input_text.strip()
    if text.startswith("/"):
        text = text[1:]
    parts = text.split(maxsplit=1)
    return parts[0].lower(), parts[1] if len(parts) > 1 else None


async def run_handler_async(command: str, args: Optional[str] = None) -> str:
    handler = ASYNC_CMD_HANDLERS.get(command)
    if not handler:
        return f"Unknown command: /{command}\n\nUse /help to see available commands."
    try:
        result = handler(args or None)
        if asyncio.iscoroutine(result):
            result = await result
        return result.message
    except Exception as e:
        logger.exception(e)
        return f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(description="MenuMate Restaurant Allergen Telegram Bot")
    parser.add_argument("--test", type=str, help="Test a command or natural language query")
    args = parser.parse_args()

    if args.test:
        command, args_text = parse_command(args.test)
        output = asyncio.run(run_handler_async(command, args_text))
        print(output)
        return

    # Production Telegram mode
    from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
    from telegram import Update
    from telegram.ext import ContextTypes

    config = load_config()
    if not config.bot_token:
        logger.error("BOT_TOKEN not set — configure bot/.env.bot")
        sys.exit(1)

    async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        handler = CMD_HANDLERS["start"]
        ctx = ({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": None}
               if hasattr(handler, '__code__') and 'ctx' in handler.__code__.co_varnames else None)
        try:
            result = handler({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": None})
            if asyncio.iscoroutine(result):
                result = await result
            await update.message.reply_text(result.message, parse_mode="Markdown")
        except Exception:
            result = handle_start({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": None})
            await update.message.reply_text(result.message, parse_mode="Markdown")

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = handle_help({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": None})
        await update.message.reply_text(result.message, parse_mode="Markdown")

    async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = await handle_menu_async({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": None})
        await update.message.reply_text(result.message, parse_mode="Markdown")

    async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query_text = context.args[0] if context.args else None
        result = await handle_check_async({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": query_text})
        await update.message.reply_text(result.message, parse_mode="Markdown")

    async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = await handle_natural_language({"user_id": update.effective_user.id, "username": update.effective_user.username, "args": update.message.text})
        await update.message.reply_text(result.message, parse_mode="Markdown")

    # Build application
    app = ApplicationBuilder().token(config.bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("menu", cmd_menu))
    app.add_handler(CommandHandler("check", cmd_check))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    logger.info("Bot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
