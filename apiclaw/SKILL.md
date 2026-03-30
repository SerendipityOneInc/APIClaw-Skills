---
name: APIClaw — Commerce Data for AI Agents
version: 2.0.0
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
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Commerce Data Infrastructure for AI Agents

> Real-time access to 200M+ Amazon products. 11 endpoints, one API key.
>
> **Language rule**: Respond in the user's language.

## Quick Start

1. Get API key: [apiclaw.io/api-keys](https://apiclaw.io/api-keys)
2. Set env: `export APICLAW_API_KEY='hms_live_xxx'`
3. Base URL: `https://api.apiclaw.io/openapi/v2`
4. Auth: `Authorization: Bearer YOUR_API_KEY`
5. All endpoints: **POST** with JSON body

New keys need 3-5 seconds to activate. If 403, wait and retry.

## API Endpoints

| # | Endpoint | What It Does | Key Output |
|---|----------|-------------|------------|
| 1 | `categories` | Browse Amazon category tree | categoryName, categoryPath, productCount, hasChildren |
| 2 | `markets/search` | Market-level aggregate metrics | sampleAvgMonthlySales, sampleAvgPrice, sampleBrandCount, topSalesRate, sampleFbaRate |
| 3 | `products/search` | Product search with 14 preset strategies | asin, title, price, bsrRank, atLeastMonthlySales, rating, ratingCount |
| 4 | `products/competitor-lookup` | Competitor analysis by keyword/ASIN | competitive products with sales, revenue, seller info |
| 5 | `realtime/product` | Live single-ASIN detail | title, rating, features, variants, bestsellersRank, buyboxWinner |
| 6 | `reviews/analyze` | AI-powered review insights | sentimentDistribution, consumerInsights (painPoints, buyingFactors, etc.) |
| 7 | `products/price-band-overview` | Price band summary with best opportunity | sampleMedianPrice, hottestBand, bestOpportunityBand |
| 8 | `products/price-band-detail` | Full 5-band price distribution | priceBands (array of 5 band objects with sales, brands, ratings) |
| 9 | `products/brand-overview` | Top-brand concentration metrics | sampleBrandCount, sampleTop10BrandSalesRate (CR10), sampleTop10AvgRating |
| 10 | `products/brand-detail` | Per-brand breakdown with products | brands (array with sales, revenue, pricing, top products) |
| 11 | `products/product-history` | Historical daily snapshots for ASINs | daily price, bsrRank, subBsrRank, recentSales |

## Endpoint Details

### 1. Categories
Browse or search Amazon's category hierarchy.
```
POST /openapi/v2/categories
{"categoryKeyword": "pet supplies"}                    # search by keyword
{"parentCategoryPath": ["Pet Supplies"]}               # browse children
```
⚠️ Use `categoryKeyword` (not `keyword`) and `parentCategoryPath` (not `parentCategoryName`).

### 2. Markets
Category-level market metrics — answer "Is this market worth entering?"
```
POST /openapi/v2/markets/search
{"categoryPath": ["Pet Supplies", "Dogs", "Toys"], "topN": "10"}
```
⚠️ `topN` must be a **string** (`"3"`, `"5"`, `"10"`, `"20"`), NOT an integer.

Returns: sampleAvgMonthlySales, sampleAvgPrice, sampleBrandCount, sampleSellerCount, topSalesRate (concentration), sampleNewSkuRate, sampleFbaRate.

### 3. Products
Product search with filters or 14 built-in selection modes.
```
POST /openapi/v2/products/search
{"keyword": "yoga mat", "mode": "beginner"}
```
**14 modes**: beginner, fast-movers, emerging, long-tail, underserved, new-release, fbm-friendly, low-price, single-variant, high-demand-low-barrier, broad-catalog, selective-catalog, speculative, top-bsr.

Key fields: `atLeastMonthlySales` (lower-bound estimate), `bsrRank` (integer), `ratingCount` (not reviewCount), `price`, `profitMargin`, `fbaFee`.

### 4. Competitors
Competitor discovery by keyword, brand, or specific ASIN.
```
POST /openapi/v2/products/competitor-lookup
{"keyword": "wireless earbuds"}
{"asin": "B09V3KXJPB"}
```
Returns same product fields as `products/search`.

### 5. Realtime Product
Live data for a single ASIN — current listing content and pricing.
```
POST /openapi/v2/realtime/product
{"asin": "B09V3KXJPB"}
```

Key response fields:
| Field | Type | Note |
|-------|------|------|
| `title`, `brand` | String | Basic info |
| `rating`, `ratingCount` | Float/Int | Rating data |
| `ratingBreakdown` | Object | `{five_star: {percentage, count}, ...}` |
| `features` | List | Bullet points |
| `bestsellersRank` | Array | `[{category, rank}, ...]` — NOT a single integer |
| `buyboxWinner` | Object | `{price, fulfillment, seller}` — price is nested here |
| `topReviews` | List | Top reviews with title, body, rating |
| `variants` | List | All variants with dimensions |

⚠️ Does **NOT** return: `atLeastMonthlySales`, `profitMargin`, `fbaFee`, `sellerCount`. Use `products/competitor-lookup` for those.
⚠️ Price is nested: `buyboxWinner.price`, NOT top-level `price`.

### 6. Review Analysis
AI-powered consumer insights from customer reviews.
```
POST /openapi/v2/reviews/analyze

# Single or multiple ASINs (mode + asins required)
{"mode": "asin", "asins": ["B09V3KXJPB"]}
{"mode": "asin", "asins": ["B09V3KXJPB", "B08YYYYY"]}

# Category-level insights
{"mode": "category", "categoryPath": "Pet Supplies,Dogs,Toys", "period": "90d"}

# Filter to specific dimensions
{"mode": "asin", "asins": ["B09V3KXJPB"], "labelType": "painPoints"}
```

⚠️ `mode` is **required** (`"asin"` or `"category"`).
⚠️ Use `asins` (plural, array), NOT `asin` (singular string).

11 insight dimensions (labelType): `painPoints`, `improvements`, `buyingFactors`, `issues`, `positives`, `scenarios`, `keywords`, `userProfiles`, `usageTimes`, `usageLocations`, `behaviors`.

Returns: `totalReviews`, `avgRating`, `sentimentDistribution`, `ratingDistribution`, `consumerInsights`, `topKeywords`, `verifiedRatio`.

### 7. Price Band Overview
Quick summary of price distribution — find the hottest and best-opportunity price bands.
```
POST /openapi/v2/products/price-band-overview
{"keyword": "yoga mat"}
```

Returns: `sampleMedianPrice`, `hottestBand`, `bestOpportunityBand`.

Each band object contains: `bandIdx`, `bandLabel`, `sampleBandMinPrice`, `sampleBandMaxPrice`, `sampleSkuCount`, `sampleSalesRate`, `sampleBrandCount`, `sampleTop3BrandSalesRate`, `sampleAvgRating`, `sampleOpportunityIndex`.

⚠️ Only accepts `keyword` — does NOT support `categoryPath` filtering.

### 8. Price Band Detail
Full 5-band price distribution with per-band competition and sales data.
```
POST /openapi/v2/products/price-band-detail
{"keyword": "yoga mat"}
```

Returns: `sampleSkuCount`, `sampleTotalMonthlySales`, `priceBands` (array of 5 band objects).

Each band object has the same structure as Price Band Overview: `bandIdx`, `bandLabel`, `sampleBandMinPrice`, `sampleBandMaxPrice`, `sampleSkuCount`, `sampleSalesRate`, `sampleBrandCount`, `sampleTop3BrandSalesRate`, `sampleAvgRating`, `sampleOpportunityIndex`.

⚠️ Only accepts `keyword` — does NOT support `categoryPath` filtering.

### 9. Brand Overview
Top-brand concentration metrics — answer "How dominated is this market?"
```
POST /openapi/v2/products/brand-overview
{"keyword": "yoga mat"}
```

Returns: `sampleBrandCount`, `sampleTop10BrandSalesRate` (CR10 — top 10 brands' share of total sales), `sampleTop10AvgRating`, `sampleTop10AvgPrice`.

⚠️ Only accepts `keyword` — does NOT support `categoryPath` filtering.

### 10. Brand Detail
Per-brand breakdown with individual brand metrics and sample products.
```
POST /openapi/v2/products/brand-detail
{"keyword": "yoga mat"}
```

Returns: `sampleSkuCount`, `sampleTotalMonthlySales`, `sampleBrandCount`, `brands` (array).

Each brand object: `brandName`, `sampleSkuCount`, `sampleGroupMonthlySales`, `sampleGroupMonthlyRevenue`, `sampleSalesRate`, `sampleAvgPrice`, `minPrice`, `maxPrice`, `sampleAvgRating`, `sampleAvgRatingCount`, `sampleProducts` (array of Product objects).

⚠️ Only accepts `keyword` — does NOT support `categoryPath` filtering.

### 11. Product History
Historical daily snapshots for one or more ASINs over a date range.
```
POST /openapi/v2/products/product-history
{"asins": ["B09V3KXJPB"], "startDate": "2026-03-01", "endDate": "2026-03-30"}
```

⚠️ Uses `startDate`/`endDate` (NOT `dateRange`). Date format: `YYYY-MM-DD`.

Returns daily snapshots per ASIN: `asin`, `price`, `bsrRank`, `subBsrRank`, `recentSales`, `updatedAt`.

## ⚠️ Field Differences Across Endpoints

The endpoint types return **different fields**. Do NOT assume they share the same structure.

| Data | `markets` | `products`/`competitors` | `realtime/product` | `reviews/analyze` | `price-band-*` | `brand-*` | `product-history` |
|------|-----------|--------------------------|--------------------|--------------------|-----------------|-----------|-------------------|
| Monthly Sales | sampleAvgMonthlySales | ✅ atLeastMonthlySales | ❌ | ❌ | sampleSalesRate (per band) | sampleGroupMonthlySales | recentSales |
| Price | sampleAvgPrice | price | buyboxWinner.price | ❌ | sampleBandMinPrice/MaxPrice | sampleAvgPrice, minPrice, maxPrice | price |
| BSR | sampleAvgBsr | bsrRank (integer) | bestsellersRank (array) | ❌ | ❌ | ❌ | bsrRank, subBsrRank |
| Rating | sampleAvgRating | rating | rating | avgRating | sampleAvgRating (per band) | sampleAvgRating | ❌ |
| Review Count | sampleAvgReviewCount | ratingCount | ratingCount | totalReviews | ❌ | sampleAvgRatingCount | ❌ |
| Brand Count | sampleBrandCount | ❌ | ❌ | ❌ | sampleBrandCount (per band) | sampleBrandCount | ❌ |
| Sentiment | ❌ | ❌ | ❌ | ✅ sentimentDistribution | ❌ | ❌ | ❌ |
| Consumer Insights | ❌ | ❌ | ❌ | ✅ consumerInsights | ❌ | ❌ | ❌ |
| Pain Points | ❌ | ❌ | ❌ (manual from topReviews) | ✅ AI-analyzed | ❌ | ❌ | ❌ |
| Profit Margin | ❌ | profitMargin | ❌ | ❌ | ❌ | ❌ | ❌ |
| FBA Fee | ❌ | fbaFee | ❌ | ❌ | ❌ | ❌ | ❌ |
| Features/Bullets | ❌ | ❌ | ✅ features | ❌ | ❌ | ❌ | ❌ |
| Variants | ❌ | variantCount (integer) | variants (full list) | ❌ | ❌ | ❌ | ❌ |
| Opportunity Index | ❌ | ❌ | ❌ | ❌ | sampleOpportunityIndex | ❌ | ❌ |
| Brand Concentration | topSalesRate | ❌ | ❌ | ❌ | sampleTop3BrandSalesRate | sampleTop10BrandSalesRate (CR10) | ❌ |

## What Each Endpoint Is Best For

| Need | Use This |
|------|----------|
| Sales, pricing, competition data | `products/search` or `products/competitor-lookup` |
| Live pricing, reviews, listing content | `realtime/product` |
| Category-level market sizing | `markets/search` |
| Consumer pain points, sentiment, buying factors | `reviews/analyze` |
| Category browsing / validation | `categories` |
| Quick pricing strategy guidance | `products/price-band-overview` |
| Detailed price tier analysis & opportunity finding | `products/price-band-detail` |
| Market brand concentration / dominance check | `products/brand-overview` |
| Individual brand competitive breakdown | `products/brand-detail` |
| Price/BSR/sales trend over time | `products/product-history` |
| Full product picture | Combine `products` (quantitative) + `realtime` (qualitative) + `reviews` (insights) |

## Known Quirks

1. `topN` and `newProductPeriod` are **strings** — use `"10"` not `10`
2. `listingAge` is a **string** — use `"180"` not `180`
3. All response `.data` is an **array** — use `.data[0]` not `.data.fieldName`
4. `ratingCount` not `reviewCount` — the field is called `ratingCount` everywhere
5. `bsrRank` (integer) in products/competitors vs `bestsellersRank` (array) in realtime
6. Rate limit: 100 req/min, 10 req/sec burst
7. `reviewCountMin`/`reviewCountMax` filters are currently broken — API accepts them silently but does not apply filtering (API-56)
8. Keyword search uses broad fuzzy matching — results may include unrelated products. Use `categoryPath` parameter to filter when precision matters (API-57)
9. `reviews/analyze` may return HTTP 500 for certain ASINs due to serialization bug (API-58). Retry with different ASIN or use `realtime/product` topReviews as fallback.
10. Price-band and brand endpoints only accept `keyword` (not `categoryPath`) — cross-validate returned products' categories to filter noise.

## Credits

- Each API call consumes credits
- Response includes `meta.creditsConsumed` and `meta.creditsRemaining`
- Minimum 50 reviews required for `reviews/analyze` (returns `INSUFFICIENT_REVIEWS` error otherwise)
- Plans & rates: [apiclaw.io/pricing](https://apiclaw.io/pricing)

## Data Notes

- **Monthly sales** (`atLeastMonthlySales`) is a lower-bound estimate — actual may be higher
- **Realtime vs database**: `realtime/product` is live; `products`/`competitors` have ~T+1 delay
- **Currently Amazon US only** (amazon.com) — more marketplaces planned
- **Sales estimation fallback**: When `atLeastMonthlySales` is null → Monthly sales ≈ 300,000 / BSR^0.65

## ⚠️ Data Quality Advisory

- **Keyword search pollution**: Broad keyword matching may include unrelated products in results. For precise analysis, always use `categoryPath` from the `categories` endpoint to filter.
- **Aggregated endpoints hide noise**: `price-band` and `brand` endpoints return aggregated statistics. If the underlying keyword search includes irrelevant products, these aggregations will be silently polluted. Always validate with `categoryPath` when available.
- **Sales figures are estimates**: `atLeastMonthlySales` is a lower-bound estimate. Actual sales may be significantly higher.
- **Confidence labeling recommended**: When using APIClaw data for business decisions, distinguish between data-backed facts, reasonable inferences, and directional guesses.

## Go Deeper

For advanced Amazon product research — 14 selection strategies, risk assessment, pricing analysis, listing optimization, and operational monitoring — install the dedicated skill:

```bash
git clone https://github.com/SerendipityOneInc/APIClaw-Skills.git
# Point your agent to: APIClaw-Skills/amazon-analysis/SKILL.md
```

## Links

- **Website**: [apiclaw.io](https://apiclaw.io)
- **API Docs**: [api.apiclaw.io/api-docs](https://api.apiclaw.io/api-docs)
- **GitHub**: [github.com/SerendipityOneInc](https://github.com/SerendipityOneInc/APIClaw-Skills)
- **Support**: support@apiclaw.io
