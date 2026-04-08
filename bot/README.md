# Restaurant Allergen Telegram Bot

Entry point with:
- Telegram bot mode (production)
- Test mode via --test flag (offline testing)
- LLM-powered natural language routing

Usage:
    uv run bot.py                  # Start Telegram bot
    uv run bot.py --test "/start"  # Test a command offline
    uv run bot.py --test "I'm allergic to milk"  # Test natural language
