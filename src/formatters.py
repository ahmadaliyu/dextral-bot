"""
Formatting helpers — numbers, addresses, percentages, time deltas.
"""

from datetime import datetime, timezone


def fmt_number(n: float, decimals: int = 2) -> str:
    """Format large numbers: 1.2M, 3.4B, etc."""
    if n is None:
        return "N/A"
    abs_n = abs(n)
    sign = "-" if n < 0 else ""
    if abs_n >= 1_000_000_000:
        return f"{sign}${abs_n / 1_000_000_000:,.{decimals}f}B"
    if abs_n >= 1_000_000:
        return f"{sign}${abs_n / 1_000_000:,.{decimals}f}M"
    if abs_n >= 1_000:
        return f"{sign}${abs_n / 1_000:,.{decimals}f}K"
    return f"{sign}${abs_n:,.{decimals}f}"


def fmt_price(price: float) -> str:
    """Format token price with appropriate decimal places."""
    if price is None:
        return "N/A"
    if price == 0:
        return "$0"
    if price < 0.00000001:
        return f"${price:.12f}"
    if price < 0.0001:
        return f"${price:.8f}"
    if price < 0.01:
        return f"${price:.6f}"
    if price < 1:
        return f"${price:.4f}"
    return f"${price:,.2f}"


def fmt_percent(pct: float) -> str:
    """Format percentage with color emoji."""
    if pct is None:
        return "N/A"
    emoji = "🟢" if pct >= 0 else "🔴"
    return f"{emoji} {pct:+.2f}%"


def fmt_address(addr: str, chars: int = 6) -> str:
    """Shorten an address: 0x1234...abcd"""
    if not addr:
        return "N/A"
    return f"{addr[:chars]}...{addr[-4:]}"


def fmt_age(timestamp: int) -> str:
    """Human-readable age from unix timestamp."""
    if not timestamp:
        return "N/A"
    now = datetime.now(timezone.utc)
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    delta = now - dt
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60

    if days > 365:
        years = days // 365
        return f"{years}y {days % 365}d"
    if days > 30:
        months = days // 30
        return f"{months}mo {days % 30}d"
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"


def basescan_token_url(address: str) -> str:
    return f"https://basescan.org/token/{address}"


def basescan_address_url(address: str) -> str:
    return f"https://basescan.org/address/{address}"


def basescan_tx_url(tx_hash: str) -> str:
    return f"https://basescan.org/tx/{tx_hash}"


def dexscreener_url(pair_address: str) -> str:
    return f"https://dexscreener.com/base/{pair_address}"


def defined_url(token_address: str) -> str:
    return f"https://www.defined.fi/base/{token_address}"


def safety_score_emoji(score: int) -> str:
    """Return emoji based on safety score 0-100."""
    if score >= 80:
        return "🟢"
    if score >= 60:
        return "🟡"
    if score >= 40:
        return "🟠"
    return "🔴"
