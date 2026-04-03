# APIClaw API Quick Reference

> Concise field reference for all 11 endpoints. Load when you need exact parameter/field names.
>
> **OpenAPI Spec (live)**: https://apiclaw.io/api/v1/openapi-spec

Base URL: `https://api.apiclaw.io/openapi/v2`
Auth: `Bearer $APICLAW_API_KEY`
Method: All POST with JSON body

---

## 1. categories

| Parameter | Type | Note |
|-----------|------|------|
| categoryKeyword | String | Search by keyword |
| categoryPath | String | Exact path lookup |
| parentCategoryPath | List\<String\> | Browse children |
| _(no params)_ | — | Returns root categories |

Response: `categoryId`, `categoryName`, `categoryPath`, `hasChildren`, `isRoot`, `level`, `productCount`, `link`

---

## 2. markets/search

| Parameter | Type | Note |
|-----------|------|------|
| categoryPath | List\<String\> | e.g. `["Pet Supplies", "Dogs"]` |
| categoryKeyword | String | Keyword match across levels |
| topN | **String** | `"3"` / `"5"` / `"10"` / `"20"` ⚠️ must be string |
| newProductPeriod | **String** | `"1"` / `"3"` / `"6"` / `"12"` ⚠️ must be string |
| sampleType | String | `by_sale_100` / `by_bsr_100` / `avg` |
| dateRange | String | default `30d` |
| pageSize | Integer | default 20 |
| sortBy | String | default `sampleAvgMonthlySaleAmt` |
| sortOrder | String | `asc` / `desc` |

Key response fields: `sampleAvgMonthlySales`, `sampleAvgPrice`, `sampleAvgMonthlyRevenue`, `sampleBrandCount`, `sampleSellerCount`, `sampleFbaRate`, `sampleNewSkuRate`, `topSalesRate`, `topBrandSalesRate`, `topSellerSalesRate`, `totalSkuCount`

---

## 3. products/competitors

| Parameter | Type | Note |
|-----------|------|------|
| keyword | String | Search keyword |
| brand | String | Brand filter |
| seller | String | Seller filter |
| asin | String | ASIN filter |
| categoryPath | List\<String\> | Category filter |
| sortBy | String | `monthlySalesFloor` / `monthlyRevenueFloor` / `bsr` / `price` / `rating` / `ratingCount` / `listingDate` |
| sortOrder | String | `asc` / `desc` |
| pageSize | Integer | default 20 |

---

## 4. products/search

Same as competitors, plus:

| Parameter | Type | Note |
|-----------|------|------|
| mode | String | 14 preset modes (see SKILL.md) |
| keywordMatchType | String | `fuzzy` / `phrase` / `exact` |
| listingAge | **String** | Max age in days ⚠️ must be string |

Filter pairs (all optional, Min/Max): `monthlySales`, `revenue`, `salesGrowthRate`, `bsr`, `subBsr`, `bsrGrowthRate`, `price`, `rating`, `ratingCount`, `fbaShipping`, `variantCount`, `grossMargin`, `sellerCount`

Additional: `includeBrands`, `excludeBrands`, `fulfillment` (`["FBA"]`/`["FBM"]`), `badges` (`["New Release"]`/`["Best Seller"]`)

---

## 5. realtime/product

| Parameter | Required | Note |
|-----------|----------|------|
| asin | **Yes** | Product ASIN |
| marketplace | No | `US`/`UK`/`DE`/`FR`/`IT`/`ES`/`JP`/`CA`/`AU`/`IN`/`MX`/`BR` (default: US) |

Response fields: `asin`, `title`, `brand`, `rating`, `ratingCount`, `ratingBreakdown`, `features`, `description`, `specifications`, `categories`, `variants`, `bestsellersRank` (array), `buyboxWinner` (object with price), `images`, `dimensions`, `weight`

⚠️ Does NOT have: `monthlySalesFloor`, `fbaFee`, `sellerCount`

---

## 6. reviews/analysis

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| mode | String | **Yes** | `asin` or `category` |
| asins | List\<String\> | When mode=asin | ⚠️ plural, array format |
| categoryPath | String | When mode=category | Category path |
| labelType | String | No | Filter to dimension |
| period | String | No | e.g. `90d` |

labelType values: `scenarios`, `issues`, `positives`, `improvements`, `buyingFactors`, `painPoints`, `keywords`, `userProfiles`, `usageTimes`, `usageLocations`, `behaviors`

Response: `reviewCount`, `avgRating`, `verifiedRate`, `ratingDistribution`, `sentimentDistribution`, `consumerInsights` (list of InsightItem), `topKeywords`

InsightItem: `element`, `labelType`, `count`, `reviewRate`, `avgRating`

---

## 7. products/price-band-overview

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | **Yes** | Search keyword |

⚠️ Only accepts `keyword` — does NOT support `categoryPath`.

**Response (top-level):**

| Field | Type | Note |
|-------|------|------|
| sampleMedianPrice | Float | Median price across sampled products |
| hottestBand | BandObject | Band with highest sales rate |
| bestOpportunityBand | BandObject | Band with highest opportunity index |

**BandObject:**

| Field | Type | Note |
|-------|------|------|
| bandIdx | Integer | Band index (0-4) |
| bandLabel | String | e.g. "$10-$20" |
| sampleBandMinPrice | Float | Band minimum price |
| sampleBandMaxPrice | Float | Band maximum price |
| sampleSkuCount | Integer | Number of SKUs in this band |
| sampleSalesRate | Float | Share of total sales in this band |
| sampleBrandCount | Integer | Number of brands in this band |
| sampleTop3BrandSalesRate | Float | Top 3 brands' share within this band |
| sampleAvgRating | Float | Average rating in this band |
| sampleOpportunityIndex | Float | Composite opportunity score |

---

## 8. products/price-band-detail

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | **Yes** | Search keyword |

⚠️ Only accepts `keyword` — does NOT support `categoryPath`.

**Response:**

| Field | Type | Note |
|-------|------|------|
| sampleSkuCount | Integer | Total sampled SKUs |
| sampleTotalMonthlySales | Integer | Total monthly sales across all bands |
| priceBands | Array\<BandObject\> | Array of 5 band objects (same structure as §7) |

---

## 9. products/brand-overview

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | **Yes** | Search keyword |

⚠️ Only accepts `keyword` — does NOT support `categoryPath`.

**Response:**

| Field | Type | Note |
|-------|------|------|
| sampleBrandCount | Integer | Total number of brands found |
| sampleTop10BrandSalesRate | Float | CR10 — top 10 brands' share of total sales |
| sampleTop10AvgRating | Float | Average rating of top 10 brands |
| sampleTop10AvgPrice | Float | Average price of top 10 brands |

---

## 10. products/brand-detail

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | **Yes** | Search keyword |

⚠️ Only accepts `keyword` — does NOT support `categoryPath`.

**Response (top-level):**

| Field | Type | Note |
|-------|------|------|
| sampleSkuCount | Integer | Total sampled SKUs |
| sampleTotalMonthlySales | Integer | Total monthly sales |
| sampleBrandCount | Integer | Total brands found |
| brands | Array\<BrandObject\> | Per-brand breakdown |

**BrandObject:**

| Field | Type | Note |
|-------|------|------|
| brandName | String | Brand name |
| sampleSkuCount | Integer | SKUs for this brand |
| sampleGroupMonthlySales | Integer | Monthly unit sales |
| sampleGroupMonthlyRevenue | Float | Monthly revenue |
| sampleSalesRate | Float | Share of total sales |
| sampleAvgPrice | Float | Average price |
| minPrice | Float | Lowest price product |
| maxPrice | Float | Highest price product |
| sampleAvgRating | Float | Average rating |
| sampleAvgRatingCount | Integer | Average review count |
| sampleProducts | Array\<ProductObject\> | Sample products from this brand |

**ProductObject** (within sampleProducts): Same fields as Shared Product Object below.

---

## 11. products/history

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asins | List\<String\> | **Yes** | One or more ASINs |
| startDate | String | **Yes** | Start date `YYYY-MM-DD` |
| endDate | String | **Yes** | End date `YYYY-MM-DD` |

⚠️ Uses `startDate`/`endDate` — NOT `dateRange`. Date format is `YYYY-MM-DD`.

**Response:** Array of daily snapshot objects per ASIN.

| Field | Type | Note |
|-------|------|------|
| asin | String | Product ASIN |
| price | Float | Price on that date |
| bsr | Integer | BSR rank on that date |
| subBsr | Integer | Sub-category BSR rank |
| recentSales | Integer | Recent sales estimate |
| updatedAt | String | Timestamp of the snapshot |

---

## Shared Product Object (products/search, competitors & brand-detail sampleProducts)

| Field | Type | Note |
|-------|------|------|
| asin | String | |
| title | String | |
| brand | String | |
| price | Float | Top-level (unlike realtime) |
| bsr | Integer | BSR rank (NOT `bsr` or `bestsellersRank`) |
| monthlySalesFloor | Integer | Lower-bound monthly sales |
| monthlyRevenueFloor | Float | Monthly revenue lower bound |
| salesGrowthRate | Float | Growth rate |
| rating | Float | 0-5 |
| ratingCount | Integer | NOT `reviewCount` |
| fbaFee | Float | |
| sellerCount | Integer | |
| variantCount | Integer | |
| fulfillment | String | FBA/FBM/AMZ |
| listingDate | String | |
| buyBoxSellerName | String | |
