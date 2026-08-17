<p align="right">
  <a href="README.md">English</a> | <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <h1 align="center">ZooData Skills</h1>
</p>

<p align="center">
  <b>The data infrastructure built for agents.</b><br/>
  Currently powering Amazon commerce with 200M+ products, 1B+ reviews, and real-time signals.
</p>

<p align="center">
  <a href="https://github.com/SerendipityOneInc/ZooData-Skills/actions/workflows/test-zoodata.yml"><img src="https://github.com/SerendipityOneInc/ZooData-Skills/actions/workflows/test-zoodata.yml/badge.svg" alt="Tests" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" /></a>
  <a href="https://zoodata.ai"><img src="https://img.shields.io/badge/API-zoodata.ai-orange" alt="API" /></a>
  <a href="https://discord.gg/YfDFU9BDp5"><img src="https://img.shields.io/badge/Discord-Join-7289da?logo=discord&logoColor=white" alt="Discord" /></a>
  <a href="https://github.com/SerendipityOneInc/ZooData-Skills/stargazers"><img src="https://img.shields.io/github/stars/SerendipityOneInc/ZooData-Skills?style=social" alt="Stars" /></a>
</p>

<p align="center">
  <a href="https://zoodata.ai">Website</a> •
  <a href="https://zoodata.ai/en/api-keys">Get API Key</a> •
  <a href="https://discord.gg/YfDFU9BDp5">Discord</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-endpoints">API Reference</a>
</p>

---

## What is ZooData?

[ZooData](https://zoodata.ai) is the data infrastructure built for agents. Not a scraping API. Not a human dashboard. A purpose-built data layer that gives your AI agents direct access to Amazon commerce signals — 200M+ indexed products, 2+ years of history, and 1B+ reviews pre-processed into structured insights. Clean JSON, real-time, agent-ready.


https://github.com/user-attachments/assets/305a161b-7a53-49b8-afdc-4469a4fbf361



## Skills Overview

This repo contains **11 agent skills** organized in two tiers:

**🏗️ Foundation** — data access and full-spectrum analysis:

| Skill | What It Does | Input | Output | Key Advantage |
|-------|-------------|-------|--------|---------------|
| 📦 [`zoodata/`](zoodata/) | Direct access to all 22 API endpoints — 12 commerce endpoints plus 10 keyword-intelligence endpoints | Keyword, category, ASIN, or brand | Raw API data with field mapping and quirk documentation | Complete API reference — every other skill builds on this |
| 🎯 [`amazon-analysis/`](amazon-analysis/) | 13 built-in selection modes + market research, competitor analysis, ASIN evaluation, pricing, category research | Keyword/category/ASIN + intent | Analysis findings, top products, ASIN deep dives, confidence-tagged insights | Composite commands (`report`, `opportunity`) run multi-endpoint pipelines in one shot |
| 🔎 [`amazon-keyword-traffic-analysis/`](amazon-keyword-traffic-analysis/) | Keyword value and product traffic-health workflows built on 10 keyword intelligence endpoints | Seed keyword, target keyword, ASIN, or ASIN + keyword | Expansion tiers, keyword-value analysis, product traffic structure, trends, and health diagnosis | Dedicated flows for keyword expansion, keyword analysis, and product traffic analysis |

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
npx skills add SerendipityOneInc/ZooData-Skills
```

You'll be prompted to select which skills to install:

**🏗️ Foundation:**
- **ZooData — Amazon Commerce Data, 11 Endpoints**
- **Amazon Analysis — Full-Spectrum Research & Seller Intelligence**
- **Amazon Keyword Intelligence — Expansion, Reverse ASIN & Monitoring**

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
git clone https://github.com/SerendipityOneInc/ZooData-Skills.git
```

### 2. Set Your API Key

```bash
export ZOODATA_API_KEY='hms_live_xxx'   # Get yours free at zoodata.ai/en/api-keys
```

> 🎁 **Free tier**: 1,000 credits on signup. 1 credit = 1 API call. No credit card required.

### 3. Try It

Ask your AI agent:

> *"Analyze the competitive landscape for wireless earbuds under $50 on Amazon US"*

Or use the CLI directly:

```bash
python amazon-analysis/scripts/zoodata.py products --keyword "wireless earbuds" --mode fast-movers
```

## API Endpoints

**Base URL:** `https://api.zoodata.ai/openapi/v2`
**Auth:** `Authorization: Bearer $ZOODATA_API_KEY`
**Method:** All endpoints use `POST` with JSON body

| Endpoint | Description | Example Use Case |
|----------|-------------|-----------------|
| 🔍 `products/search` | Product search with 20+ filters (13 preset modes via the CLI) | *"Find running shoes under $80 with 4+ stars"* |
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

The skill CLI (`zoodata.py --mode`) provides 13 preset modes for different research strategies. Modes are expanded into concrete filter fields (`monthlySalesMin`, `salesGrowthRateMin`, …) on the client side — `mode` is **not** an API parameter, and sending it to `/openapi/v2/products/search` returns 422:

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
├── zoodata/                              # Data layer skill (lightweight)
│   ├── SKILL.md                            # 22 endpoints, quick start
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
│       └── zoodata.py                      # CLI — 8 subcommands, 13 preset modes
│
├── amazon-keyword-traffic-analysis/      # Keyword intelligence & traffic analysis
│   ├── SKILL.md
│   ├── README.md
│   └── references/
│       ├── reference.md                    # Keyword endpoint reference
│       ├── execution-guide.md              # Execution and monitoring rules
│       ├── scenarios-expand.md             # Keyword expansion
│       ├── scenarios-keyword-analysis.md   # Keyword value and trend analysis
│       └── scenarios-product-traffic-analysis.md # Product traffic health analysis
│
├── amazon-competitor-intelligence-monitor/  # Competitor intelligence & monitoring
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-daily-market-radar/            # Daily market pulse & anomaly detection
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-listing-audit-pro/             # Listing quality audit & optimization
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-market-entry-analyzer/         # Market viability assessment
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-opportunity-discoverer/        # Niche & opportunity identification
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-market-trend-scanner/           # Category landscape scanning & trend discovery
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-pricing-command-center/        # Pricing strategy & competitive signals
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── amazon-review-intelligence-extractor/    # Review intelligence & insight extraction
│   ├── SKILL.md
│   ├── references/
│   │   └── reference.md
│   └── scripts/
│       └── zoodata.py
│
├── scoring-methodology.md                # Unified quality scoring framework
├── CHANGELOG.md
└── README.md
```

## Requirements

- Python 3.8+ (stdlib only, zero pip dependencies)
- ZooData API Key ([get one free](https://zoodata.ai/en/api-keys))

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Community

- 💬 [Discord](https://discord.gg/YfDFU9BDp5) — Chat, get help, share what you're building
- 🐛 [Issues](https://github.com/SerendipityOneInc/ZooData-Skills/issues) — Bug reports and feature requests
- 📖 [API Docs](https://zoodata.ai) — Full API documentation

## License

[MIT](LICENSE) © [SerendipityOne Inc.](https://zoodata.ai)
