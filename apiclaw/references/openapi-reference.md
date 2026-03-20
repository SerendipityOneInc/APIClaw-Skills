# APIClaw OpenAPI Quick Reference

> Load this only when you need exact field names, parameter types, or response structure.

Base URL: `https://api.apiclaw.io/openapi/v2`
Auth: `Authorization: Bearer $APICLAW_API_KEY`
All endpoints: POST with JSON body

---

## 1. categories

| Parameter | Type | Description |
|-----------|------|-------------|
| keyword | string | Search categories by keyword |
| parentCategoryName | string | Get child categories |

Response fields: `categoryName`, `categoryPath`, `productCount`, `hasChildren`

---

## 2. markets/search

| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Category path (comma or ` > ` separated) |
| topN | int | Top N for concentration metrics (default 10) |
| sampleType | string | Sample type |
| dateRange | string | Date range |
| sortBy | string | Sort field |
| sortOrder | string | asc / desc |

Key response fields: `sampleAvgMonthlySales`, `sampleAvgPrice`, `sampleAvgBsr`, `sampleAvgRating`, `sampleAvgReviewCount`, `sampleBrandCount`, `topSalesRate`, `topBrandSalesRate`, `sampleNewSkuRate`, `sampleFbaRate`, `sampleAvgMonthlyRevenue`

---

## 3. products/search

| Parameter | Type | Description |
|-----------|------|-------------|
| keyword | string | Search keyword |
| category | string | Category path |
| mode | string | Preset mode (14 options) |
| keywordMatchType | string | fuzzy / exact / phrase |
| salesMin / salesMax | int | Monthly sales range |
| priceMin / priceMax | float | Price range |
| reviewsMin / reviewsMax | int | Review count range |
| ratingMin / ratingMax | float | Rating range |
| bsrMin / bsrMax | int | BSR range |
| growthMin | float | Growth rate minimum |
| pageSize | int | Results per page |
| sortBy | string | Sort field |
| sortOrder | string | asc / desc |

Product fields: `asin`, `title`, `brand`, `price`, `bsrRank`, `atLeastMonthlySales`, `rating`, `ratingCount`, `variantCount`, `buyboxSeller`, `profitMargin`, `fbaFee`, `salesRevenue`, `sellerCount`

**14 modes**: beginner, fast-movers, emerging, long-tail, underserved, new-release, fbm-friendly, low-price, single-variant, high-demand-low-barrier, broad-catalog, selective-catalog, speculative, top-bsr

---

## 4. products/competitor-lookup

| Parameter | Type | Description |
|-----------|------|-------------|
| keyword | string | Search keyword |
| asin | string | Specific ASIN |
| brand | string | Brand name |
| pageSize | int | Results per page |

Returns same product fields as products/search.

---

## 5. realtime/product

| Parameter | Type | Description |
|-----------|------|-------------|
| asin | string | ASIN to look up |

Response fields: `title`, `brand`, `rating`, `ratingCount`, `ratingBreakdown`, `features` (array), `topReviews` (array), `specifications`, `variants` (array), `bestsellersRank` (array of {category, rank}), `buyboxWinner` ({price, seller, fulfillment})

⚠️ No: atLeastMonthlySales, profitMargin, fbaFee

---

## 6. reviews/analyze

| Parameter | Type | Description |
|-----------|------|-------------|
| asin | string | Single ASIN |
| asins | array | Multiple ASINs (comparison) |
| category | string | Category path (category-level analysis) |
| period | string | Time period (e.g. "90d") |
| labelType | string | Comma-separated dimensions to analyze |

Response fields: `totalReviews`, `avgRating`, `sentimentDistribution`, `ratingDistribution`, `consumerInsights` (keyed by labelType), `topKeywords`, `verifiedRatio`

11 labelType options: painPoints, improvements, buyingFactors, issues, positives, scenarios, keywords, userProfiles, usageTimes, usageLocations, behaviors

---

## Common Response Structure

All endpoints return:
```json
{
  "success": true,
  "data": [ ... ],
  "_query": { ... },
  "_credits": { "consumed": 1, "remaining": 499 }
}
```

`.data` is always an **array**. Use `.data[0]` for single results.
