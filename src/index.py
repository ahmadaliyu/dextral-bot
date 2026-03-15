"""
DEXTRAL BOT — Main entry point.
Advanced Base chain token research Telegram bot.
"""

import logging
import sys

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from src.config import config
from src.handlers import (
    cmd_start,
    cmd_help,
    cmd_token,
    cmd_scan,
    cmd_dev,
    cmd_holders,
    cmd_whale,
    cmd_pvp,
    cmd_trending,
    cmd_new,
    cmd_search,
    callback_handler,
    message_handler,
)

# ─── Logging ──────────────────────────────────────────────────

log_handlers = [logging.StreamHandler(sys.stdout)]
try:
    log_handlers.append(logging.FileHandler("dextral.log", encoding="utf-8"))
except (OSError, PermissionError):
    pass  # Skip file logging on platforms like Render

logging.basicConfig(
    format="%(asctime)s │ %(name)-20s │ %(levelname)-8s │ %(message)s",
    level=logging.INFO,
    handlers=log_handlers,
)
# Silence noisy libs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("dextral")


# ─── Boot ─────────────────────────────────────────────────────

def main() -> None:
    """Start the bot."""
    if not config.BOT_TOKEN or config.BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error(
            "❌  TELEGRAM_BOT_TOKEN is not set!\n"
            "    1. Talk to @BotFather on Telegram to create a bot\n"
            "    2. Copy the token\n"
            "    3. Create a .env file: cp .env.example .env\n"
            "    4. Paste the token into .env"
        )
        sys.exit(1)

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  🤖  DEXTRAL BOT — Starting up...")
    logger.info("  🔗  Network: Base (Chain ID 8453)")
    logger.info(f"  🌐  RPC: {config.BASE_RPC_URL}")
    logger.info(f"  🐋  Whale threshold: ${config.WHALE_THRESHOLD_USD:,.0f}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Build the application
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    # ── Register command handlers ─────────────────────────────
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("token", cmd_token))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("dev", cmd_dev))
    app.add_handler(CommandHandler("holders", cmd_holders))
    app.add_handler(CommandHandler("whale", cmd_whale))
    app.add_handler(CommandHandler("pvp", cmd_pvp))
    app.add_handler(CommandHandler("trending", cmd_trending))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("search", cmd_search))

    # ── Inline keyboard callback handler ──────────────────────
    app.add_handler(CallbackQueryHandler(callback_handler))

    # ── Plain text message handler (auto-detect addresses) ────
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    # ── Start polling ─────────────────────────────────────────
    logger.info("✅  Bot is running! Listening for messages...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
