"""
Web3 provider for Base chain — on-chain reads.
"""

from __future__ import annotations

import logging
from web3 import Web3
from web3.contract import Contract

from src.config import config
from src.abi import ERC20_ABI, UNISWAP_V2_PAIR_ABI

logger = logging.getLogger(__name__)

w3 = Web3(Web3.HTTPProvider(config.BASE_RPC_URL))


def get_checksum(address: str) -> str:
    """Return checksummed address."""
    return Web3.to_checksum_address(address.strip())


def get_token_contract(address: str) -> Contract:
    """Return an ERC-20 contract instance."""
    return w3.eth.contract(address=get_checksum(address), abi=ERC20_ABI)


def get_pair_contract(address: str) -> Contract:
    """Return a Uniswap V2 pair contract instance."""
    return w3.eth.contract(address=get_checksum(address), abi=UNISWAP_V2_PAIR_ABI)


async def get_token_basic_info(address: str) -> dict:
    """Read basic ERC-20 info from chain."""
    try:
        contract = get_token_contract(address)
        name = contract.functions.name().call()
        symbol = contract.functions.symbol().call()
        decimals = contract.functions.decimals().call()
        total_supply_raw = contract.functions.totalSupply().call()
        total_supply = total_supply_raw / (10**decimals)

        # Try to get owner
        owner = None
        try:
            owner = contract.functions.owner().call()
        except Exception:
            pass

        return {
            "address": get_checksum(address),
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "total_supply": total_supply,
            "total_supply_raw": total_supply_raw,
            "owner": owner,
        }
    except Exception as e:
        logger.error(f"Error reading token {address}: {e}")
        return {}


async def get_eth_balance(address: str) -> float:
    """Get ETH balance of an address."""
    try:
        balance_wei = w3.eth.get_balance(get_checksum(address))
        return float(Web3.from_wei(balance_wei, "ether"))
    except Exception as e:
        logger.error(f"Error getting ETH balance for {address}: {e}")
        return 0.0


async def get_token_balance(token_address: str, holder_address: str) -> float:
    """Get token balance of a holder."""
    try:
        contract = get_token_contract(token_address)
        decimals = contract.functions.decimals().call()
        balance_raw = contract.functions.balanceOf(
            get_checksum(holder_address)
        ).call()
        return balance_raw / (10**decimals)
    except Exception as e:
        logger.error(f"Error getting token balance: {e}")
        return 0.0


async def get_contract_creation_info(address: str) -> dict | None:
    """
    Attempt to find the deployer by scanning the first few internal/normal txs.
    Falls back to Basescan API (see api_services).
    """
    return None  # Handled by Basescan API
