# Amazon Listing Audit Pro — APIClaw Agent Skill

> 8-dimension health check. Benchmark against leaders. Fix what matters most.

## What This Skill Does

Comprehensive listing health check and optimization engine. Scores your listing across 8 weighted dimensions, benchmarks against category leaders, identifies keyword gaps, and generates data-backed improvement recommendations with suggested rewrites. Supports single ASIN or bulk audit for agencies.

### What Makes This Different

- **8-dimension scoring**: Title, Bullets, Images, A+ Content, Reviews, Keywords, Category Fit, Pricing — each scored 0-100 with weighted total
- **Leader benchmarking**: Side-by-side comparison with Top 3 category leaders
- **Keyword gap analysis**: Finds missing keywords from top competitor titles and bullets
- **Actionable rewrites**: Suggested title and bullet improvements using high-frequency review language
- **Bulk audit**: Supports 10-100+ ASINs with shared market data

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Listing Audit Pro** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Audit my listing for ASIN B0XXXXXXXX, keyword 'yoga mat'"*
- *"Run a listing health check for ASIN B0XXXXXXXX"*
- *"How does my listing compare to the top sellers in my category?"*
- *"What keywords am I missing compared to competitors?"*
- *"Batch audit the listing quality for these 5 ASINs"*

## What You Get

| Section | Description |
|---------|-------------|
| 🏆 Overall Score | X/100 with A-F grade |
| 📊 8-Dimension Scorecard | Per-dimension scores with basis |
| 📝 Title Audit | Analysis + suggested rewrite |
| 🔫 Bullets Audit | vs leaders, missing points, rewrites |
| 🖼️ Image Audit | Count, type, quality assessment |
| ⭐ Review Health | Rating breakdown, sentiment, pain points |
| 🔑 Keyword Gap Analysis | Missing keywords vs Top 5 leaders |
| 📋 vs Category Leaders | Side-by-side Top 3 comparison |
| 🎯 Priority Fix List | Lowest scores first, highest impact |

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category resolution |
| `markets/search` | Market benchmarks |
| `products/search` | Category product landscape |
| `products/competitor-lookup` | Leader discovery |
| `realtime/product` | Live listing details (yours + leaders) |
| `reviews/analyze` | Review sentiment and keywords |
| `products/price-band-overview` | Pricing opportunity |
| `products/price-band-detail` | Price band analysis |
| `products/brand-overview` | Brand landscape |
| `products/brand-detail` | Brand breakdown |
| `products/product-history` | BSR and price trends |

## Credit Cost

~20-25 credits per ASIN. Bulk audits share market data across ASINs.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
