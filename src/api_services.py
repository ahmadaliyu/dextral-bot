"""
External API integrations — DexScreener, GeckoTerminal, Basescan, GoPlus.
All async using aiohttp.
"""

from __future__ import annotations

import logging
import aiohttp
from cachetools import TTLCache

from src.config import config

logger = logging.getLogger(__name__)

# In-memory caches
_token_cache = TTLCache(maxsize=500, ttl=config.CACHE_TTL)
_pair_cache = TTLCache(maxsize=500, ttl=config.CACHE_TTL)
_holder_cache = TTLCache(maxsize=200, ttl=config.CACHE_TTL * 3)
_safety_cache = TTLCache(maxsize=200, ttl=config.CACHE_TTL * 5)


# ─── DexScreener ──────────────────────────────────────────────

async def dexscreener_search(query: str) -> list[dict]:
    """Search tokens on DexScreener."""
    url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    pairs = data.get("pairs", [])
                    # Filter to Base chain only
                    return [p for p in pairs if p.get("chainId") == "base"]
    except Exception as e:
        logger.error(f"DexScreener search error: {e}")
    return []


async def dexscreener_token(address: str) -> dict | None:
    """Get token pairs from DexScreener by token address."""
    cache_key = f"dex_{address.lower()}"
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    pairs = data.get("pairs", [])
                    base_pairs = [p for p in pairs if p.get("chainId") == "base"]
                    if base_pairs:
                        # Sort by liquidity descending
                        base_pairs.sort(
                            key=lambda x: float(x.get("liquidity", {}).get("usd", 0) or 0),
                            reverse=True,
                        )
                        result = base_pairs[0]
                        result["_all_pairs"] = base_pairs
                        _token_cache[cache_key] = result
                        return result
    except Exception as e:
        logger.error(f"DexScreener token error: {e}")
    return None


async def dexscreener_trending() -> list[dict]:
    """Get trending tokens on Base from DexScreener."""
    url = "https://api.dexscreener.com/latest/dex/tokens/trending"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    # Some endpoints may differ; fallback to search
                    return [p for p in data if p.get("chainId") == "base"]
    except Exception:
        pass
    return []


# ─── GeckoTerminal ────────────────────────────────────────────

async def gecko_token_info(address: str) -> dict | None:
    """Get token info from GeckoTerminal."""
    url = f"{config.GECKOTERMINAL_API}/networks/base/tokens/{address}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("data", {}).get("attributes", {})
    except Exception as e:
        logger.error(f"GeckoTerminal token error: {e}")
    return None


async def gecko_top_pools(address: str) -> list[dict]:
    """Get top pools for a token from GeckoTerminal."""
    url = f"{config.GECKOTERMINAL_API}/networks/base/tokens/{address}/pools"
    try:
        async with aiohttp.ClientSession() as session:
            params = {"sort": "h24_volume_usd_desc", "page": "1"}
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    pools = data.get("data", [])
                    return [p.get("attributes", {}) for p in pools[:5]]
    except Exception as e:
        logger.error(f"GeckoTerminal pools error: {e}")
    return []


async def gecko_trending_base() -> list[dict]:
    """Get trending pools on Base from GeckoTerminal."""
    url = f"{config.GECKOTERMINAL_API}/networks/base/trending_pools"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("data", [])
    except Exception as e:
        logger.error(f"GeckoTerminal trending error: {e}")
    return []


async def gecko_new_pools_base() -> list[dict]:
    """Get newly created pools on Base."""
    url = f"{config.GECKOTERMINAL_API}/networks/base/new_pools"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    return data.get("data", [])
    except Exception as e:
        logger.error(f"GeckoTerminal new pools error: {e}")
    return []


# ─── Basescan ─────────────────────────────────────────────────

async def basescan_get_contract_creation(address: str) -> dict | None:
    """Get contract creator and creation tx from Basescan."""
    cache_key = f"creator_{address.lower()}"
    if cache_key in _holder_cache:
        return _holder_cache[cache_key]

    url = config.BASESCAN_API
    params = {
        "module": "contract",
        "action": "getcontractcreation",
        "contractaddresses": address,
        "apikey": config.BASESCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("result", [])
                    if results and isinstance(results, list):
                        result = results[0]
                        _holder_cache[cache_key] = result
                        return result
    except Exception as e:
        logger.error(f"Basescan contract creation error: {e}")
    return None


async def basescan_get_source_code(address: str) -> dict | None:
    """Get contract source code verification status."""
    url = config.BASESCAN_API
    params = {
        "module": "contract",
        "action": "getsourcecode",
        "address": address,
        "apikey": config.BASESCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("result", [])
                    if results and isinstance(results, list):
                        return results[0]
    except Exception as e:
        logger.error(f"Basescan source code error: {e}")
    return None


async def basescan_token_holders(address: str, page: int = 1) -> list[dict]:
    """Get top token holders from Basescan."""
    cache_key = f"holders_{address.lower()}_{page}"
    if cache_key in _holder_cache:
        return _holder_cache[cache_key]

    url = config.BASESCAN_API
    params = {
        "module": "token",
        "action": "tokenholderlist",
        "contractaddress": address,
        "page": str(page),
        "offset": "20",
        "apikey": config.BASESCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("result", [])
                    if isinstance(results, list):
                        _holder_cache[cache_key] = results
                        return results
    except Exception as e:
        logger.error(f"Basescan holders error: {e}")
    return []


async def basescan_token_transfers(
    address: str, start_block: int = 0, sort: str = "desc", page: int = 1
) -> list[dict]:
    """Get token transfer events."""
    url = config.BASESCAN_API
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": address,
        "startblock": str(start_block),
        "endblock": "99999999",
        "page": str(page),
        "offset": "100",
        "sort": sort,
        "apikey": config.BASESCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("result", [])
                    if isinstance(results, list):
                        return results
    except Exception as e:
        logger.error(f"Basescan transfers error: {e}")
    return []


async def basescan_normal_txs(address: str, sort: str = "desc") -> list[dict]:
    """Get normal transactions for an address."""
    url = config.BASESCAN_API
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": "0",
        "endblock": "99999999",
        "page": "1",
        "offset": "50",
        "sort": sort,
        "apikey": config.BASESCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    results = data.get("result", [])
                    if isinstance(results, list):
                        return results
    except Exception as e:
        logger.error(f"Basescan normal txs error: {e}")
    return []


async def basescan_eth_price() -> float:
    """Get current ETH price from Basescan."""
    url = config.BASESCAN_API
    params = {
        "module": "stats",
        "action": "ethprice",
        "apikey": config.BASESCAN_API_KEY,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    result = data.get("result", {})
                    return float(result.get("ethusd", 0))
    except Exception as e:
        logger.error(f"Basescan ETH price error: {e}")
    return 0.0


# ─── GoPlus Security ──────────────────────────────────────────

async def goplus_token_security(address: str) -> dict | None:
    """Get token security info from GoPlus (free API)."""
    cache_key = f"goplus_{address.lower()}"
    if cache_key in _safety_cache:
        return _safety_cache[cache_key]

    url = f"https://api.gopluslabs.io/api/v1/token_security/8453"
    params = {"contract_addresses": address}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as r:
                if r.status == 200:
                    data = await r.json()
                    result_map = data.get("result", {})
                    # GoPlus returns with lowercased key
                    token_data = result_map.get(address.lower(), {})
                    if token_data:
                        _safety_cache[cache_key] = token_data
                        return token_data
    except Exception as e:
        logger.error(f"GoPlus security error: {e}")
    return None
