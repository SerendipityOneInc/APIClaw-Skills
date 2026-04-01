<p align="right">
  <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <h1 align="center">APIClaw Skills</h1>
</p>

<p align="center">
  <b>The data infrastructure built for agents.</b><br/>
  Currently powering Amazon commerce with 200M+ products, 1B+ reviews, and real-time signals.
</p>

<p align="center">
  <a href="https://github.com/SerendipityOneInc/APIClaw-Skills/actions/workflows/ci.yml"><img src="https://github.com/SerendipityOneInc/APIClaw-Skills/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://apiclaw.io"><img src="https://img.shields.io/badge/API-apiclaw.io-orange" alt="API" /></a>
  <a href="https://discord.gg/YfDFU9BDp5"><img src="https://img.shields.io/badge/Discord-Join-7289da?logo=discord&logoColor=white" alt="Discord" /></a>
  <a href="https://github.com/SerendipityOneInc/APIClaw-Skills/stargazers"><img src="https://img.shields.io/github/stars/SerendipityOneInc/APIClaw-Skills?style=social" alt="Stars" /></a>
</p>

<p align="center">
  <a href="https://apiclaw.io">Website</a> •
  <a href="https://apiclaw.io/en/api-keys">Get API Key</a> •
  <a href="https://discord.gg/YfDFU9BDp5">Discord</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-endpoints">API Reference</a>
</p>

---

## What is APIClaw?

[APIClaw](https://apiclaw.io) is the data infrastructure built for agents. Not a scraping API. Not a human dashboard. A purpose-built data layer that gives your AI agents direct access to Amazon commerce signals — 200M+ indexed products, 2+ years of history, and 1B+ reviews pre-processed into structured insights. Clean JSON, real-time, agent-ready.

This repo contains **9 agent skills** that let any AI assistant use APIClaw instantly:

| Skill | Description | Best For |
|-------|------------|----------|
| 📦 **[`apiclaw/`](apiclaw/)** | Data layer overview, 11 API endpoints, quick integration | Getting started, agent tool-calling |
| 🎯 **[`amazon-analysis/`](amazon-analysis/)** | 14 selection strategies, market validation, competitor intelligence | Deep product research, autonomous sourcing |
| ⚔️ **[`amazon-competitor-war-room/`](amazon-competitor-war-room/)** | Real-time competitive monitoring and response strategy | Tracking competitors, price wars |
| 📡 **[`amazon-daily-market-radar/`](amazon-daily-market-radar/)** | Daily market pulse check and anomaly detection | Morning briefings, trend alerts |
| ✅ **[`amazon-listing-audit-pro/`](amazon-listing-audit-pro/)** | Comprehensive listing quality audit and optimization | Listing health checks, conversion improvement |
| 🚪 **[`amazon-market-entry-analyzer/`](amazon-market-entry-analyzer/)** | Market viability assessment for new category entry | Go/no-go decisions, market sizing |
| 💎 **[`amazon-opportunity-discoverer/`](amazon-opportunity-discoverer/)** | Underserved niche and opportunity identification | Finding blue ocean markets |
| 💰 **[`amazon-pricing-command-center/`](amazon-pricing-command-center/)** | Dynamic pricing strategy and margin optimization | Price positioning, profit maximization |
| 💬 **[`amazon-review-intelligence-engine/`](amazon-review-intelligence-engine/)** | Deep review sentiment analysis and insight extraction | Customer voice analysis, product improvement |

## Quick Start

### 1. Install the Skills

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

You'll be prompted to select which skills to install:
- **APIClaw — Commerce Data for AI Agents** (general overview, 6 endpoints)
- **Amazon Product Research & Seller Analytics** (deep analysis, 14 strategies)

Or clone manually:
```bash
git clone https://github.com/SerendipityOneInc/APIClaw-Skills.git
```

### 2. Set Your API Key

```bash
export APICLAW_API_KEY='hms_live_xxx'   # Get yours free at apiclaw.io/en/api-keys
```

> 🎁 **Free tier**: 1,000 credits on signup. 1 credit = 1 API call. No credit card required.

### 3. Try It

Ask your AI agent:

> *"Analyze the competitive landscape for wireless earbuds under $50 on Amazon US"*

Or use the CLI directly:

```bash
python amazon-analysis/scripts/apiclaw.py products --keyword "wireless earbuds" --mode competitive_landscape
```

## Example: Product Search

```bash
curl -X POST 'https://api.apiclaw.io/openapi/v2/products/search' \
  -H 'Authorization: Bearer hms_live_xxx' \
  -H 'Content-Type: application/json' \
  -d '{
    "keyword": "wireless earbuds",
    "mode": "beginner",
    "priceMax": 50,
    "pageSize": 3
  }'
```

Example response (simplified):

```json
{
  "products": [
    {
      "asin": "B0D5CRV4KL",
      "title": "Wireless Earbuds Bluetooth 5.3 ...",
      "price": 29.99,
      "rating": 4.5,
      "ratingCount": 12847,
      "bsrRank": 15,
      "atLeastMonthlySales": 8500,
      "brand": "SoundCore",
      "profitMargin": 0.42
    }
  ]
}
```

> **Note:** This is a simplified example. Actual responses include additional fields. See [API reference](apiclaw/references/openapi-reference.md) for full field list.

## API Endpoints

| Endpoint | Description | Example Use Case |
|----------|-------------|-----------------|
| 🔍 `products/search` | Product search with 14 preset modes, 20+ filters | *"Find running shoes under $80 with 4+ stars"* |
| 📊 `markets/search` | Market-level metrics — concentration, brand share, pricing | *"How competitive is the yoga mat market?"* |
| 🏷️ `products/competitor-lookup` | Competitor discovery by keyword, brand, or ASIN | *"Who are the top sellers in this niche?"* |
| ⚡ `realtime/product` | Real-time product details — reviews, features, variants | *"Get current details for ASIN B0D5CRV4KL"* |
| 💬 `reviews/analyze` | AI-powered review insights — sentiment, pain points | *"What do customers love/hate about this product?"* |
| 📁 `categories` | Amazon category tree navigation | *"Show subcategories under Electronics"* |
| 📈 `products/price-band-overview` | Price band summary with best opportunity band | *"What's the best price range for yoga mats?"* |
| 📊 `products/price-band-detail` | Full 5-band price distribution analysis | *"Show detailed price band breakdown for wireless earbuds"* |
| 🏢 `products/brand-overview` | Top-brand concentration metrics (CR10) | *"How concentrated is the brand landscape?"* |
| 🏷️ `products/brand-detail` | Per-brand breakdown with top products | *"Which brands dominate this category?"* |
| 📅 `products/product-history` | Historical daily snapshots for ASINs | *"Show price and BSR history for this ASIN"* |

**Base URL:** `https://api.apiclaw.io/openapi/v2`  
**Auth:** `Authorization: Bearer $APICLAW_API_KEY`  
**Method:** All endpoints use `POST` with JSON body

## 14 Product Search Modes

The `products/search` endpoint supports 14 preset modes for different research strategies:

| Mode | Strategy | Target |
|------|----------|--------|
| `beginner` | Low competition, easy entry | New sellers |
| `fast-movers` | High sales velocity | Quick revenue |
| `emerging` | Rising trends, low saturation | Early movers |
| `long-tail` | Niche keywords, steady demand | Sustainable income |
| `underserved` | High demand, few sellers | Market gaps |
| `new-release` | Recently launched products | Trending items |
| `fbm-friendly` | Suitable for merchant fulfillment | Low-investment start |
| `low-price` | Budget-friendly products | Volume strategy |
| `single-variant` | Simple listings, no variants | Easy management |
| `high-demand-low-barrier` | High sales, low review barrier | Scalable entry |
| `broad-catalog` | Wide product range analysis | Category overview |
| `selective-catalog` | Curated high-quality picks | Premium selection |
| `speculative` | High-risk, high-reward opportunities | Aggressive strategy |
| `top-bsr` | Best Seller Rank leaders | Market leaders |

## Use Cases

- 🔎 **Product Research** — Find profitable niches with low competition
- 📈 **Competitor Monitoring** — Track pricing, reviews, and BSR changes
- ✍️ **Listing Optimization** — AI-powered review analysis to improve your listings
- 🚀 **Market Entry Analysis** — Evaluate market size, competition, and profit potential
- 📊 **Trend Detection** — Spot rising products and emerging categories

## Project Structure

```
├── apiclaw/                              # Data layer skill (lightweight)
│   ├── SKILL.md                            # 11 endpoints, quick start
│   └── references/
│       └── openapi-reference.md            # API field reference
│
├── amazon-analysis/                      # Deep analysis skill
│   ├── SKILL.md                            # Intent routing, workflows, evaluation criteria
│   ├── references/
│   │   ├── reference.md                    # Full API reference
│   │   ├── execution-guide.md              # Step-by-step execution playbook
│   │   ├── scenarios-composite.md          # Comprehensive recommendations
│   │   ├── scenarios-eval.md               # Product evaluation, risk, reviews
│   │   ├── scenarios-pricing.md            # Pricing strategy, profit estimation
│   │   ├── scenarios-ops.md                # Market monitoring, alerts
│   │   ├── scenarios-expand.md             # Expansion, trends
│   │   └── scenarios-listing.md            # Listing writing, optimization
│   └── scripts/
│       └── apiclaw.py                      # CLI — 8 subcommands, 14 preset modes
│
├── amazon-competitor-war-room/           # Competitive monitoring & response
│   └── SKILL.md
│
├── amazon-daily-market-radar/            # Daily market pulse & anomaly detection
│   └── SKILL.md
│
├── amazon-listing-audit-pro/             # Listing quality audit & optimization
│   └── SKILL.md
│
├── amazon-market-entry-analyzer/         # Market viability assessment
│   └── SKILL.md
│
├── amazon-opportunity-discoverer/        # Niche & opportunity identification
│   └── SKILL.md
│
├── amazon-pricing-command-center/        # Pricing strategy & margin optimization
│   └── SKILL.md
│
├── amazon-review-intelligence-engine/    # Review sentiment & insight extraction
│   └── SKILL.md
│
├── scoring-methodology.md                # Unified quality scoring framework
├── CHANGELOG.md
└── README.md
```

## Requirements

- Python 3.8+ (stdlib only, zero pip dependencies)
- APIClaw API Key ([get one free](https://apiclaw.io/en/api-keys))

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Community

- 💬 [Discord](https://discord.gg/YfDFU9BDp5) — Chat, get help, share what you're building
- 🐛 [Issues](https://github.com/SerendipityOneInc/APIClaw-Skills/issues) — Bug reports and feature requests
- 📖 [API Docs](https://apiclaw.io) — Full API documentation

## License

[MIT](LICENSE) © [SerendipityOne Inc.](https://apiclaw.io)
