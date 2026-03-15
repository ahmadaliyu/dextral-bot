"""
Token analysis engine — aggregates data from all sources into
comprehensive research reports.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.config import config
from src.chain import get_token_basic_info, get_eth_balance, get_token_balance, get_checksum
from src.api_services import (
    dexscreener_token,
    dexscreener_search,
    gecko_token_info,
    gecko_top_pools,
    basescan_get_contract_creation,
    basescan_get_source_code,
    basescan_token_holders,
    basescan_token_transfers,
    basescan_normal_txs,
    basescan_eth_price,
    goplus_token_security,
)
from src.formatters import (
    fmt_number,
    fmt_price,
    fmt_percent,
    fmt_address,
    fmt_age,
    basescan_token_url,
    basescan_address_url,
    dexscreener_url,
    safety_score_emoji,
)

logger = logging.getLogger(__name__)


@dataclass
class TokenReport:
    """Full research report for a token."""

    # Basic
    address: str = ""
    name: str = ""
    symbol: str = ""
    decimals: int = 18
    total_supply: float = 0
    owner: str | None = None

    # Market
    price_usd: float = 0
    market_cap: float = 0
    fdv: float = 0
    liquidity_usd: float = 0
    volume_24h: float = 0
    price_change_5m: float = 0
    price_change_1h: float = 0
    price_change_6h: float = 0
    price_change_24h: float = 0
    buys_24h: int = 0
    sells_24h: int = 0
    pair_address: str = ""
    pair_created_at: int = 0
    dex_name: str = ""

    # Dev / Deployer
    deployer: str = ""
    creation_tx: str = ""
    deployer_eth_balance: float = 0
    deployer_token_balance: float = 0
    deployer_token_pct: float = 0

    # Contract
    is_verified: bool = False
    is_proxy: bool = False
    compiler: str = ""

    # Security (GoPlus)
    is_honeypot: bool | None = None
    is_mintable: bool | None = None
    is_open_source: bool | None = None
    buy_tax: float = 0
    sell_tax: float = 0
    can_take_back_ownership: bool | None = None
    owner_change_balance: bool | None = None
    hidden_owner: bool | None = None
    has_external_call: bool | None = None
    is_anti_whale: bool | None = None
    trading_cooldown: bool | None = None
    is_blacklisted: bool | None = None
    holder_count: int = 0
    lp_holder_count: int = 0
    lp_total_supply: float = 0
    is_in_dex: bool | None = None

    # Safety score 0-100
    safety_score: int = 0

    # Holders
    top_holders: list = field(default_factory=list)

    # Pools
    pools: list = field(default_factory=list)

    # Errors
    errors: list = field(default_factory=list)


async def analyze_token(address: str) -> TokenReport:
    """
    Run full analysis on a Base chain token.
    Aggregates on-chain + off-chain data.
    """
    report = TokenReport(address=get_checksum(address))

    # ── 1. On-chain basics ────────────────────────────────────
    chain_info = await get_token_basic_info(address)
    if chain_info:
        report.name = chain_info.get("name", "Unknown")
        report.symbol = chain_info.get("symbol", "???")
        report.decimals = chain_info.get("decimals", 18)
        report.total_supply = chain_info.get("total_supply", 0)
        report.owner = chain_info.get("owner")
    else:
        report.errors.append("⚠️ Could not read on-chain token data")

    # ── 2. DexScreener market data ────────────────────────────
    dex = await dexscreener_token(address)
    if dex:
        report.price_usd = float(dex.get("priceUsd", 0) or 0)
        report.market_cap = float(dex.get("marketCap", 0) or 0)
        report.fdv = float(dex.get("fdv", 0) or 0)

        liq = dex.get("liquidity", {})
        report.liquidity_usd = float(liq.get("usd", 0) or 0)

        vol = dex.get("volume", {})
        report.volume_24h = float(vol.get("h24", 0) or 0)

        pc = dex.get("priceChange", {})
        report.price_change_5m = float(pc.get("m5", 0) or 0)
        report.price_change_1h = float(pc.get("h1", 0) or 0)
        report.price_change_6h = float(pc.get("h6", 0) or 0)
        report.price_change_24h = float(pc.get("h24", 0) or 0)

        txns = dex.get("txns", {}).get("h24", {})
        report.buys_24h = int(txns.get("buys", 0) or 0)
        report.sells_24h = int(txns.get("sells", 0) or 0)

        report.pair_address = dex.get("pairAddress", "")
        report.pair_created_at = int(dex.get("pairCreatedAt", 0) or 0) // 1000
        report.dex_name = dex.get("dexId", "Unknown")

        # Override name/symbol if chain read failed
        if not report.name or report.name == "Unknown":
            bi = dex.get("baseToken", {})
            report.name = bi.get("name", "Unknown")
            report.symbol = bi.get("symbol", "???")
    else:
        report.errors.append("⚠️ No DexScreener data found")

    # ── 3. Contract deployer ──────────────────────────────────
    creation = await basescan_get_contract_creation(address)
    if creation:
        report.deployer = creation.get("contractCreator", "")
        report.creation_tx = creation.get("txHash", "")

        if report.deployer:
            report.deployer_eth_balance = await get_eth_balance(report.deployer)
            report.deployer_token_balance = await get_token_balance(
                address, report.deployer
            )
            if report.total_supply > 0:
                report.deployer_token_pct = (
                    report.deployer_token_balance / report.total_supply
                ) * 100

    # ── 4. Source code verification ───────────────────────────
    source = await basescan_get_source_code(address)
    if source:
        report.is_verified = bool(source.get("SourceCode"))
        report.is_proxy = source.get("Proxy") == "1"
        report.compiler = source.get("CompilerVersion", "")

    # ── 5. GoPlus security ────────────────────────────────────
    security = await goplus_token_security(address)
    if security:
        report.is_honeypot = _to_bool(security.get("is_honeypot"))
        report.is_mintable = _to_bool(security.get("is_mintable"))
        report.is_open_source = _to_bool(security.get("is_open_source"))
        report.buy_tax = _safe_float(security.get("buy_tax", 0))
        report.sell_tax = _safe_float(security.get("sell_tax", 0))
        report.can_take_back_ownership = _to_bool(
            security.get("can_take_back_ownership")
        )
        report.owner_change_balance = _to_bool(
            security.get("owner_change_balance")
        )
        report.hidden_owner = _to_bool(security.get("hidden_owner"))
        report.has_external_call = _to_bool(security.get("external_call"))
        report.is_anti_whale = _to_bool(security.get("is_anti_whale"))
        report.trading_cooldown = _to_bool(security.get("trading_cooldown"))
        report.is_blacklisted = _to_bool(security.get("is_blacklisted"))
        report.holder_count = int(security.get("holder_count", 0) or 0)
        report.lp_holder_count = int(security.get("lp_holder_count", 0) or 0)
        report.lp_total_supply = _safe_float(
            security.get("lp_total_supply", 0)
        )
        report.is_in_dex = _to_bool(security.get("is_in_dex"))

        # Holder list from GoPlus
        holders_raw = security.get("holders", [])
        if holders_raw:
            report.top_holders = [
                {
                    "address": h.get("address", ""),
                    "balance": _safe_float(h.get("balance", 0)),
                    "percent": _safe_float(h.get("percent", 0)) * 100,
                    "is_locked": _to_bool(h.get("is_locked")),
                    "is_contract": _to_bool(h.get("is_contract")),
                    "tag": h.get("tag", ""),
                }
                for h in holders_raw[:15]
            ]

    # ── 6. Safety score ───────────────────────────────────────
    report.safety_score = _calculate_safety_score(report)

    return report


def _calculate_safety_score(r: TokenReport) -> int:
    """Calculate a safety score 0-100 based on all flags."""
    score = 100

    # Critical issues (big deductions)
    if r.is_honeypot is True:
        score -= 80
    if r.buy_tax > 10:
        score -= 20
    if r.sell_tax > 10:
        score -= 20
    if r.is_mintable is True:
        score -= 15
    if r.can_take_back_ownership is True:
        score -= 15
    if r.owner_change_balance is True:
        score -= 15
    if r.hidden_owner is True:
        score -= 10
    if r.has_external_call is True:
        score -= 10

    # Moderate issues
    if not r.is_verified:
        score -= 10
    if r.is_proxy:
        score -= 5
    if r.is_blacklisted is True:
        score -= 10
    if r.liquidity_usd < 5000:
        score -= 10
    if r.holder_count < 50:
        score -= 5

    # Positive signals
    if r.is_open_source is True:
        score += 5
    if r.liquidity_usd > 100_000:
        score += 5
    if r.holder_count > 500:
        score += 5

    # Dev wallet check
    if r.deployer_token_pct > 20:
        score -= 15
    elif r.deployer_token_pct > 10:
        score -= 10
    elif r.deployer_token_pct > 5:
        score -= 5

    return max(0, min(100, score))


async def analyze_dev_wallet(token_address: str) -> dict:
    """Deep analysis of the deployer wallet."""
    result = {
        "deployer": "",
        "eth_balance": 0,
        "token_balance": 0,
        "token_pct": 0,
        "total_tokens_deployed": 0,
        "recent_txs": [],
        "other_tokens": [],
        "deployer_age_text": "",
        "risk_level": "Unknown",
    }

    creation = await basescan_get_contract_creation(token_address)
    if not creation:
        return result

    deployer = creation.get("contractCreator", "")
    if not deployer:
        return result

    result["deployer"] = deployer
    result["eth_balance"] = await get_eth_balance(deployer)

    chain_info = await get_token_basic_info(token_address)
    if chain_info:
        total_supply = chain_info.get("total_supply", 0)
        token_bal = await get_token_balance(token_address, deployer)
        result["token_balance"] = token_bal
        if total_supply > 0:
            result["token_pct"] = (token_bal / total_supply) * 100

    # Get deployer's recent transactions
    txs = await basescan_normal_txs(deployer)
    if txs:
        result["recent_txs"] = txs[:10]

        # Count contract deployments (to = "")
        deployments = [tx for tx in txs if tx.get("to") == ""]
        result["total_tokens_deployed"] = len(deployments)

        # First tx timestamp as "age"
        sorted_txs = sorted(txs, key=lambda t: int(t.get("timeStamp", 0)))
        if sorted_txs:
            first_ts = int(sorted_txs[0].get("timeStamp", 0))
            result["deployer_age_text"] = fmt_age(first_ts)

    # Risk assessment
    risk = "🟢 LOW"
    if result["token_pct"] > 20:
        risk = "🔴 HIGH"
    elif result["token_pct"] > 10:
        risk = "🟠 MEDIUM"
    elif result["total_tokens_deployed"] > 5:
        risk = "🟠 MEDIUM (serial deployer)"
    elif result["eth_balance"] < 0.01:
        risk = "🟡 WATCH (low ETH balance)"

    result["risk_level"] = risk
    return result


async def analyze_whale_holders(token_address: str) -> dict:
    """Analyze top holders and identify whales."""
    result = {
        "holders": [],
        "whale_count": 0,
        "top10_pct": 0,
        "top20_pct": 0,
        "concentration_risk": "",
        "dead_supply_pct": 0,
    }

    chain_info = await get_token_basic_info(token_address)
    total_supply = chain_info.get("total_supply", 0) if chain_info else 0

    # Get security data (which includes holder list)
    security = await goplus_token_security(token_address)
    if security:
        holders_raw = security.get("holders", [])
        holders = []
        dead_pct = 0

        for h in holders_raw[:20]:
            addr = h.get("address", "")
            pct = _safe_float(h.get("percent", 0)) * 100
            is_contract = _to_bool(h.get("is_contract"))
            is_locked = _to_bool(h.get("is_locked"))
            tag = h.get("tag", "")

            # Check if dead address
            if addr.lower() in [d.lower() for d in config.DEAD_ADDRESSES]:
                dead_pct += pct
                tag = "🔥 Burn Address"

            holders.append({
                "address": addr,
                "percent": pct,
                "is_contract": is_contract,
                "is_locked": is_locked,
                "tag": tag,
            })

        result["holders"] = holders
        result["dead_supply_pct"] = dead_pct

        # Calculate concentration
        top10_pct = sum(h["percent"] for h in holders[:10])
        top20_pct = sum(h["percent"] for h in holders[:20])
        result["top10_pct"] = top10_pct
        result["top20_pct"] = top20_pct

        # Whale count (holding > 2%)
        result["whale_count"] = len([h for h in holders if h["percent"] > 2])

        # Risk assessment
        adjusted_top10 = top10_pct - dead_pct
        if adjusted_top10 > 60:
            result["concentration_risk"] = "🔴 VERY HIGH — Top 10 holders control >60%"
        elif adjusted_top10 > 40:
            result["concentration_risk"] = "🟠 HIGH — Top 10 holders control >40%"
        elif adjusted_top10 > 25:
            result["concentration_risk"] = "🟡 MODERATE — Top 10 holders control >25%"
        else:
            result["concentration_risk"] = "🟢 LOW — Well distributed"

    return result


async def get_recent_whale_txs(token_address: str, eth_price: float = 0) -> list[dict]:
    """Find recent large transactions for a token."""
    if eth_price == 0:
        eth_price = await basescan_eth_price()

    transfers = await basescan_token_transfers(token_address)
    chain_info = await get_token_basic_info(token_address)
    decimals = chain_info.get("decimals", 18) if chain_info else 18

    dex = await dexscreener_token(token_address)
    token_price = float(dex.get("priceUsd", 0) or 0) if dex else 0

    whale_txs = []
    for tx in transfers:
        value_raw = int(tx.get("value", 0))
        value = value_raw / (10**decimals)
        value_usd = value * token_price

        if value_usd >= config.WHALE_THRESHOLD_USD:
            whale_txs.append({
                "hash": tx.get("hash", ""),
                "from": tx.get("from", ""),
                "to": tx.get("to", ""),
                "value": value,
                "value_usd": value_usd,
                "timestamp": int(tx.get("timeStamp", 0)),
            })

    # Sort by value descending
    whale_txs.sort(key=lambda x: x["value_usd"], reverse=True)
    return whale_txs[:20]


# ─── Helpers ──────────────────────────────────────────────────

def _to_bool(val) -> bool | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val == "1" or val.lower() == "true"
    return bool(val)


def _safe_float(val) -> float:
    try:
        return float(val or 0)
    except (ValueError, TypeError):
        return 0.0


async def analyze_pvp(token_address: str) -> dict:
    """
    PvP Analysis — detect duplicate/copycat tokens with the same name or symbol.
    Helps identify PvP situations where multiple tokens compete under the same name.
    """
    result = {
        "token_name": "",
        "token_symbol": "",
        "token_address": token_address,
        "token_liquidity": 0,
        "token_mcap": 0,
        "duplicates": [],
        "total_found": 0,
        "pvp_risk": "",
        "is_original": True,
    }

    # Get info about the target token
    chain_info = await get_token_basic_info(token_address)
    if not chain_info:
        return result

    token_name = chain_info.get("name", "")
    token_symbol = chain_info.get("symbol", "")
    result["token_name"] = token_name
    result["token_symbol"] = token_symbol

    # Get market data for our token
    dex = await dexscreener_token(token_address)
    if dex:
        result["token_liquidity"] = float(dex.get("liquidity", {}).get("usd", 0) or 0)
        result["token_mcap"] = float(dex.get("marketCap", 0) or 0)

    # Search for tokens with same name AND same symbol on DexScreener
    duplicates = []

    # Search by symbol
    symbol_results = await dexscreener_search(token_symbol)
    # Search by name
    name_results = await dexscreener_search(token_name)

    # Merge and deduplicate
    seen_addresses = {token_address.lower()}
    all_results = symbol_results + name_results

    for pair in all_results:
        base_token = pair.get("baseToken", {})
        addr = base_token.get("address", "")
        name = base_token.get("name", "")
        symbol = base_token.get("symbol", "")

        if not addr or addr.lower() in seen_addresses:
            continue

        # Check if name or symbol matches (case-insensitive)
        name_match = (
            token_name.lower() in name.lower() or name.lower() in token_name.lower()
        ) if token_name else False
        symbol_match = token_symbol.lower() == symbol.lower() if token_symbol else False

        if name_match or symbol_match:
            seen_addresses.add(addr.lower())
            liq = float(pair.get("liquidity", {}).get("usd", 0) or 0)
            mcap = float(pair.get("marketCap", 0) or 0)
            vol = float(pair.get("volume", {}).get("h24", 0) or 0)
            price = float(pair.get("priceUsd", 0) or 0)
            created = int(pair.get("pairCreatedAt", 0) or 0) // 1000

            duplicates.append({
                "address": addr,
                "name": name,
                "symbol": symbol,
                "price": price,
                "liquidity": liq,
                "mcap": mcap,
                "volume_24h": vol,
                "pair_created_at": created,
                "dex": pair.get("dexId", ""),
                "pair_address": pair.get("pairAddress", ""),
                "name_match": name_match,
                "symbol_match": symbol_match,
            })

    # Sort by liquidity descending
    duplicates.sort(key=lambda x: x["liquidity"], reverse=True)
    result["duplicates"] = duplicates
    result["total_found"] = len(duplicates)

    # Determine if our token is the "original" (highest liquidity)
    if duplicates:
        top_liq = duplicates[0]["liquidity"]
        if top_liq > result["token_liquidity"] * 2:
            result["is_original"] = False

    # PvP risk assessment
    if len(duplicates) == 0:
        result["pvp_risk"] = "🟢 SAFE — No duplicates found"
    elif len(duplicates) == 1:
        result["pvp_risk"] = "🟡 LOW — 1 similar token exists"
    elif len(duplicates) <= 3:
        result["pvp_risk"] = "🟠 MEDIUM — Multiple similar tokens found"
    else:
        result["pvp_risk"] = f"🔴 HIGH — {len(duplicates)} similar tokens detected! Active PvP zone"

    return result
