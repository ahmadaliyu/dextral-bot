"""
Telegram message builders — produces rich formatted messages from reports.
"""

from src.token_analysis import TokenReport
from src.formatters import (
    fmt_number,
    fmt_price,
    fmt_percent,
    fmt_address,
    fmt_age,
    basescan_token_url,
    basescan_address_url,
    basescan_tx_url,
    dexscreener_url,
    safety_score_emoji,
)


def build_token_message(r: TokenReport) -> str:
    """Build the main /token response message."""
    score_em = safety_score_emoji(r.safety_score)

    # Header
    lines = [
        f"{'━' * 32}",
        f"🔬 <b>{r.name}</b> (${r.symbol})",
        f"{'━' * 32}",
        "",
        f"📍 <b>Network:</b> Base",
        f"📋 <code>{r.address}</code>",
        "",
    ]

    # Market Data
    lines += [
        f"💰 <b>Price:</b> {fmt_price(r.price_usd)}",
        f"📊 <b>Market Cap:</b> {fmt_number(r.market_cap)}",
        f"💎 <b>FDV:</b> {fmt_number(r.fdv)}",
        f"🏊 <b>Liquidity:</b> {fmt_number(r.liquidity_usd)}",
        f"📈 <b>24h Volume:</b> {fmt_number(r.volume_24h)}",
        "",
    ]

    # Price Changes
    lines += [
        "📉 <b>Price Changes:</b>",
        f"    5m: {fmt_percent(r.price_change_5m)}  "
        f"1h: {fmt_percent(r.price_change_1h)}",
        f"    6h: {fmt_percent(r.price_change_6h)}  "
        f"24h: {fmt_percent(r.price_change_24h)}",
        "",
    ]

    # Trading Activity
    total_txns = r.buys_24h + r.sells_24h
    buy_pct = (r.buys_24h / total_txns * 100) if total_txns > 0 else 0
    lines += [
        "🔄 <b>24h Trading:</b>",
        f"    🟢 Buys: {r.buys_24h:,}  🔴 Sells: {r.sells_24h:,}",
        f"    Buy Pressure: {buy_pct:.1f}%",
        "",
    ]

    # Supply & Token Info
    lines += [
        "📦 <b>Supply:</b>",
        f"    Total: {r.total_supply:,.0f}",
        f"    Holders: {r.holder_count:,}" if r.holder_count else "",
        f"    LP Holders: {r.lp_holder_count:,}" if r.lp_holder_count else "",
        "",
    ]

    # DEX Info
    if r.pair_address:
        lines += [
            f"🏦 <b>DEX:</b> {r.dex_name.upper()}",
            f"    Pair Age: {fmt_age(r.pair_created_at)}",
            "",
        ]

    # Safety Score
    lines += [
        f"{'━' * 32}",
        f"{score_em} <b>Safety Score: {r.safety_score}/100</b>",
        f"{'━' * 32}",
    ]

    # Security Flags
    flags = []
    if r.is_honeypot is True:
        flags.append("🍯 HONEYPOT DETECTED")
    if r.is_honeypot is False:
        flags.append("✅ Not Honeypot")
    if r.is_mintable is True:
        flags.append("⚠️ Mintable")
    if r.is_mintable is False:
        flags.append("✅ Not Mintable")
    if r.is_open_source is True:
        flags.append("✅ Open Source")
    if r.is_open_source is False:
        flags.append("❌ Not Open Source")
    if r.is_verified:
        flags.append("✅ Verified Contract")
    else:
        flags.append("❌ Unverified Contract")
    if r.is_proxy:
        flags.append("⚠️ Proxy Contract")
    if r.hidden_owner is True:
        flags.append("⚠️ Hidden Owner")
    if r.can_take_back_ownership is True:
        flags.append("🚨 Can Reclaim Ownership")
    if r.owner_change_balance is True:
        flags.append("🚨 Owner Can Change Balances")
    if r.is_blacklisted is True:
        flags.append("⚠️ Has Blacklist Function")
    if r.has_external_call is True:
        flags.append("⚠️ External Calls")
    if r.is_anti_whale is True:
        flags.append("🐋 Anti-Whale Enabled")
    if r.trading_cooldown is True:
        flags.append("⏱ Trading Cooldown")
    if r.buy_tax > 0:
        flags.append(f"💸 Buy Tax: {r.buy_tax:.1f}%")
    if r.sell_tax > 0:
        flags.append(f"💸 Sell Tax: {r.sell_tax:.1f}%")

    if flags:
        lines.append("")
        lines.append("🛡 <b>Security Flags:</b>")
        for f in flags:
            lines.append(f"    {f}")

    # Dev wallet preview
    if r.deployer:
        lines += [
            "",
            f"👨‍💻 <b>Deployer:</b> <code>{r.deployer}</code>",
            f"    ETH Balance: {r.deployer_eth_balance:.4f} ETH",
            f"    Token Holdings: {r.deployer_token_pct:.2f}% of supply",
        ]

    # Links
    lines += [
        "",
        f"{'━' * 32}",
        "🔗 <b>Links:</b>",
        f"    📊 <a href='{dexscreener_url(r.pair_address)}'>DexScreener</a>"
        if r.pair_address
        else "",
        f"    🔍 <a href='{basescan_token_url(r.address)}'>Basescan</a>",
        f"{'━' * 32}",
    ]

    # Errors
    if r.errors:
        lines.append("")
        for err in r.errors:
            lines.append(err)

    return "\n".join(line for line in lines if line is not None)


def build_dev_message(dev_info: dict, token_address: str, token_symbol: str) -> str:
    """Build the /dev response message."""
    deployer = dev_info.get("deployer", "N/A")
    if not deployer:
        return "❌ Could not find deployer information for this token."

    lines = [
        f"{'━' * 32}",
        f"👨‍💻 <b>Dev Wallet Analysis</b> — ${token_symbol}",
        f"{'━' * 32}",
        "",
        f"📋 <b>Deployer:</b> <code>{deployer}</code>",
        f"🔗 <a href='{basescan_address_url(deployer)}'>View on Basescan</a>",
        "",
        f"💰 <b>ETH Balance:</b> {dev_info['eth_balance']:.4f} ETH",
        f"🪙 <b>Token Balance:</b> {dev_info['token_balance']:,.2f} ({dev_info['token_pct']:.2f}%)",
        f"🏭 <b>Contracts Deployed:</b> {dev_info['total_tokens_deployed']}",
        f"📅 <b>Wallet Age:</b> {dev_info.get('deployer_age_text', 'N/A')}",
        "",
        f"⚠️ <b>Risk Level:</b> {dev_info['risk_level']}",
    ]

    # Recent transactions
    recent = dev_info.get("recent_txs", [])
    if recent:
        lines += ["", "📜 <b>Recent Transactions:</b>"]
        for tx in recent[:5]:
            ts = int(tx.get("timeStamp", 0))
            to_addr = tx.get("to", "")
            val_eth = int(tx.get("value", 0)) / 1e18
            tx_hash = tx.get("hash", "")
            direction = "→" if to_addr else "📦 Deploy"
            lines.append(
                f"    {fmt_age(ts)} ago │ {direction} "
                f"{fmt_address(to_addr) if to_addr else ''} │ "
                f"{val_eth:.4f} ETH │ "
                f"<a href='{basescan_tx_url(tx_hash)}'>Tx</a>"
            )

    lines.append(f"\n{'━' * 32}")
    return "\n".join(lines)


def build_holders_message(
    holder_info: dict, token_address: str, token_symbol: str
) -> str:
    """Build the /holders response message."""
    lines = [
        f"{'━' * 32}",
        f"🐋 <b>Holder Analysis</b> — ${token_symbol}",
        f"{'━' * 32}",
        "",
        f"📊 <b>Concentration:</b>",
        f"    Top 10: {holder_info['top10_pct']:.2f}%",
        f"    Top 20: {holder_info['top20_pct']:.2f}%",
        f"    🔥 Burned: {holder_info['dead_supply_pct']:.2f}%",
        f"    🐋 Whales (>2%): {holder_info['whale_count']}",
        "",
        f"    {holder_info['concentration_risk']}",
        "",
        f"{'━' * 32}",
        f"👑 <b>Top Holders:</b>",
        "",
    ]

    for i, h in enumerate(holder_info.get("holders", [])[:10], 1):
        addr = h["address"]
        pct = h["percent"]
        tag = h.get("tag", "")
        locked = " 🔒" if h.get("is_locked") else ""
        contract = " 📜" if h.get("is_contract") else ""
        tag_str = f" ({tag})" if tag else ""

        lines.append(
            f"    {i}. <code>{fmt_address(addr)}</code> — "
            f"{pct:.2f}%{locked}{contract}{tag_str}"
        )

    lines += [
        "",
        "🔒 = Locked  📜 = Contract",
        f"{'━' * 32}",
    ]

    return "\n".join(lines)


def build_whale_txs_message(
    whale_txs: list, token_symbol: str
) -> str:
    """Build the /whale response for recent large transactions."""
    if not whale_txs:
        return f"🐋 No whale transactions found for ${token_symbol} above the threshold."

    lines = [
        f"{'━' * 32}",
        f"🐋 <b>Whale Transactions</b> — ${token_symbol}",
        f"{'━' * 32}",
        "",
    ]

    for i, tx in enumerate(whale_txs[:10], 1):
        age = fmt_age(tx["timestamp"])
        lines.append(
            f"{i}. {fmt_number(tx['value_usd'])} │ "
            f"{tx['value']:,.0f} tokens\n"
            f"    {fmt_address(tx['from'])} → {fmt_address(tx['to'])}\n"
            f"    {age} ago │ "
            f"<a href='{basescan_tx_url(tx['hash'])}'>View Tx</a>"
        )
        lines.append("")

    lines.append(f"{'━' * 32}")
    return "\n".join(lines)


def build_scan_message(r: TokenReport) -> str:
    """Build a quick-scan summary (lighter than full /token)."""
    score_em = safety_score_emoji(r.safety_score)

    # Quick risk flags
    risks = []
    if r.is_honeypot is True:
        risks.append("🍯 HONEYPOT")
    if r.buy_tax > 5:
        risks.append(f"💸 Buy Tax {r.buy_tax:.0f}%")
    if r.sell_tax > 5:
        risks.append(f"💸 Sell Tax {r.sell_tax:.0f}%")
    if r.is_mintable is True:
        risks.append("⚠️ Mintable")
    if r.deployer_token_pct > 10:
        risks.append(f"👨‍💻 Dev holds {r.deployer_token_pct:.1f}%")
    if r.hidden_owner is True:
        risks.append("👤 Hidden Owner")
    if r.can_take_back_ownership is True:
        risks.append("🚨 Can Reclaim")
    if not r.is_verified:
        risks.append("❌ Unverified")

    risk_str = " │ ".join(risks) if risks else "✅ No major risks detected"

    lines = [
        f"{score_em} <b>{r.name}</b> (${r.symbol}) — Score: {r.safety_score}/100",
        f"💰 {fmt_price(r.price_usd)} │ MC {fmt_number(r.market_cap)} │ Liq {fmt_number(r.liquidity_usd)}",
        f"📈 24h: {fmt_percent(r.price_change_24h)} │ Vol: {fmt_number(r.volume_24h)}",
        f"⚠️ {risk_str}",
        f"📋 <code>{r.address}</code>",
    ]

    return "\n".join(lines)


def build_trending_message(pools: list) -> str:
    """Build the /trending response."""
    if not pools:
        return "📊 No trending data available right now."

    lines = [
        f"{'━' * 32}",
        "🔥 <b>Trending on Base</b>",
        f"{'━' * 32}",
        "",
    ]

    for i, pool in enumerate(pools[:15], 1):
        attrs = pool.get("attributes", {}) if "attributes" in pool else pool
        name = attrs.get("name", "Unknown")
        price = fmt_price(float(attrs.get("base_token_price_usd", 0) or 0))
        vol = fmt_number(float(attrs.get("volume_usd", {}).get("h24", 0) or 0))
        change = float(
            attrs.get("price_change_percentage", {}).get("h24", 0) or 0
        )

        lines.append(
            f"{i}. <b>{name}</b>\n"
            f"    💰 {price} │ 📈 {fmt_percent(change)} │ Vol: {vol}"
        )
        lines.append("")

    lines.append(f"{'━' * 32}")
    return "\n".join(lines)


def build_new_pairs_message(pools: list) -> str:
    """Build the /new response for newly created pairs."""
    if not pools:
        return "🆕 No new pairs found right now."

    lines = [
        f"{'━' * 32}",
        "🆕 <b>New Pairs on Base</b>",
        f"{'━' * 32}",
        "",
    ]

    for i, pool in enumerate(pools[:10], 1):
        attrs = pool.get("attributes", {}) if "attributes" in pool else pool
        name = attrs.get("name", "Unknown")
        price = fmt_price(float(attrs.get("base_token_price_usd", 0) or 0))
        created = attrs.get("pool_created_at", "")

        lines.append(
            f"{i}. <b>{name}</b>\n"
            f"    💰 {price} │ 🕐 Created: {created[:16] if created else 'N/A'}"
        )
        lines.append("")

    lines.append(f"{'━' * 32}")
    return "\n".join(lines)


def build_pvp_message(pvp_info: dict) -> str:
    """Build the /pvp response — duplicate/copycat token detection."""
    token_name = pvp_info.get("token_name", "Unknown")
    token_symbol = pvp_info.get("token_symbol", "???")
    token_address = pvp_info.get("token_address", "")
    duplicates = pvp_info.get("duplicates", [])
    total = pvp_info.get("total_found", 0)
    pvp_risk = pvp_info.get("pvp_risk", "")
    is_original = pvp_info.get("is_original", True)

    lines = [
        f"{'━' * 32}",
        f"⚔️ <b>PvP Analysis</b> — ${token_symbol}",
        f"{'━' * 32}",
        "",
        f"🎯 <b>Your Token:</b> {token_name} (${token_symbol})",
        f"📋 <code>{token_address}</code>",
        f"🏊 Liquidity: {fmt_number(pvp_info.get('token_liquidity', 0))}",
        f"📊 Market Cap: {fmt_number(pvp_info.get('token_mcap', 0))}",
        "",
        f"{'━' * 32}",
        f"⚠️ <b>PvP Risk:</b> {pvp_risk}",
        f"{'━' * 32}",
    ]

    if not is_original:
        lines += [
            "",
            "🚨 <b>WARNING:</b> Another token with the same name has",
            "    MORE liquidity — your token may NOT be the original!",
        ]

    if duplicates:
        lines += [
            "",
            f"🔍 <b>Found {total} similar token(s) on Base:</b>",
            "",
        ]

        for i, d in enumerate(duplicates[:10], 1):
            match_type = []
            if d.get("name_match"):
                match_type.append("name")
            if d.get("symbol_match"):
                match_type.append("symbol")
            match_str = " + ".join(match_type)

            age_str = fmt_age(d["pair_created_at"]) if d.get("pair_created_at") else "N/A"

            lines.append(
                f"{i}. <b>{d['name']}</b> (${d['symbol']})\n"
                f"    📋 <code>{d['address']}</code>\n"
                f"    💰 {fmt_price(d['price'])} │ MC {fmt_number(d['mcap'])}\n"
                f"    🏊 Liq: {fmt_number(d['liquidity'])} │ Vol: {fmt_number(d['volume_24h'])}\n"
                f"    🏦 {d.get('dex', 'N/A').upper()} │ Age: {age_str}\n"
                f"    🔗 Matched by: {match_str}"
            )
            lines.append("")
    else:
        lines += [
            "",
            "✅ No duplicate or copycat tokens found on Base.",
            "    This appears to be a unique token name/symbol.",
        ]

    lines += [
        f"{'━' * 32}",
        "💡 <b>Tip:</b> Always verify the contract address from",
        "    official sources before buying.",
        f"{'━' * 32}",
    ]

    return "\n".join(lines)