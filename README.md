# APIClaw Skills

> AI-powered commerce data infrastructure. Backed by 200M+ product database. Powered by [APIClaw API](https://apiclaw.io).

This repo contains two skills for AI agents:

## Skills

### 📦 `apiclaw/` — General Skill (lightweight)

APIClaw platform overview — what it can do, 6 API endpoints, quick start guide.

**Best for:** Understanding APIClaw capabilities, getting started, general commerce data queries.

### 🎯 `amazon-analysis/` — Amazon Product Research (deep)

Full Amazon seller toolkit — 14 selection strategies, risk assessment, competitor analysis, listing optimization, market monitoring.

**Best for:** Serious Amazon product research, FBA/FBM sourcing, daily seller operations.

## Structure

```
├── apiclaw/                        # General skill
│   ├── SKILL.md                      # Capabilities overview, quick start
│   └── references/
│       └── openapi-reference.md      # API field reference
│
├── amazon-analysis/                # Amazon deep skill
│   ├── SKILL.md                      # Intent routing, workflows, evaluation criteria
│   ├── references/
│   │   ├── reference.md              # Full API reference
│   │   ├── scenarios-composite.md    # Comprehensive recommendations
│   │   ├── scenarios-eval.md         # Product evaluation, risk, reviews
│   │   ├── scenarios-pricing.md      # Pricing strategy, profit estimation
│   │   ├── scenarios-ops.md          # Market monitoring, alerts
│   │   ├── scenarios-expand.md       # Expansion, trends
│   │   └── scenarios-listing.md      # Listing writing, optimization
│   └── scripts/
│       └── apiclaw.py                # CLI — 8 subcommands, 14 preset modes
```

## Installation

### ClawHub

```bash
# Amazon deep skill (published on ClawHub)
npx clawhub install Amazon-analysis-skill
```

### Manual

Clone this repo into your agent's skill directory and point to the desired `SKILL.md`.

## Setup

1. Get API Key: [apiclaw.io/api-keys](https://apiclaw.io/api-keys)
2. Set env: `export APICLAW_API_KEY='hms_live_xxx'`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `categories` | Amazon category tree navigation |
| `markets/search` | Market-level metrics (concentration, brand count, etc.) |
| `products/search` | Product search with 14 preset modes, 20+ filters |
| `products/competitor-lookup` | Competitor discovery by keyword/brand/ASIN |
| `realtime/product` | Real-time product details (reviews, features, variants) |
| `reviews/analyze` | AI-powered review insights (sentiment, pain points, buying factors) |

## Requirements

- Python 3.8+ (stdlib only, no pip dependencies)
- APIClaw API Key ([get one here](https://apiclaw.io/api-keys))

## License

MIT
