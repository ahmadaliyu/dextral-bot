"""
Configuration loader — reads .env and exposes typed settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Telegram
    BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # Base Chain
    BASE_RPC_URL: str = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
    BASE_CHAIN_ID: int = 8453

    # API Keys
    BASESCAN_API_KEY: str = os.getenv("BASESCAN_API_KEY", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")

    # API Base URLs
    DEXSCREENER_API: str = "https://api.dexscreener.com/latest"
    GECKOTERMINAL_API: str = "https://api.geckoterminal.com/api/v2"
    BASESCAN_API: str = "https://api.basescan.org/api"
    DEFINED_API: str = "https://graph.defined.fi/graphql"

    # Thresholds
    WHALE_THRESHOLD_USD: float = float(os.getenv("WHALE_THRESHOLD_USD", "50000"))

    # Cache
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "60"))

    # Well-known Base addresses
    WETH_BASE: str = "0x4200000000000000000000000000000000000006"
    UNISWAP_V2_FACTORY: str = "0x8909Dc15e40173Ff4699343b6eB8132c65e18eC6"
    UNISWAP_V3_FACTORY: str = "0x33128a8fC17869897dcE68Ed026d694621f6FDfD"
    AERODROME_ROUTER: str = "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43"

    # Dead wallets (tokens sent here are considered burned)
    DEAD_ADDRESSES: list = [
        "0x0000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000dEaD",
        "0x0000000000000000000000000000000000000001",
    ]


config = Config()
