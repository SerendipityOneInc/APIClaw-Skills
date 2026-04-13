---
name: APIClaw — Amazon Commerce Data, 11 Endpoints
version: 1.1.1
description: >
  General overview, 11 API endpoints.
  AI-powered commerce data infrastructure with 200M+ Amazon products.
  Endpoints: category browsing, market metrics, product search,
  competitor lookup, realtime ASIN detail, AI review analysis,
  price band overview/detail, brand overview/detail, and product history.
  Use when user asks: what APIClaw can do, available API endpoints,
  how to get started, API capabilities overview, credit usage, or
  general commerce data questions. For deep Amazon product selection
  strategies and analysis workflows, use the Amazon-analysis-skill instead.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

> **📋 Live API Reference**: Field names and parameters may change. If you encounter field errors,
> check the latest OpenAPI spec at https://apiclaw.io/api/v1/openapi-spec for current field definitions.

# APIClaw — Commerce Data Infrastructure for AI Agents

200M+ Amazon products. 11 endpoints. One API key.

## Quick Start
1. Get key: [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) (1,000 free credits)
2. `export APICLAW_API_KEY='hms_live_xxx'`
3. Base URL: `https://api.apiclaw.io/openapi/v2` — all POST with JSON body
4. Auth: `Authorization: Bearer YOUR_API_KEY`
5. New keys need 3-5s to activate. If 403, wait and retry.

## ⚠️ Critical API Pitfalls (ALL skills must follow)
1. **Keyword search is broad** → MUST lock `categoryPath` first via `categories` endpoint
2. **Brand/price-band queries MUST include --category** to avoid cross-category contamination
3. **Revenue** = `sampleAvgMonthlyRevenue` directly. **NEVER** calculate avgPrice × totalSales (overestimates 30-70%)
4. **Sales** = `monthlySalesFloor` (lower bound). Fallback: 300,000 / BSR^0.65, tag as 🔍
5. **Use API fields directly**: `sampleOpportunityIndex`, `sampleTop10BrandSalesRate` — never reinvent
6. **reviews/analysis** needs 50+ reviews; fallback to realtime ratingBreakdown
7. **Aggregation endpoints** (price-band, brand) without categoryPath produce severely distorted data
8. **Price-band and brand endpoints only accept `keyword`** (not categoryPath) — cross-validate returned products

## 11 Endpoints

| # | Endpoint | Purpose | Key Output |
|---|----------|---------|------------|
| 1 | `categories` | Browse/search category tree | categoryPath, productCount |
| 2 | `markets/search` | Market-level metrics | sampleAvgMonthlySales, sampleAvgPrice, topSalesRate, sampleNewSkuRate |
| 3 | `products/search` | Product search (14 modes) | asin, price, monthlySalesFloor, rating, ratingCount, fbaFee |
| 4 | `products/competitors` | Competitor discovery | same fields as products/search |
| 5 | `realtime/product` | Live ASIN detail | rating, features, bestsellersRank[], buyboxWinner.price, variants |
| 6 | `reviews/analysis` | AI review insights (11 dims) | sentimentDistribution, consumerInsights, topKeywords |
| 7 | `products/price-band-overview` | Price band summary | hottestBand, bestOpportunityBand, sampleOpportunityIndex |
| 8 | `products/price-band-detail` | Full 5-band distribution | priceBands[] with sales, brands, ratings per band |
| 9 | `products/brand-overview` | Brand concentration | sampleTop10BrandSalesRate (CR10), sampleBrandCount |
| 10 | `products/brand-detail` | Per-brand breakdown | brands[] with sales, revenue, sampleProducts |
| 11 | `products/history` | Time series (single ASIN per call) | timestamps[], price[], bsr[], monthlySalesFloor[], rating[], ratingCount[], sellerCount[], title/imageUrl/bestSeller/newRelease/aPlus/inventoryStatus changelogs |

## Known Quirks
- `topN`, `listingAge`, `newProductPeriod` are **strings** (`"10"` not `10`)
- Response `.data` is always an **array** — use `.data[0]`
- `ratingCount` not `reviewCount` everywhere
- `bsr` (int) in products vs `bestsellersRank` (array) in realtime
- `buyboxWinner.price` — NOT top-level `price` in realtime
- `realtime/product` does NOT return: monthlySalesFloor, fbaFee, sellerCount
- `reviewCountMin/Max` filters currently broken (API-56)
- `reviews/analysis` may 500 for certain ASINs (API-58) — retry different ASIN
- Rate limit: 100 req/min, 10 req/sec burst
- `categories` uses `categoryKeyword` (not `keyword`) and `parentCategoryPath` (not `parentCategoryName`)
- `reviews/analysis`: `mode` required ("asin"/"category"), use `asins` (plural array) not `asin`

## Field Differences Across Endpoints

| Data | markets | products/competitors | realtime | reviews | price-band | brand | history |
|------|---------|---------------------|----------|---------|------------|-------|---------|
| Sales | sampleAvgMonthlySales | monthlySalesFloor | ❌ | ❌ | sampleSalesRate | sampleGroupMonthlySales | monthlySalesFloor[] |
| Price | sampleAvgPrice | price | buyboxWinner.price | ❌ | bandMin/MaxPrice | sampleAvgPrice | price[] |
| BSR | sampleAvgBsr | bsr (int) | bestsellersRank[] | ❌ | ❌ | ❌ | bsr[] |
| Rating | sampleAvgRating | rating | rating | avgRating | sampleAvgRating | sampleAvgRating | rating[] |
| Reviews | sampleAvgReviewCount | ratingCount | ratingCount | reviewCount | ❌ | sampleAvgRatingCount | ratingCount[] |
| Insights | ❌ | ❌ | ❌ | ✅ consumerInsights | ❌ | ❌ | ❌ |
| Concentration | topSalesRate | ❌ | ❌ | ❌ | sampleTop3BrandSalesRate | CR10 | ❌ |
| Opportunity | ❌ | ❌ | ❌ | ❌ | sampleOpportunityIndex | ❌ | ❌ |

## Confidence Labels (all skills)
- 📊 **Data-backed** — direct API data
- 🔍 **Inferred** — logical reasoning from data
- 💡 **Directional** — suggestions, predictions

Strategy recommendations and subjective conclusions are NEVER 📊. Extreme growth (>200%) = 💡 only.

## Data Notes
- Sales (`monthlySalesFloor`) = lower-bound estimate
- Realtime = live; products/competitors = ~T+1 delay
- Amazon US only (amazon.com) — more marketplaces planned
- Each call consumes credits; check `meta.creditsConsumed`

## Links
- [apiclaw.io](https://apiclaw.io) · [API Docs](https://api.apiclaw.io/api-docs) · [GitHub](https://github.com/SerendipityOneInc/APIClaw-Skills) · support@apiclaw.io
