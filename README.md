# APIClaw Analysis Skill

> Amazon Product Research skill for AI agents — powered by [APIClaw API](https://apiclaw.io)

## What It Does

Gives AI agents the ability to perform real-time Amazon product research:

- 🔍 **Market Validation** — Category size, concentration, new product rate
- 🎯 **Product Selection** — 14 built-in filter presets (beginner, fast-movers, emerging, etc.)
- 📊 **Competitor Analysis** — Brand/seller landscape, Chinese seller cases
- ⚠️ **Risk Assessment** — 6-dimension risk matrix with compliance alerts
- 💰 **Pricing Strategy** — Price band analysis, profit estimation
- 📈 **Daily Operations** — Market monitoring, alert signals

## Structure

```
apiclaw-analysis-skill/
├── SKILL.md                  # Main entry — intent routing, usage, evaluation criteria
├── references/
│   ├── reference.md          # API endpoints, fields, filters, scoring criteria
│   └── scenarios.md          # Advanced scenarios (evaluation, pricing, operations, expansion)
└── scripts/
    └── apiclaw.py            # CLI script — 8 subcommands, 14 preset modes
```

## Quick Start

1. Sign up at [apiclaw.io/api-keys](https://apiclaw.io/api-keys) → Create a new key (format: `hms_live_xxx`)
2. Tell your AI agent your API Key — it will handle the rest automatically.

## Script Commands

| Command | Description |
|---------|-------------|
| `categories` | Query Amazon category tree |
| `market` | Market-level aggregate data |
| `products` | Product search with filters (14 preset modes) |
| `competitors` | Competitor lookup by keyword/brand/ASIN |
| `product` | Real-time single ASIN details |
| `report` | Full market report (composite workflow) |
| `opportunity` | Product opportunity discovery (composite workflow) |
| `check` | API connectivity self-check |

## Product Selection Modes

14 built-in presets for `products --mode`:

`beginner` · `fast-movers` · `emerging` · `high-demand-low-barrier` · `single-variant` · `long-tail` · `underserved` · `new-release` · `fbm-friendly` · `low-price` · `broad-catalog` · `selective-catalog` · `speculative` · `top-bsr`

## Requirements

- Python 3.8+ (stdlib only, no pip dependencies)
- APIClaw API Key ([get one here](https://apiclaw.io/api-keys))

## API Coverage

| Endpoint | Description |
|----------|-------------|
| `categories` | Amazon category tree navigation |
| `markets/search` | Market-level metrics (concentration, brand count, etc.) |
| `products/search` | Product search with 20+ filter parameters |
| `products/competitor-lookup` | Competitor discovery by keyword/brand/ASIN |
| `realtime/product` | Real-time product details (reviews, features, variants) |

## License

MIT
