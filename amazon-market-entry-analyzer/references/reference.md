# Market Entry Analyzer — API Field Reference

> Load this file only when you need exact field names or response structure.

## Endpoints Used (11 of 11 — ALL)

| # | Endpoint | Purpose in This Skill | Step |
|---|----------|-----------------------|------|
| 1 | `categories` | Find category path for market search | Step 1a |
| 2 | `markets/search` | Market size, competition metrics, new product rate | Step 1b |
| 3 | `products/search` | Product supply (100+ via pagination), brand drill, price drill | Step 3, 4b, 7 |
| 4 | `products/competitors` | Top competitor list | Step 4a |
| 5 | `realtime/product` | Live detail for Top 5 competitors | Step 4c |
| 6 | `reviews/analysis` | Consumer pain points, buying factors | Step 6 |
| 7 | `products/price-band-overview` | Hottest & best opportunity price bands | Step 2a |
| 8 | `products/price-band-detail` | Per-band SKU/sales/brand/rating breakdown | Step 2b |
| 9 | `products/brand-overview` | Brand count, CR10, top brand avg price/rating | Step 1c |
| 10 | `products/brand-detail` | Per-brand SKU/sales/revenue/share ranking | Step 1d |
| 11 | `products/history` | 30-day price/BSR/sales trend for Top 3 | Step 5 |

Base URL: `https://api.apiclaw.io/openapi/v2`
Auth: `Bearer $APICLAW_API_KEY`
Method: All POST with JSON body
All endpoints return: `{success, data, error, meta}` with `meta.creditsRemaining`

---

## 1. categories

**Request:** (mutually exclusive modes)
- No params → root categories
- `categoryKeyword`: String → search by keyword
- `categoryPath`: List<String> → exact path
- `parentCategoryPath`: List<String> → child categories

**Response:**
| Field | Type | Used For |
|-------|------|----------|
| `categoryId` | string | Category ID |
| `categoryName` | string | Category name |
| `categoryPath` | list | Full path from root |
| `hasChildren` | bool | Has subcategories |
| `level` | int | Depth (1=root) |
| `productCount` | int | Products in category |

---

## 2. markets/search

**Key Request Params:**
- `categoryPath`: List<String> (e.g. `["Pet Supplies", "Dogs"]`)
- `categoryKeyword`: String
- `topN`: **String** (`"10"` not `10`)
- `sampleType`: `by_sale_100` / `by_bsr_100` / `avg`
- `pageSize`: Integer (max 20)

**Key Response Fields:**
| Field | Type | Used For |
|-------|------|----------|
| `totalSkuCount` | int | Market size |
| `sampleAvgMonthlySales` | float | Demand level |
| `sampleAvgMonthlyRevenue` | float | Market value |
| `sampleAvgPrice` | float | Price benchmark |
| `sampleAvgRating` | float | Quality benchmark |
| `sampleBrandCount` | int | Brand diversity |
| `sampleSellerCount` | int | Seller diversity |
| `sampleFbaRate` | float | FBA adoption (decimal) |
| `sampleNewSkuRate` | float | New entrant rate (decimal) |
| `topSalesRate` | float | Product concentration (CR_topN) |
| `topBrandSalesRate` | float | Brand concentration |
| `topSellerSalesRate` | float | Seller concentration |
| `sampleAPlusRate` | float | Margin benchmark |

---

## 3. products/search — Shared Product Object

**Key Request Params:**
- `keyword`, `categoryPath`, `mode` (14 presets), `keywordMatchType`
- Filter pairs: `monthlySalesMin/Max`, `priceMin/Max`, `ratingMin/Max`, etc.
- `pageSize` (max 20), `page`, `sortBy`, `sortOrder`
- `includeBrands`, `excludeBrands`

**Key Response Fields (per product):**
| Field | Type | Used For |
|-------|------|----------|
| `asin` | string | Product ID |
| `title` | string | Product name |
| `brandName` | string | Brand |
| `price` | float | Price |
| `monthlySalesFloor` | int | Monthly sales (lower bound) |
| `monthlyRevenueFloor` | float | Monthly revenue lower bound |
| `rating` | float | Rating (0-5) |
| `ratingCount` | int | Review count |
| `bsr` | int | BSR (NOT `bestsellersRank`) |
| `fbaFee` | float | FBA cost |
| `sellerCount` | int | Sellers on listing |
| `fulfillment` | string | FBA/FBM/AMZ |
| `listingDate` | string | When listed |
| `salesGrowthRate` | float | Growth rate |
| `variantCount` | int | Variants |

---

## 4. products/competitors

Same response as products/search. Different use: discovery by keyword/brand/asin.
Request params: `keyword`, `brand`, `asin`, `categoryPath`, `sortBy`, `pageSize`

---

## 5. realtime/product

**Request:**
- `asin`: String (required)
- `marketplace`: String (US/UK/DE/FR/IT/ES/JP/CA/AU/IN/MX/BR, default US)

**Response:**
| Field | Type | Used For |
|-------|------|----------|
| `asin` | string | Product ID |
| `title` | string | Full title |
| `brandName` | string | Brand |
| `rating` | float | Current rating |
| `ratingCount` | int | Current review count |
| `ratingBreakdown` | object | Star distribution {five_star: {percentage, count}, ...} |
| `features` | list | Bullet points |
| `description` | string | Product description |
| `specifications` | object | Tech specs |
| `variants` | list | All variants with dimensions |
| `bestsellersRank` | list | BSR info [{category, rank}, ...] |
| `buyboxWinner` | object | Buy Box: {price, fulfillment, seller} |
| `images` | list | All image URLs |

⚠️ Does NOT have: monthlySalesFloor, fbaFee, sellerCount

---

## 6. reviews/analysis

**Request:**
- `mode`: `"asin"` or `"category"`
- `asins`: List<String> (when mode=asin)
- `categoryPath`: String (when mode=category)
- `labelType`: filter to specific dimensions. **⚠️ Only ONE value per call — do NOT comma-separate multiple types.** Make separate calls for each labelType needed.
- `period`: e.g. `"1m"` / `"3m"` / `"6m"` / `"1y"` / `"2y"`

**labelType values (one per call):** `scenarios`, `issues`, `positives`, `improvements`, `buyingFactors`, `painPoints`, `keywords`, `userProfiles`, `usageTimes`, `usageLocations`, `behaviors`

**Response:**
| Field | Type | Used For |
|-------|------|----------|
| `reviewCount` | int | Sample size |
| `avgRating` | float | Overall satisfaction |
| `sentimentDistribution` | object | Positive/neutral/negative ratio |
| `consumerInsights` | list | Structured insights by dimension |
| `topKeywords` | list | Trending terms |

**InsightItem:** `{element, labelType, count, reviewRate, avgRating}`

---

## 7. products/price-band-overview

**Request:** Same params as products/search (keyword, category, filters)

**Response:**
| Field | Type | Used For |
|-------|------|----------|
| `sampleSkuCount` | int | Total products analyzed |
| `sampleMedianPrice` | float | Median price point |
| `hottestBand` | object | Highest sales share band |
| `bestOpportunityBand` | object | Highest opportunity index band |

**Band object:** `{bandIdx, bandLabel, sampleBandMinPrice, sampleBandMaxPrice, sampleSkuCount, sampleSalesRate, sampleBrandCount, sampleTop3BrandSalesRate, sampleAvgRating, sampleOpportunityIndex}`

---

## 8. products/price-band-detail

**Response:**
- `sampleSkuCount`, `sampleTotalMonthlySales`
- `priceBands`: array of 5 band objects (same structure as above)

---

## 9. products/brand-overview

**Response:**
| Field | Type | Used For |
|-------|------|----------|
| `sampleBrandCount` | int | Total brands |
| `sampleTop10BrandSalesRate` | float | CR10 concentration (top 10 brands) |
| `sampleTop10AvgRating` | float | Top 10 brand avg rating |
| `sampleTop10AvgPrice` | float | Top 10 brand avg price |

---

## 10. products/brand-detail

**Response:**
- `sampleSkuCount`, `sampleTotalMonthlySales`, `sampleBrandCount`
- `brands`: array of brand objects

**BrandStats:** `{brandName, sampleSkuCount, sampleGroupMonthlySales, sampleGroupMonthlyRevenue, sampleSalesRate, sampleAvgPrice, minPrice, maxPrice, sampleAvgRating, sampleAvgRatingCount, sampleProducts}`

**sampleProducts:** List of Product objects for this brand within the sample. Each product contains the full Shared Product Object fields (asin, title, price, bsr, monthlySalesFloor, rating, ratingCount, fulfillment, etc). This enables brand-level product matrix analysis without a separate products/search call.

---

## 11. products/history

**Request:**
- `asins`: List<String> (required)
- `startDate`: String "YYYY-MM-DD" (required)
- `endDate`: String "YYYY-MM-DD" (required)
⚠️ Does NOT accept `dateRange` — must use startDate + endDate

**Response (array of daily snapshots):**
| Field | Type | Used For |
|-------|------|----------|
| `asin` | string | Product ID |
| `price` | float | Price on that day |
| `bsr` | int | BSR on that day |
| `subBsr` | int | Sub-category BSR |
| `recentSales` | int | Recent sales count |
| `updatedAt` | string | Unix timestamp (string) |
| `createdAt` | string | Unix timestamp (string) |

---

## Cross-Validation Matrix

| Data Point | Primary Source | Validation Source |
|-----------|---------------|-------------------|
| Market size | markets/search | products/search (total count) |
| Brand concentration | brand-overview (sampleTop10BrandSalesRate) | markets/search (topBrandSalesRate) |
| Price distribution | price-band-detail | products/search (price field) |
| Competition level | markets (topSalesRate) | brand-detail (top brand shares) |
| Consumer demand | reviews/analysis | products (sales + growth) |
| Avg rating quality | markets (sampleAvgRating) | brand-overview (sampleTop10AvgRating) |
