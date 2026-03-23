# APIClaw API Quick Reference

> Concise field reference for all 6 endpoints. Load when you need exact parameter/field names.
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

## 3. products/competitor-lookup

| Parameter | Type | Note |
|-----------|------|------|
| keyword | String | Search keyword |
| brand | String | Brand filter |
| seller | String | Seller filter |
| asin | String | ASIN filter |
| categoryPath | List\<String\> | Category filter |
| sortBy | String | `atLeastMonthlySales` / `atLeastMonthlyRevenue` / `bsr` / `price` / `rating` / `reviewCount` / `listingDate` |
| sortOrder | String | `asc` / `desc` |
| pageSize | Integer | default 20 |

---

## 4. products/search

Same as competitor-lookup, plus:

| Parameter | Type | Note |
|-----------|------|------|
| mode | String | 14 preset modes (see SKILL.md) |
| keywordMatchType | String | `fuzzy` / `phrase` / `exact` |
| listingAge | **String** | Max age in days ⚠️ must be string |

Filter pairs (all optional, Min/Max): `monthlySales`, `revenue`, `salesGrowthRate`, `bsr`, `subBsr`, `bsrGrowthRate`, `price`, `rating`, `reviewCount`, `fbaShipping`, `variantCount`, `grossMargin`, `sellerCount`

Additional: `includeBrands`, `excludeBrands`, `fulfillment` (`["FBA"]`/`["FBM"]`), `badges` (`["New Release"]`/`["Best Seller"]`)

---

## 5. realtime/product

| Parameter | Required | Note |
|-----------|----------|------|
| asin | **Yes** | Product ASIN |
| marketplace | No | `US`/`UK`/`DE`/`FR`/`IT`/`ES`/`JP`/`CA`/`AU`/`IN`/`MX`/`BR` (default: US) |

Response fields: `asin`, `title`, `brand`, `rating`, `ratingCount`, `ratingBreakdown`, `features`, `description`, `specifications`, `categories`, `variants`, `topReviews`, `bestsellersRank` (array), `buyboxWinner` (object with price), `images`, `dimensions`, `weight`

⚠️ Does NOT have: `atLeastMonthlySales`, `profitMargin`, `fbaFee`, `sellerCount`

---

## 6. reviews/analyze

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| mode | String | **Yes** | `asin` or `category` |
| asins | List\<String\> | When mode=asin | ⚠️ plural, array format |
| categoryPath | String | When mode=category | Category path |
| labelType | String | No | Filter to dimension |
| period | String | No | e.g. `90d` |

labelType values: `scenarios`, `issues`, `positives`, `improvements`, `buyingFactors`, `painPoints`, `keywords`, `userProfiles`, `usageTimes`, `usageLocations`, `behaviors`

Response: `totalReviews`, `avgRating`, `verifiedRatio`, `ratingDistribution`, `sentimentDistribution`, `consumerInsights` (list of InsightItem), `topKeywords`

InsightItem: `element`, `labelType`, `count`, `reviewPercentage`, `avgRating`

---

## Shared Product Object (products/search & competitor-lookup)

| Field | Type | Note |
|-------|------|------|
| asin | String | |
| title | String | |
| brand | String | |
| price | Float | Top-level (unlike realtime) |
| bsrRank | Integer | BSR rank (NOT `bsr` or `bestsellersRank`) |
| atLeastMonthlySales | Integer | Lower-bound monthly sales |
| salesRevenue | Float | Monthly revenue |
| salesGrowthRate | Float | Growth rate |
| rating | Float | 0-5 |
| ratingCount | Integer | NOT `reviewCount` |
| profitMargin | Float | |
| fbaFee | Float | |
| sellerCount | Integer | |
| variantCount | Integer | |
| fulfillment | String | FBA/FBM/AMZ |
| listingDate | String | |
| buyboxSeller | String | |
