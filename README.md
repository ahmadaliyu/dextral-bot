# 🤖 DEXTRAL BOT — Base Chain Token Research

> Advanced Telegram bot for tracking Base chain tokens, analyzing dev wallets, detecting whales, and performing comprehensive token research.

![Base Chain](https://img.shields.io/badge/Chain-Base-0052FF?style=for-the-badge&logo=coinbase)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=for-the-badge&logo=telegram)

---

## ✨ Features

### 🔬 Full Token Analysis
- On-chain data (name, symbol, supply, owner)
- Real-time price, market cap, FDV, liquidity
- 24h volume, buy/sell ratio, price changes (5m / 1h / 6h / 24h)
- DEX pair info and pair age

### 🛡 Security & Safety Score
- **GoPlus Security** integration — honeypot detection, tax analysis
- Mintable / proxy / blacklist / hidden owner checks
- Contract verification status
- Automated **Safety Score 0–100**

### 👨‍💻 Dev Wallet Deep Dive
- Deployer address & creation transaction
- Dev ETH balance & token holdings (% of supply)
- Total contracts deployed (serial deployer detection)
- Wallet age & recent transactions
- Risk level assessment

### 🐋 Whale & Holder Intelligence
- Top holder breakdown with concentration %
- Whale count (holders > 2%)
- Locked / contract / burn address detection
- Top 10 / Top 20 concentration risk rating
- Recent whale transactions (configurable threshold)

### 🔥 Market Intelligence
- Trending tokens on Base (GeckoTerminal)
- Newly created pairs
- Token search by name or symbol (DexScreener)

### ⚡ User Experience
- **Paste any address** → auto-detect & full report
- Interactive inline keyboards (Dev / Holders / Whale / Refresh)
- Beautiful formatted messages with emojis
- Caching for fast responses

---

## 📋 Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message & command list |
| `/token <address>` | Full token research report |
| `/scan <address>` | Quick safety scan |
| `/dev <address>` | Deep dev wallet analysis |
| `/holders <address>` | Top holders & concentration |
| `/whale <address>` | Recent whale transactions |
| `/trending` | Trending tokens on Base |
| `/new` | Newly created pairs |
| `/search <query>` | Search tokens by name/symbol |
| `/help` | Show help |

> 💡 **Pro tip:** Just paste a contract address directly — no command needed!

---

## 🚀 Setup

### Prerequisites
- Python 3.11+
- A Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- A Basescan API Key (from [basescan.org](https://basescan.org/apis))

### 1. Clone the repo

```bash
git clone https://github.com/ahmadaliyu/dextral-bot.git
cd dextral-bot
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
BASESCAN_API_KEY=your_basescan_api_key_here
```

### 5. Run the bot

```bash
python -m src.index
```

---

## 🏗 Project Structure

```
dextral-bot/
├── src/
│   ├── __init__.py          # Package marker
│   ├── index.py             # Main entry point
│   ├── config.py            # Environment & settings
│   ├── chain.py             # Web3 provider & on-chain reads
│   ├── abi.py               # Contract ABIs
│   ├── api_services.py      # DexScreener, GeckoTerminal, Basescan, GoPlus
│   ├── token_analysis.py    # Analysis engine & safety scoring
│   ├── messages.py          # Telegram message builders
│   ├── handlers.py          # Bot command & callback handlers
│   └── formatters.py        # Number, address, time formatters
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔌 API Integrations

| Service | Purpose | Auth |
|---------|---------|------|
| **DexScreener** | Price, market data, search | Free, no key |
| **GeckoTerminal** | Trending, new pools, pool data | Free, no key |
| **Basescan** | Contract info, holders, transfers | API key (free tier) |
| **GoPlus Security** | Honeypot, tax, security flags | Free, no key |
| **Base RPC** | On-chain reads (ERC-20, balances) | Public RPC or Alchemy |

---

## ⚙️ Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | — | Your bot token from BotFather |
| `BASE_RPC_URL` | `https://mainnet.base.org` | Base chain RPC endpoint |
| `BASESCAN_API_KEY` | — | Basescan API key |
| `WHALE_THRESHOLD_USD` | `50000` | Min USD value for whale alerts |
| `CACHE_TTL` | `60` | Cache lifetime in seconds |

---

## 🐋 Whale Detection Logic

The bot flags transactions as "whale" activity when:
- Transfer value exceeds `WHALE_THRESHOLD_USD` (default $50,000)
- Whale holders are those controlling > 2% of total supply

Concentration risk is calculated as:
- 🟢 **LOW**: Top 10 (excl. burns) < 25%
- 🟡 **MODERATE**: 25–40%
- 🟠 **HIGH**: 40–60%
- 🔴 **VERY HIGH**: > 60%

---

## 🛡 Safety Score Algorithm

The safety score starts at 100 and deducts points for risk factors:

| Factor | Deduction |
|--------|-----------|
| Honeypot detected | -80 |
| Buy/Sell tax > 10% | -20 each |
| Mintable | -15 |
| Can reclaim ownership | -15 |
| Owner can change balances | -15 |
| Hidden owner | -10 |
| External calls | -10 |
| Unverified contract | -10 |
| Blacklist function | -10 |
| Low liquidity (< $5K) | -10 |
| Dev holds > 20% | -15 |
| Dev holds > 10% | -10 |
| Proxy contract | -5 |
| Low holders (< 50) | -5 |

Bonuses: Open source (+5), High liquidity (+5), Many holders (+5)

---

## 📝 License

MIT — build, modify, and use freely.

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Push and open a PR

---

<p align="center">
  Built with ❤️ for the Base ecosystem
</p>
