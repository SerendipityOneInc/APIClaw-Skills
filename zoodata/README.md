# ZooData — Commerce Data Infrastructure for AI Agents

> 200M+ Amazon products. 22 endpoints. One API key.

## What This Skill Does

The foundational data layer for all ZooData agent skills. Provides direct access to 22 API endpoints covering category browsing, market metrics, product search (20+ filter fields), competitor lookup, real-time ASIN detail, AI review analysis, price band analysis, brand intelligence, product history, and keyword intelligence. Use this skill when you need raw API access or want to understand what data is available.

### What Makes This Different

- **22 endpoints in one skill**: Complete API reference with field mappings and known quirks
- **Critical pitfalls documented**: Category-first workflow, field naming differences across endpoints, aggregation gotchas
- **Cross-endpoint field guide**: Know exactly which field to use from which endpoint
- **Foundation for all skills**: Every ZooData skill builds on this data layer

## Install

```bash
npx skills add SerendipityOneInc/ZooData-Skills
```

Select **ZooData** when prompted.

## API Key Setup

1. Get a free key at [zoodata.ai/api-keys](https://zoodata.ai/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export ZOODATA_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"What ZooData endpoints are available?"*
- *"What ZooData endpoints are available and how do I use them?"*
- *"Look up real-time data for ASIN B0XXXXXXXX"*
- *"Search for products in the 'yoga mat' category sorted by sales"*
- *"Pull the market data for this product category"*

## What You Get

| Section | Description |
|---------|-------------|
| 📚 22 Endpoint Reference | Purpose, key parameters, output fields |
| ⚠️ API Pitfalls | Critical rules all skills must follow |
| 📊 Field Difference Table | Which field comes from which endpoint |
| 🏷️ Confidence Labels | Data-backed / Inferred / Directional tagging system |
| 📝 Known Quirks | String types, array handling, rate limits |

## API Endpoints

| # | Endpoint | Purpose |
|---|----------|---------|
| 1 | `categories` | Browse/search category tree |
| 2 | `markets/search` | Market-level metrics (sales, price, concentration) |
| 3 | `products/search` | Product search with 20+ filter fields (13 CLI presets) |
| 4 | `products/competitors` | Competitor discovery |
| 5 | `realtime/product` | Live ASIN detail (rating, BSR, Buy Box, variants) |
| 6 | `reviews/analysis` | AI review insights (sentiment, pain points, keywords) |
| 7 | `realtime/reviews` | Live raw review text |
| 8 | `products/price-band-overview` | Price band summary (hottest, best opportunity) |
| 9 | `products/price-band-detail` | Full 5-band distribution |
| 10 | `products/brand-overview` | Brand concentration (CR10) |
| 11 | `products/brand-detail` | Per-brand breakdown |
| 12 | `products/history` | Daily price/BSR/sales snapshots |
| 13 | `keywords/detail` | Keyword weekly snapshot |
| 14 | `keywords/market-profile` | Multidimensional weekly keyword market profile |
| 15 | `keywords/trend` | Keyword weekly trend |
| 16 | `keywords/trend-profile` | Keyword trend profile for fixed weekly windows |
| 17 | `keywords/extends` | Keyword expansion |
| 18 | `keywords/search-results` | Keyword SERP snapshot |
| 19 | `keywords/competitor-product-keywords` | Competitor ASIN keyword coverage |
| 20 | `keywords/product-traffic-terms` | ASIN traffic-driving keywords |
| 21 | `keywords/product-traffic-terms-profile` | Weekly ASIN traffic-term profile (batch up to 20 ASINs) |
| 22 | `keywords/product-traffic-terms-timeline` | ASIN + keyword timeline |

Keyword endpoint note: ZooData keyword data is estimated search, exposure, visibility, rank, placement, and impression evidence; it is not seller ABA-SQP or Amazon Ads performance. Analysis-stage routing, seller-artifact acquisition, and output policy are owned by [`amazon-keyword-traffic-analysis`](../amazon-keyword-traffic-analysis/).

Keyword date rule: keyword workflows are keyword-query lookups. When a keyword endpoint requires `date` or `dateTo`, prefer T-1 or earlier and avoid current-date lookup unless the user explicitly asks for today's data.

## Credit Cost

Varies per endpoint. Each call consumes credits — check `meta.creditsConsumed` in response. 1,000 free credits on signup.

## Powered By

[ZooData](https://zoodata.ai) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
