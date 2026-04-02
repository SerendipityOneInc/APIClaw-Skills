# APIClaw — Commerce Data Infrastructure for AI Agents

> 200M+ Amazon products. 11 endpoints. One API key.

## What This Skill Does

The foundational data layer for all APIClaw agent skills. Provides direct access to 11 API endpoints covering category browsing, market metrics, product search (14 modes), competitor lookup, real-time ASIN detail, AI review analysis, price band analysis, brand intelligence, and product history. Use this skill when you need raw API access or want to understand what data is available.

### What Makes This Different

- **11 endpoints in one skill**: Complete API reference with field mappings and known quirks
- **Critical pitfalls documented**: Category-first workflow, field naming differences across endpoints, aggregation gotchas
- **Cross-endpoint field guide**: Know exactly which field to use from which endpoint
- **Foundation for all skills**: Every APIClaw skill builds on this data layer

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **APIClaw** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"What APIClaw endpoints are available?"*
- *"APIClaw 有哪些接口？怎么用？"*
- *"Look up real-time data for ASIN B0XXXXXXXX"*
- *"Search for products in the 'yoga mat' category sorted by sales"*
- *"帮我查一下这个品类的市场数据"*

## What You Get

| Section | Description |
|---------|-------------|
| 📚 11 Endpoint Reference | Purpose, key parameters, output fields |
| ⚠️ API Pitfalls | Critical rules all skills must follow |
| 📊 Field Difference Table | Which field comes from which endpoint |
| 🏷️ Confidence Labels | Data-backed / Inferred / Directional tagging system |
| 📝 Known Quirks | String types, array handling, rate limits |

## API Endpoints

| # | Endpoint | Purpose |
|---|----------|---------|
| 1 | `categories` | Browse/search category tree |
| 2 | `markets/search` | Market-level metrics (sales, price, concentration) |
| 3 | `products/search` | Product search with 14 selection modes |
| 4 | `products/competitor-lookup` | Competitor discovery |
| 5 | `realtime/product` | Live ASIN detail (rating, BSR, Buy Box, variants) |
| 6 | `reviews/analyze` | AI review insights (sentiment, pain points, keywords) |
| 7 | `products/price-band-overview` | Price band summary (hottest, best opportunity) |
| 8 | `products/price-band-detail` | Full 5-band distribution |
| 9 | `products/brand-overview` | Brand concentration (CR10) |
| 10 | `products/brand-detail` | Per-brand breakdown |
| 11 | `products/product-history` | Daily price/BSR/sales snapshots |

## Credit Cost

Varies per endpoint. Each call consumes credits — check `meta.creditsConsumed` in response. 1,000 free credits on signup.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
