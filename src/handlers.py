"""
Telegram bot command handlers.
"""

import re
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from src.token_analysis import (
    analyze_token,
    analyze_dev_wallet,
    analyze_whale_holders,
    get_recent_whale_txs,
    analyze_pvp,
)
from src.api_services import (
    dexscreener_search,
    gecko_trending_base,
    gecko_new_pools_base,
)
from src.messages import (
    build_token_message,
    build_dev_message,
    build_holders_message,
    build_whale_txs_message,
    build_scan_message,
    build_trending_message,
    build_new_pairs_message,
    build_pvp_message,
)
from src.formatters import dexscreener_url, basescan_token_url

logger = logging.getLogger(__name__)

# Regex for Ethereum addresses
ETH_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


def _is_address(text: str) -> bool:
    return bool(ETH_ADDRESS_RE.match(text.strip()))


def _get_token_keyboard(address: str, pair_address: str = "") -> InlineKeyboardMarkup:
    """Inline keyboard for token actions."""
    buttons = [
        [
            InlineKeyboardButton("👨‍💻 Dev Wallet", callback_data=f"dev_{address}"),
            InlineKeyboardButton("🐋 Holders", callback_data=f"holders_{address}"),
        ],
        [
            InlineKeyboardButton("💸 Whale Txs", callback_data=f"whale_{address}"),
            InlineKeyboardButton("⚔️ PvP Check", callback_data=f"pvp_{address}"),
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{address}"),
        ],
        [
            InlineKeyboardButton(
                "📊 DexScreener",
                url=dexscreener_url(pair_address or address),
            ),
            InlineKeyboardButton(
                "🔍 Basescan", url=basescan_token_url(address)
            ),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════
#  COMMANDS
# ═══════════════════════════════════════════════════════════════


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    welcome = (
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 <b>DEXTRAL BOT</b> — Base Chain Research\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "Your <b>all-in-one research tool</b> for Base chain tokens.\n"
        "Track prices, analyze dev wallets, detect whales,\n"
        "check contract safety, and stay ahead of the market.\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 <b>COMMANDS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "🔬 /token <code>&lt;address&gt;</code>\n"
        "    Full token research report\n"
        "\n"
        "⚡ /scan <code>&lt;address&gt;</code>\n"
        "    Quick safety scan\n"
        "\n"
        "👨‍💻 /dev <code>&lt;address&gt;</code>\n"
        "    Deep dev wallet analysis\n"
        "\n"
        "🐋 /holders <code>&lt;address&gt;</code>\n"
        "    Top holders & concentration\n"
        "\n"
        "💸 /whale <code>&lt;address&gt;</code>\n"
        "    Recent whale transactions\n"
        "\n"
        "⚔️ /pvp <code>&lt;address&gt;</code>\n"
        "    Check for duplicate/copycat tokens\n"
        "\n"
        "🔥 /trending\n"
        "    Trending tokens on Base\n"
        "\n"
        "🆕 /new\n"
        "    Newly created pairs\n"
        "\n"
        "🔎 /search <code>&lt;name or symbol&gt;</code>\n"
        "    Search tokens by name\n"
        "\n"
        "❓ /help\n"
        "    Show this message\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>TIP:</b> Just paste a contract address to get\n"
        "a full report instantly!\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(welcome, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await cmd_start(update, context)


async def cmd_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /token <address> — full research report."""
    if not context.args:
        await update.message.reply_text(
            "❌ Please provide a token address.\n"
            "Usage: <code>/token 0x...</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    address = context.args[0].strip()
    if not _is_address(address):
        await update.message.reply_text("❌ Invalid Base address format.")
        return

    msg = await update.message.reply_text("🔍 Analyzing token... Please wait.")

    try:
        report = await analyze_token(address)
        text = build_token_message(report)
        keyboard = _get_token_keyboard(address, report.pair_address)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /token: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error analyzing token: {str(e)[:200]}")


async def cmd_scan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /scan <address> — quick safety scan."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/scan 0x...</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    address = context.args[0].strip()
    if not _is_address(address):
        await update.message.reply_text("❌ Invalid address format.")
        return

    msg = await update.message.reply_text("⚡ Quick scanning...")

    try:
        report = await analyze_token(address)
        text = build_scan_message(report)
        keyboard = _get_token_keyboard(address, report.pair_address)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /scan: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error scanning token: {str(e)[:200]}")


async def cmd_dev(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /dev <address> — dev wallet deep dive."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/dev 0x...</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    address = context.args[0].strip()
    if not _is_address(address):
        await update.message.reply_text("❌ Invalid address format.")
        return

    msg = await update.message.reply_text("👨‍💻 Analyzing dev wallet...")

    try:
        # Get token symbol first
        report = await analyze_token(address)
        dev_info = await analyze_dev_wallet(address)
        text = build_dev_message(dev_info, address, report.symbol)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /dev: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


async def cmd_holders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /holders <address> — holder analysis."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/holders 0x...</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    address = context.args[0].strip()
    if not _is_address(address):
        await update.message.reply_text("❌ Invalid address format.")
        return

    msg = await update.message.reply_text("🐋 Analyzing holders...")

    try:
        report = await analyze_token(address)
        holder_info = await analyze_whale_holders(address)
        text = build_holders_message(holder_info, address, report.symbol)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /holders: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


async def cmd_whale(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /whale <address> — recent whale transactions."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/whale 0x...</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    address = context.args[0].strip()
    if not _is_address(address):
        await update.message.reply_text("❌ Invalid address format.")
        return

    msg = await update.message.reply_text("💸 Finding whale transactions...")

    try:
        report = await analyze_token(address)
        whale_txs = await get_recent_whale_txs(address)
        text = build_whale_txs_message(whale_txs, report.symbol)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /whale: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


async def cmd_trending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /trending — trending tokens on Base."""
    msg = await update.message.reply_text("🔥 Fetching trending tokens...")

    try:
        pools = await gecko_trending_base()
        text = build_trending_message(pools)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /trending: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


async def cmd_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /new — newly created pairs on Base."""
    msg = await update.message.reply_text("🆕 Fetching new pairs...")

    try:
        pools = await gecko_new_pools_base()
        text = build_new_pairs_message(pools)
        await msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /new: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /search <query> — search tokens by name/symbol."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/search DEGEN</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🔎 Searching for '{query}'...")

    try:
        pairs = await dexscreener_search(query)
        if not pairs:
            await msg.edit_text(f"❌ No tokens found for '{query}' on Base.")
            return

        lines = [
            f"{'━' * 32}",
            f"🔎 <b>Search Results for '{query}'</b>",
            f"{'━' * 32}",
            "",
        ]

        for i, p in enumerate(pairs[:8], 1):
            bt = p.get("baseToken", {})
            name = bt.get("name", "Unknown")
            symbol = bt.get("symbol", "?")
            addr = bt.get("address", "")
            price = float(p.get("priceUsd", 0) or 0)
            liq = float(p.get("liquidity", {}).get("usd", 0) or 0)
            mc = float(p.get("marketCap", 0) or 0)
            from src.formatters import fmt_price as fp, fmt_number as fn

            lines.append(
                f"{i}. <b>{name}</b> (${symbol})\n"
                f"    💰 {fp(price)} │ MC {fn(mc)} │ Liq {fn(liq)}\n"
                f"    📋 <code>{addr}</code>"
            )
            lines.append("")

        lines.append("💡 Copy an address and use /token to get a full report")
        lines.append(f"{'━' * 32}")

        await msg.edit_text(
            "\n".join(lines),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Error in /search: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


async def cmd_pvp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pvp <address> — check for duplicate/copycat tokens."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: <code>/pvp 0x...</code>\n"
            "Checks if other tokens with the same name/symbol exist on Base.",
            parse_mode=ParseMode.HTML,
        )
        return

    address = context.args[0].strip()
    if not _is_address(address):
        await update.message.reply_text("❌ Invalid address format.")
        return

    msg = await update.message.reply_text("⚔️ Running PvP analysis... Searching for duplicates...")

    try:
        pvp_info = await analyze_pvp(address)
        text = build_pvp_message(pvp_info)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Full Token Report", callback_data=f"refresh_{address}")]
        ])
        await msg.edit_text(
            text, parse_mode=ParseMode.HTML,
            reply_markup=keyboard, disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error(f"Error in /pvp: {e}", exc_info=True)
        await msg.edit_text(f"❌ Error: {str(e)[:200]}")


# ═══════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER (Inline Keyboard Buttons)
# ═══════════════════════════════════════════════════════════════


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if not data:
        return

    if data.startswith("dev_"):
        address = data[4:]
        await query.edit_message_text("👨‍💻 Analyzing dev wallet...")
        try:
            report = await analyze_token(address)
            dev_info = await analyze_dev_wallet(address)
            text = build_dev_message(dev_info, address, report.symbol)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Token", callback_data=f"refresh_{address}")]
            ])
            await query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True,
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)[:200]}")

    elif data.startswith("holders_"):
        address = data[8:]
        await query.edit_message_text("🐋 Analyzing holders...")
        try:
            report = await analyze_token(address)
            holder_info = await analyze_whale_holders(address)
            text = build_holders_message(holder_info, address, report.symbol)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Token", callback_data=f"refresh_{address}")]
            ])
            await query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True,
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)[:200]}")

    elif data.startswith("whale_"):
        address = data[6:]
        await query.edit_message_text("💸 Finding whale transactions...")
        try:
            report = await analyze_token(address)
            whale_txs = await get_recent_whale_txs(address)
            text = build_whale_txs_message(whale_txs, report.symbol)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Token", callback_data=f"refresh_{address}")]
            ])
            await query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True,
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)[:200]}")

    elif data.startswith("pvp_"):
        address = data[4:]
        await query.edit_message_text("⚔️ Running PvP analysis...")
        try:
            pvp_info = await analyze_pvp(address)
            text = build_pvp_message(pvp_info)
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back to Token", callback_data=f"refresh_{address}")]
            ])
            await query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True,
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)[:200]}")

    elif data.startswith("refresh_"):
        address = data[8:]
        await query.edit_message_text("🔄 Refreshing...")
        try:
            report = await analyze_token(address)
            text = build_token_message(report)
            keyboard = _get_token_keyboard(address, report.pair_address)
            await query.edit_message_text(
                text, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True,
            )
        except Exception as e:
            await query.edit_message_text(f"❌ Error: {str(e)[:200]}")


# ═══════════════════════════════════════════════════════════════
#  MESSAGE HANDLER — Auto-detect pasted addresses
# ═══════════════════════════════════════════════════════════════


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle plain text messages — auto-detect contract addresses."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()

    # Check if the message is a contract address
    if _is_address(text):
        msg = await update.message.reply_text("🔍 Address detected! Analyzing...")
        try:
            report = await analyze_token(text)
            response = build_token_message(report)
            keyboard = _get_token_keyboard(text, report.pair_address)
            await msg.edit_text(
                response, parse_mode=ParseMode.HTML,
                reply_markup=keyboard, disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Error in auto-detect: {e}", exc_info=True)
            await msg.edit_text(f"❌ Error: {str(e)[:200]}")
