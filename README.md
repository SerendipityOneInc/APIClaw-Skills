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

## Skills Overview

This repo contains **10 agent skills** organized in two tiers:

**🏗️ Foundation** — data access and full-spectrum analysis:

| Skill | What It Does | Input | Output | Key Advantage |
|-------|-------------|-------|--------|---------------|
| 📦 [`apiclaw/`](apiclaw/) | Direct access to all 11 API endpoints — categories, markets, products, competitors, realtime, reviews, price bands, brands, history | Keyword, category, ASIN, or brand | Raw API data with field mapping and quirk documentation | Complete API reference — every other skill builds on this |
| 🎯 [`amazon-analysis/`](amazon-analysis/) | 13 built-in selection modes + market research, competitor analysis, ASIN evaluation, pricing, category research | Keyword/category/ASIN + intent | Analysis findings, top products, ASIN deep dives, confidence-tagged insights | Composite commands (`report`, `opportunity`) run multi-endpoint pipelines in one shot |

**⚡ Specialized** — purpose-built for specific workflows:

| Skill | What It Does | Input | Output | Key Advantage |
|-------|-------------|-------|--------|---------------|
| ⚔️ [`amazon-competitor-intelligence-monitor/`](amazon-competitor-intelligence-monitor/) | Deep competitor intelligence — Full Scan or Quick Check with tiered alerts | Keyword or ASIN(s), optionally your ASIN + competitor ASINs | Competitor matrix, brand ranking, price map, 30-day trends, scores (1-100), tiered alerts | Dual-mode (Full ~28-35 credits, Quick ~5-10) with three-tier alert system |
| 📡 [`amazon-daily-market-radar/`](amazon-daily-market-radar/) | Automated daily monitoring — price changes, new competitors, BSR movements, review spikes | Your ASINs (1-10) + keyword | RED/YELLOW/GREEN alerts, KPI dashboard, competitor movement, action items | Set-and-forget with signal validation (7+ day trends vs single-day spikes) |
| ✅ [`amazon-listing-audit-pro/`](amazon-listing-audit-pro/) | 8-dimension listing health check with optimization recommendations | Your ASIN + keyword | Score (X/100, A-F), 8-dimension scorecard, keyword gaps, priority fix list | Actionable rewrites using high-frequency review language; bulk audit support |
| 🚪 [`amazon-market-entry-analyzer/`](amazon-market-entry-analyzer/) | One-click market viability — discovers sub-markets, scores (1-100), delivers GO/CAUTION/AVOID | Keyword or category path | Sub-market landscape, verdict, market overview, brand landscape, entry strategy | Auto sub-market discovery with dual-level CR10 check |
| 📈 [`amazon-market-trend-scanner/`](amazon-market-trend-scanner/) | Category landscape scanning — trending subcategories, emerging niches, market shifts | 1+ category paths or keywords | Trend dashboard, Hot Categories TOP 5, new entrant scan, risk alerts | Category-level trend analysis across ALL subcategories |
| 💎 [`amazon-opportunity-discoverer/`](amazon-opportunity-discoverer/) | Profile-driven opportunity scanner — auto-selects strategies, validates with real-time data, 7-dimension scoring | Budget + experience level + keyword/category | Top 10 opportunities (S/A/B/C), detailed top 3 analysis, risk alerts | Profile-driven strategy auto-selection + Quick-Scan (~10 credits) |
| 💰 [`amazon-pricing-command-center/`](amazon-pricing-command-center/) | Data-driven pricing signals — auto-detects leaf category, analyzes pricing landscape | One or more ASINs | RAISE/HOLD/LOWER signal, price band heatmap, competitor price map, BuyBox analysis | ASIN-only input (no keyword needed), Sales/Competition Ratio |
| 💬 [`amazon-review-intelligence-extractor/`](amazon-review-intelligence-extractor/) | Deep consumer insights from 1B+ pre-analyzed reviews across 11 dimensions | Single ASIN, multiple ASINs, or category keyword | Pain points, buying factors, user profiles, usage patterns, differentiation roadmap | 1B+ pre-analyzed reviews (95% token savings), 11 dimensions |

## Quick Start

### 1. Install the Skills

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

You'll be prompted to select which skills to install:

**🏗️ Foundation:**
- **APIClaw — Amazon Commerce Data, 11 Endpoints**
- **Amazon Analysis — Full-Spectrum Research & Seller Intelligence**

**⚡ Specialized:**
- **Amazon Competitor Intelligence Monitor** — Dual-mode competitive intelligence with tiered alerts
- **Amazon Daily Market Radar — Automated Monitoring & Alerts**
- **Amazon Listing Audit Pro — 8-Dimension Health Check**
- **Amazon Market Entry Analyzer — GO/CAUTION/AVOID Verdicts**
- **Amazon Market Trend Scanner — Daily Category Radar**
- **Amazon Opportunity Discoverer — Niche Scanner & Scoring**
- **Amazon Pricing Command Center — RAISE/HOLD/LOWER Signals**
- **Amazon Review Intelligence Extractor — Consumer Insights from 1B+ Reviews**

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

## API Endpoints

**Base URL:** `https://api.apiclaw.io/openapi/v2`
**Auth:** `Authorization: Bearer $APICLAW_API_KEY`
**Method:** All endpoints use `POST` with JSON body

| Endpoint | Description | Example Use Case |
|----------|-------------|-----------------|
| 🔍 `products/search` | Product search with 13 preset modes, 20+ filters | *"Find running shoes under $80 with 4+ stars"* |
| 📊 `markets/search` | Market-level metrics — concentration, brand share, pricing | *"How competitive is the yoga mat market?"* |
| 🏷️ `products/competitors` | Competitor discovery by keyword, brand, or ASIN | *"Who are the top sellers in this niche?"* |
| ⚡ `realtime/product` | Real-time product details — reviews, features, variants | *"Get current details for ASIN B0D5CRV4KL"* |
| 💬 `reviews/analysis` | AI-powered review insights — sentiment, pain points | *"What do customers love/hate about this product?"* |
| 📁 `categories` | Amazon category tree navigation | *"Show subcategories under Electronics"* |
| 📈 `products/price-band-overview` | Price band summary with best opportunity band | *"What's the best price range for yoga mats?"* |
| 📊 `products/price-band-detail` | Full 5-band price distribution analysis | *"Show detailed price band breakdown for wireless earbuds"* |
| 🏢 `products/brand-overview` | Top-brand concentration metrics (CR10) | *"How concentrated is the brand landscape?"* |
| 🏷️ `products/brand-detail` | Per-brand breakdown with top products | *"Which brands dominate this category?"* |
| 📅 `products/history` | Historical daily snapshots for ASINs | *"Show price and BSR history for this ASIN"* |

## 13 Product Search Modes

The `products/search` endpoint supports 13 preset modes for different research strategies:

| Mode | Strategy | Target |
|------|----------|--------|
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
│   │   ├── scenarios-pricing.md            # Pricing strategy
│   │   ├── scenarios-ops.md                # Market monitoring, alerts
│   │   ├── scenarios-expand.md             # Expansion, trends
│   │   └── scenarios-listing.md            # Listing writing, optimization
│   └── scripts/
│       └── apiclaw.py                      # CLI — 8 subcommands, 13 preset modes
│
├── amazon-competitor-intelligence-monitor/  # Competitor intelligence & monitoring
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-daily-market-radar/            # Daily market pulse & anomaly detection
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-listing-audit-pro/             # Listing quality audit & optimization
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-market-entry-analyzer/         # Market viability assessment
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-opportunity-discoverer/        # Niche & opportunity identification
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-market-trend-scanner/           # Category landscape scanning & trend discovery
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-pricing-command-center/        # Pricing strategy & competitive signals
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
│
├── amazon-review-intelligence-extractor/    # Review intelligence & insight extraction
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── apiclaw.py
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
