# Amazon Blue Ocean Product Finder — APIClaw Agent Skill

> Find untapped products. High demand, low competition, real data.

## What This Skill Does

Discovers blue ocean products on Amazon — high demand, low competition, real profit potential. Three ways to use it:

1. **Specific market**: "Find blue ocean products in yoga mats" → scans that category
2. **Broad direction**: "Blue ocean in home products" → discovers sub-categories, you pick which to scan
3. **Full-site scan**: "Find me blue ocean products" → scans across ALL Amazon categories

For each approach, the skill:
- Scans up to 300 products using 3 blue-ocean modes (emerging, underserved, high-demand-low-barrier)
- Deduplicates and scores each candidate across 6 dimensions
- Deep-validates the top 20 with real-time data, brand analysis, price bands, consumer insights, and trends
- Delivers a **TOP 10 ranked list** with detailed analysis of the top 3

### What Makes This Different

- **No category required**: Can scan the entire Amazon catalog — no need to know where to look
- **11 API endpoints**: Not just product search. Every candidate is cross-validated with brand data, price band opportunity, consumer pain points, and historical trends
- **Blue ocean validation**: Automatically filters out false positives (low sales ≠ blue ocean, promotional pricing ≠ opportunity)
- **Confidence tagging**: Every data point tagged as 📊 Data-backed, 🔍 Inferred, or 💡 Directional

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Blue Ocean Product Finder** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Find blue ocean products under $30 with less than 100 reviews"*
- *"Find blue ocean products, price $15-35, 300+ monthly sales"*
- *"What are the best untapped product opportunities on Amazon right now?"*
- *"Scan the pet supplies category for hidden gems"*
- *"Find blue ocean"* (full-site scan, no restrictions)

## What You Get

| Section | Description |
|---------|-------------|
| 🔍 Scan Overview | Modes used, products scanned, filters applied |
| 🏆 TOP 10 Blue Ocean Products | Ranked by Blue Ocean Score with tier (S/A/B) |
| 📋 TOP 3 Detailed Analysis | Brand landscape, price positioning, pain points, trends |
| ⚠️ Risk Alerts | Declining trends, thin margins, seasonal, brand-dominated |
| 📊 Scoring Breakdown | 6-dimension scoring with rationale |
| 🎯 Next Steps | Actionable recommendations per tier |

## API Endpoints Used

All 11 APIClaw endpoints:

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category resolution (when market specified) |
| `markets/search` | Market-level context |
| `products/search` | Blue ocean product scanning (3 modes × 5 pages) |
| `products/competitor-lookup` | Competitive landscape |
| `realtime/product` | Real-time validation of top candidates |
| `reviews/analyze` | Consumer pain points and buying factors |
| `products/price-band-overview` | Best opportunity price band |
| `products/price-band-detail` | Detailed price band analysis |
| `products/brand-overview` | Brand concentration (CR10) |
| `products/brand-detail` | Per-brand breakdown |
| `products/product-history` | 30-day trend analysis |

## Credit Cost

~40-50 credits per scan.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
