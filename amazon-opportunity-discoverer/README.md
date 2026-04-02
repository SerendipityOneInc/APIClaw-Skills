# Amazon Opportunity Discoverer — APIClaw Agent Skill

> Tell me your budget and experience. I find opportunities, score them, and rank.

## What This Skill Does

Automated product opportunity scanner tailored to your seller profile. Tell it your budget, experience level, and risk tolerance — it selects the right strategies from 14 preset modes, scans categories, validates candidates with real-time data, and ranks opportunities by a 7-dimension composite score (1-100). From beginner-friendly picks to advanced aggressive plays.

### What Makes This Different

- **Profile-driven strategy**: Auto-selects scanning modes based on your budget, experience, and risk tolerance
- **7-dimension scoring**: Demand, Competition Gap, Price Opportunity, Trend, Profit Margin, Differentiation, Profile Fit
- **Tiered results**: S-tier 🔥 (act fast), A-tier ✅ (pursue), B-tier ⚠️ (needs differentiation), C-tier ❌ (skip)
- **Smart category selection**: No category? Scans market data to find the best subcategories for you
- **Quick-Scan mode**: ~10 credits for directional results when you just need a quick look

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Opportunity Discoverer** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"I'm a beginner with $5K budget, find me safe product opportunities"*
- *"我是新手卖家，预算 3 万，帮我找适合的产品"*
- *"Find aggressive opportunities in home & kitchen, I have 2 years experience"*
- *"Scan for products under $30 with less than 100 reviews and 300+ monthly sales"*
- *"帮我做一次快速扫描，看看有什么机会"*

## What You Get

| Section | Description |
|---------|-------------|
| 🔍 Scan Summary | Modes used, filters applied, products scanned |
| 🏆 Top 10 Opportunities | Ranked by composite score with S/A/B/C tiers |
| 📋 Top 3 Detailed Analysis | Deep dive with brand, price, pain points, trends |
| 🗺️ Category Heatmap | Subcategory opportunity comparison |
| ⚠️ Risk Alerts | Declining trends, thin margins, brand-dominated |
| 🎯 Next Steps | S: buy sample, A: deep-dive, B: watch |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category resolution and selection |
| `markets/search` | Market metrics for category ranking |
| `products/search` | Multi-mode product scanning |
| `products/competitor-lookup` | Competitive landscape |
| `realtime/product` | Real-time validation of top candidates |
| `reviews/analyze` | Pain points and differentiation gaps |
| `products/price-band-overview` | Price opportunity assessment |
| `products/price-band-detail` | Detailed price band analysis |
| `products/brand-overview` | Brand concentration |
| `products/brand-detail` | Per-brand breakdown |
| `products/product-history` | Trend validation |

## Credit Cost

Full scan: ~50-60 credits. Quick-Scan mode: ~10 credits (directional only).

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
