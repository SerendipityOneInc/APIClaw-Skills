---
name: apiclaw
description: "APIClaw API platform overview — AI-powered commerce data infrastructure. Provides programmatic access to 200M+ Amazon products with real-time data across 6 endpoints: category browsing, market metrics, product search, competitor lookup, realtime ASIN detail, and AI review analysis. Use when user asks: what APIClaw can do, available API endpoints, how to get started, API capabilities overview, credit usage, or general commerce data questions. For deep Amazon product selection strategies and analysis workflows, use the Amazon-analysis-skill instead. Requires APICLAW_API_KEY."
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Commerce Data Infrastructure for AI Agents

> Real-time access to 200M+ Amazon products. 6 endpoints, one API key.
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
| 1 | `categories` | Browse Amazon category tree | categoryName, productCount, hasChildren |
| 2 | `markets/search` | Market-level aggregate metrics | avg sales, avg price, brand count, concentration, FBA rate |
| 3 | `products/search` | Product search with 14 preset strategies | ASIN, title, price, BSR, monthly sales, rating, reviews |
| 4 | `products/competitor-lookup` | Competitor analysis by keyword/ASIN | competitive products with sales, revenue, seller info |
| 5 | `realtime/product` | Live single-ASIN detail | price, BSR, reviews, features, variants, buy box |
| 6 | `reviews/analyze` | AI-powered review insights | sentiment, pain points, buying factors, user profiles |

## Endpoint Details

### 1. Categories
Browse or search Amazon's category hierarchy.
```
POST /openapi/v2/categories
{"keyword": "pet supplies"}         # search by keyword
{"parentCategoryName": "Pet Supplies"}  # browse children
```

### 2. Market
Category-level market metrics — answer "Is this market worth entering?"
```
POST /openapi/v2/markets/search
{"category": "Pet Supplies,Dogs,Toys", "topN": 10}
```
Returns: avg monthly sales, avg price, brand count, seller count, concentration ratios, new SKU rate, FBA rate.

### 3. Products
Product search with filters or 14 built-in selection modes.
```
POST /openapi/v2/products/search
{"keyword": "yoga mat", "mode": "beginner"}
```
**14 modes**: beginner, fast-movers, emerging, long-tail, underserved, new-release, fbm-friendly, low-price, single-variant, high-demand-low-barrier, broad-catalog, selective-catalog, speculative, top-bsr.

Monthly sales field: `atLeastMonthlySales` (lower-bound estimate).

### 4. Competitors
Competitor discovery by keyword, brand, or specific ASIN.
```
POST /openapi/v2/products/competitor-lookup
{"keyword": "wireless earbuds"}
{"asin": "B09V3KXJPB"}
```

### 5. Realtime Product
Live data for a single ASIN — current price, BSR, reviews, features, variants.
```
POST /openapi/v2/realtime/product
{"asin": "B09V3KXJPB"}
```
⚠️ Does NOT return monthly sales or profit margin. Use products/competitors for those.

### 6. Review Analysis
AI-powered consumer insights from customer reviews.
```
POST /openapi/v2/reviews/analyze
{"asin": "B09V3KXJPB"}
{"asins": ["B09V3KXJPB", "B08YYYYY"]}          # compare products
{"category": "Pet Supplies,Dogs,Toys", "period": "90d"}  # category-level
```
11 insight dimensions: painPoints, improvements, buyingFactors, issues, positives, scenarios, keywords, userProfiles, usageTimes, usageLocations, behaviors.

## What Each Endpoint Is Best For

| Need | Use This |
|------|----------|
| Sales & competition data | `products` / `competitors` |
| Live pricing, reviews, listing content | `realtime/product` |
| Category-level market sizing | `markets/search` |
| Consumer pain points & insights | `reviews/analyze` |
| Category browsing / validation | `categories` |

## Credits

- Each API call consumes credits
- Response includes `_credits.consumed` and `_credits.remaining`
- Plans & rates: [apiclaw.io/pricing](https://apiclaw.io/pricing)

## Data Notes

- **Monthly sales** (`atLeastMonthlySales`) is a lower-bound estimate — variance across tools is normal
- **Realtime vs database**: `realtime/product` is live; `products`/`competitors` have ~T+1 delay
- **Currently Amazon US only** (amazon.com) — more marketplaces planned

## Go Deeper

For advanced Amazon product research — 14 selection strategies, risk assessment, pricing analysis, listing optimization, and operational monitoring — install the dedicated skill:

```bash
clawhub install Amazon-analysis-skill
```

## Links

- **Website**: [apiclaw.io](https://apiclaw.io)
- **API Docs**: [api.apiclaw.io/api-docs](https://api.apiclaw.io/api-docs)
- **GitHub**: [github.com/SerendipityOneInc](https://github.com/SerendipityOneInc/Amazon-analysis-skill)
- **Support**: support@apiclaw.io
