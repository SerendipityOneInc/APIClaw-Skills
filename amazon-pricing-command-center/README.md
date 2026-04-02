# Amazon Pricing Command Center — APIClaw Agent Skill

> Give me your ASIN(s). RAISE, HOLD, or LOWER — backed by data.

## What This Skill Does

Data-driven pricing strategy engine for Amazon sellers. Just provide your ASIN(s) — the skill auto-detects each product's leaf category, analyzes the pricing landscape, and delivers clear RAISE/HOLD/LOWER signals with profit simulation. Supports single ASIN or batch analysis with auto-grouping by category.

### What Makes This Different

- **ASIN-only input**: No keyword needed — auto-detects leaf category from BSR data
- **Clear pricing signals**: RAISE / HOLD / LOWER with data-backed reasoning
- **Profit simulation**: 3 scenarios (Conservative, Moderate, Aggressive) with full cost breakdown
- **Sales/Competition Ratio**: Identifies the best entry price band by demand-to-barrier ratio, not just highest sales
- **Batch mode**: Multiple ASINs auto-grouped by category to share market data and save credits

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Pricing Command Center** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Should I raise or lower the price on ASIN B0XXXXXXXX?"*
- *"帮我分析这个 ASIN 的定价策略：B0XXXXXXXX"*
- *"Analyze pricing for these 5 ASINs: B0AAA, B0BBB, B0CCC, B0DDD, B0EEE"*
- *"My COGS is $8, current price $24.99 — am I leaving money on the table?"*
- *"该涨价还是降价？ASIN B0XXXXXXXX，成本 ¥45"*

## What You Get

| Section | Description |
|---------|-------------|
| 🚦 Price Signal | RAISE / HOLD / LOWER with reasoning |
| 📍 Current Position | Where you sit in the category price landscape |
| 💰 Price Band Heatmap | Sales/Competition Ratio per band |
| 🏷️ Competitor Price Map | Top 10 competitors in leaf category |
| 📈 30-Day Trend | Price and BSR movement |
| 💵 Profit Simulation | 3 scenarios with revenue, fees, and net profit |
| 🛒 BuyBox Analysis | Current Buy Box status and strategy |
| 🎯 Recommended Price | Data-backed optimal price point |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `realtime/product` | ASIN detail + leaf category detection |
| `categories` | Category path resolution |
| `markets/search` | Market-level pricing context |
| `products/search` | Category product landscape |
| `products/competitor-lookup` | Competitor pricing |
| `products/price-band-overview` | Opportunity band identification |
| `products/price-band-detail` | Full price distribution |
| `products/brand-overview` | Brand concentration |
| `products/brand-detail` | Per-brand pricing |
| `products/product-history` | Price and BSR trends |

## Credit Cost

Single ASIN: ~20-25 credits. Batch (same category): ~20-25 + 1 per additional ASIN. Batch (different categories): ~20-25 per unique category.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
