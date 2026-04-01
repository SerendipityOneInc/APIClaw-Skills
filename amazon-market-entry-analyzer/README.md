# Amazon Market Entry Analyzer — APIClaw Agent Skill

> One input. Complete market viability assessment with sub-market discovery. **GO / CAUTION / AVOID.**

## What This Skill Does

Evaluates whether a product category on Amazon is worth entering. Give it a keyword or category, and it:

1. **Discovers all sub-markets** within the category — finds every leaf-level niche and ranks them by opportunity
2. **Deep-dives top sub-markets** — pulls data from all 11 APIClaw endpoints for comprehensive analysis
3. **Scores market viability** (1-100) across 7 dimensions: market size, trend, competition, pricing, new entrant space, consumer pain points, and profit potential
4. **Delivers a verdict** — GO ✅ / CAUTION ⚠️ / AVOID 🔴 with confidence-tagged reasoning

### What Makes This Different

- **Sub-market discovery**: Don't just analyze "Fitness" — automatically find and compare 46+ leaf sub-markets (Protein Whey, Resistance Bands, Yoga Mats...) to pinpoint the best entry point
- **11 API endpoints**: Every data source cross-validated. Not just market metrics — includes competitor deep-dives, consumer pain points, price band analysis, brand landscape, and historical trends
- **Confidence tagging**: Every data point tagged as 📊 Data-backed, 🔍 Inferred, or 💡 Directional — you always know what's hard data vs. interpretation

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Market Entry Analyzer** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Should I enter the yoga mat market on Amazon?"*
- *"Analyze the protein supplement category — is it worth it for a new seller?"*
- *"Compare sub-markets within Pet Supplies > Dogs to find the best niche"*
- *"Evaluate wireless earbuds under $50 — GO or AVOID?"*

## What You Get

A comprehensive market entry report including:

| Section | Description |
|---------|-------------|
| 🗺️ Sub-Market Landscape | All sub-markets ranked by opportunity score |
| 📊 Executive Summary | Score (1-100), GO/CAUTION/AVOID verdict |
| 📈 Market Overview | Market value, SKU count, demand, pricing |
| 📉 Market Trend | 30-day BSR/price/sales trajectory |
| 🏷️ Brand Landscape | Brand count, CR10, top 5 brands |
| 💰 Price Structure | 5-band analysis, opportunity bands |
| 🏆 Top 5 Competitors | Side-by-side with realtime data |
| 💬 Consumer Insights | Pain points, buying factors, gaps |
| 📋 Scoring Breakdown | 7-dimension weighted scoring |
| 🎯 Entry Strategy | Target price, differentiation, expected sales |
| 🎯 Cross-Market Comparison | Side-by-side sub-market comparison with final recommendation |

## API Endpoints Used

All 11 APIClaw endpoints:

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category tree navigation and resolution |
| `markets/search` | Market-level metrics + sub-market discovery |
| `products/search` | Product supply analysis (100+ products) |
| `products/competitor-lookup` | Competitor discovery |
| `realtime/product` | Live competitor details |
| `reviews/analyze` | AI-powered consumer insights |
| `products/price-band-overview` | Price band opportunities |
| `products/price-band-detail` | Detailed 5-band breakdown |
| `products/brand-overview` | Brand concentration (CR10) |
| `products/brand-detail` | Per-brand analysis |
| `products/product-history` | 30-day trend analysis |

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
