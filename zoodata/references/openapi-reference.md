# ZooData API Quick Reference

> Concise field reference for the currently documented Amazon commerce and keyword-intelligence endpoints. Load when you need exact parameter/field names.
>
> **OpenAPI Spec (live)**: https://zoodata.ai/api/v1/openapi-spec

Base URL: `https://api.zoodata.ai/openapi/v2`
Auth: `Bearer $ZOODATA_API_KEY`
Method: All POST with JSON body

---

## 1. categories

| Parameter | Type | Note |
|-----------|------|------|
| categoryKeyword | String | Search by keyword |
| categoryPath | List\<String\> | Exact path lookup, e.g. `["Electronics", "Computers"]` |
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
| sampleType | String | `bySale100` / `byBsr100` / `avg` |
| dateRange | String | default `30d` |
| pageSize | Integer | default 20 |
| sortBy | String | default `sampleAvgMonthlySales` |
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
| keywordMatchType | String | `fuzzy` / `phrase` / `exact` |
| listingAge | **Enum String** | One of `30d` / `90d` / `180d` / `1y` / `2y` (⚠️ bare numbers like `180` → 422) |

Filter pairs (all optional, Min/Max): `monthlySales`, `revenue`, `salesGrowthRate`, `bsr`, `subBsr`, `bsrGrowthRate`, `price`, `rating`, `ratingCount`, `fbaShipping`, `variantCount`, `grossMargin`, `sellerCount`

> `mode` is **NOT** an API parameter. The 13 CLI presets in `zoodata.py` expand client-side into the filter pairs above before the request is sent; passing `mode` in a raw request returns 422.

Additional: `includeBrands`, `excludeBrands`, `fulfillment` (`["FBA"]`/`["FBM"]`/`["AMZ"]`), `badges` — enum values `["bestSeller"]` / `["amazonChoice"]` / `["newRelease"]` / `["aPlus"]` / `["video"]` (⚠️ `"New Release"` with a space → 422)

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
| period | String | No | e.g. `6m` |

⚠️ `labelType` is **not** an API request parameter. The API returns all 11 dimensions in one call. Filter by `labelType` client-side from the `consumerInsights` array.

Response: `reviewCount`, `avgRating`, `verifiedRate`, `ratingDistribution`, `sentimentDistribution`, `consumerInsights` (list of InsightItem), `topKeywords`

InsightItem: `element`, `labelType`, `count`, `reviewRate`, `avgRating`

labelType values (in response): `scenarios`, `issues`, `positives`, `improvements`, `buyingFactors`, `painPoints`, `keywords`, `userProfiles`, `usageTimes`, `usageLocations`, `behaviors`

---

## 6b. realtime/reviews

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | **Yes** | Product ASIN (10 chars) |
| marketplace | String | No | `US`/`UK` only (default: US) |
| cursor | String | No | Pagination token from previous response's `nextCursor`. Omit for first page. |

⚠️ No `pageSize` parameter — server returns 10 reviews/page fixed. Hard cap = **100 reviews / 10 pages**. Cost = **1 credit/page**.

Response: `asin`, `reviews` (array of RealtimeReview), `nextCursor` (null = no more pages).

RealtimeReview: `reviewId`, `title`, `body`, `bodyHtml`, `rating`, `author`, `date` (ISO 8601), `verifiedPurchase`, `vineProgram`, `helpfulVoteCount`, `unhelpfulVoteCount`, `reviewCountry`, `images`, `link`, `isGlobalReview`

Use cases:
- ASIN has <50 reviews so `/reviews/analysis` aggregation is empty
- Brand-new product with no daily snapshot
- Need fresh raw text for local LLM analysis (Map/Reduce → consumerInsights)

See `zoodata.py reviews-raw / review-tag-prompt / review-reduce-prompt / review-aggregate` for the local toolkit that consumes this endpoint.

---

## 6c. reviews/search

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | **Yes** | Product ASIN |
| ratingMin / ratingMax | Number | No | 1-5 inclusive |
| verifiedOnly | Boolean | No | Default false |
| vineOnly | Boolean | No | Default false |
| helpfulVoteCountMin | Integer | No | Filter low-engagement reviews |
| dateStart / dateEnd | Date (YYYY-MM-DD) | No | Inclusive range |
| sortBy | String | No | `recent` (default) / `rating` / `helpfulVoteCount` |
| sortOrder | String | No | `desc` (default) / `asc` |
| page | Integer | No | 1-indexed, default 1 |
| pageSize | Integer | No | 1-20, default 10 |

Response: array of TaggedReview with AI-generated `tags[{labelType, element}]` derived from the offline analysis pipeline (BigQuery daily snapshot).

TaggedReview vs RealtimeReview: `reviews/search` uses snapshot data with AI tags (T+1 delay); `realtime/reviews` is live raw text (no tags). Use `reviews/search` when daily snapshot exists and you want pre-tagged data; use `realtime/reviews` for fresh data or new products.

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
| asin | String | **Yes** | Single ASIN (one per call) |
| startDate | String | **Yes** | Start date `YYYY-MM-DD` |
| endDate | String | **Yes** | End date `YYYY-MM-DD` |
| marketplace | String | No | Marketplace code, default `US` |

⚠️ `asin` is a **single string** — NOT an array. For multiple ASINs, make separate calls.
⚠️ Does NOT support `page`/`pageSize` — returns full date range in one response.
⚠️ Uses `startDate`/`endDate` — NOT `dateRange`.

**Response:** Single time series object (NOT an array of snapshots).

| Field | Type | Note |
|-------|------|------|
| asin | String | Product ASIN |
| timestamps | List\<String\> | Dates (YYYY-MM-DD) |
| price | List\<Float\> | Price on each date |
| bsr | List\<Integer\> | BSR on each date |
| subBsr | List\<Integer\> | Sub-category BSR |
| monthlySalesFloor | List\<Integer\> | Monthly sales lower bound |
| rating | List\<Float\> | Rating on each date |
| ratingCount | List\<Integer\> | Review count on each date |
| sellerCount | List\<Integer\> | Seller count |
| title | List\<ChangeLog\> | Title changes `{date, value}` |
| imageUrl | List\<ChangeLog\> | Main image changes `{date, value}` |
| bestSeller | List\<ChangeLog\> | Best Seller badge `{date, value}` |
| amazonChoice | List\<ChangeLog\> | Amazon's Choice badge `{date, value}` |
| newRelease | List\<ChangeLog\> | New Release badge `{date, value}` |
| aPlus | List\<ChangeLog\> | A+ content status `{date, value}` |
| inventoryStatus | List\<ChangeLog\> | Stock status `{date, value}` |
| currency | String | e.g. `USD` |

---

## Keyword Intelligence Endpoints

This reference is a production endpoint whitelist; every listed endpoint must be deployed and callable through the standard production base URL.

Tool-surface note:
- API documentation and live endpoint availability do not guarantee that the current agent session exposes matching callable tools
- For skill execution, verify the live tool surface first; use this file for parameter and field confirmation after that

## 12. /openapi/v2/keywords/detail

Keyword value boundary for all keyword endpoints:
- The keyword endpoints expose estimated search, SERP visibility, rank, traffic-share, and impression-point signals.
- Keyword endpoints are keyword-query workflows; parameters named `keyword` or `query` expect Amazon search query / keyword phrases.
- For keyword endpoints that require `date` or `dateTo`, prefer T-1 or earlier and avoid the current date unless the user explicitly asks for today's lookup.
- These signals support directional screening and testing priority, but do not 100% prove a keyword's value for a specific ASIN.
- Seller-artifact acquisition, stage selection, field interpretation, and output policy are outside this endpoint contract and belong to the `amazon-keyword-traffic-analysis` skill.
- All eleven current keyword and product-traffic request schemas retain `granularity` for compatibility. Its only supported value is `week`, and their only supported marketplace is `US`; never send another value or legacy `lookbackDays`.
- For batch `keywords[]` on detail, market-profile, trend, trend-profile, and product-traffic-terms-trend, every value must already equal `LOWER(TRIM(value))`; uppercase letters, surrounding whitespace, and duplicates are rejected. The bundled CLI normalizes case and whitespace before sending.

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | Conditional | One keyword; exactly one of `keyword` / `keywords` |
| keywords | List\<String\> | Conditional | Batch of 1–20 keywords; preserves request order |
| date | String | **Yes** | Lookup date `YYYY-MM-DD`; prefer T-1 or earlier; resolves to the nearest available weekly snapshot at or before that date |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[]` for both single and batch requests.

Context fields include marketplace/site, requested/resolved date, weekly granularity, and `dataWindow.currentPeriod`.

Each item has `identity`, `status=ok|empty`, `snapshotData`, `emptyReason`, and nullable `errorCode` /
`errorMessage`. The latter are auxiliary fields, not status enums. `snapshotData` includes
`estimateSearchCount`, `abaRank`, Top3 click/conversion shares,
`marketCharacteristics`, `totalSkuCount`, SKU/brand/title coverage, organic/ad counts, and Top48 benchmarks.

Do not expect legacy `estimateSearchCountWeekly`, `totalSkuCnt`, or top-level `data:null`. An unmatched
keyword is an item with `status=empty` and an `emptyReason`.

---

## 12b. /openapi/v2/keywords/market-profile (metric layer)

Availability: standard production endpoint under the documented base URL. A subject-specific calculation failure can return HTTP 500 for the whole batch; treat that as runtime behavior, not an empty item.

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | Conditional | One keyword; exactly one of `keyword` / `keywords` |
| keywords | List\<String\> | Conditional | Batch of 1–20 keywords; preserves request order |
| date | String | **Yes** | Lookup date `YYYY-MM-DD`; resolves to the latest weekly snapshot on or before this date |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[]` for both single and batch requests.

Context fields: `marketplace`, `site`, `requestedDate`, `resolvedDate`, `granularity`, `dataWindow.currentPeriod`, and `scoringSpec` (`id`, `version`, `scoreType`, `scoreRange`, `referenceScope`).

Each item has `identity`, `status=ok|empty`, `marketProfile`, and `emptyReason`. `marketProfile` contains `marketCharacteristics`, `demandScale`, `top3Concentration`, `adActivity`, `top20OrganicEntryDifficulty`, `supplySaturation`, `brandStructure`, and `organicProductBenchmark`.

Use returned scores only with `context.scoringSpec`. Each scored dimension exposes `supported`, `level`, `interpretation`, `calculationStatus`, `unsupportedReason`, and `levelEvidence.score.{value,direction}`; evaluate it independently and treat any explicit unavailable signal as a conclusion boundary. `marketCharacteristics.volatility` exposes type and mapping-confidence evidence. `marketCharacteristics.annualSeasonality` separately exposes classification, year-over-year correlation, eligible-pair count, peak-pattern detection, and peak periods. Do not merge the two classifications or invent peak periods. This endpoint returns deterministic weekly snapshot evidence, not trend, root cause, recommendations, or seller-private ABA-SQP conversion data.

An unmatched keyword returns `status=empty`, `marketProfile=null`, descriptive `emptyReason` text, zero consumed credits, and may return null resolved context / scoring spec. A subject-specific calculation error can currently return HTTP 500 for the entire batch; treat that as a service failure rather than an empty item, and do not automatically fan out the batch. Use returned `meta.creditsConsumed` / `meta.creditsConsumedExact`.

Three-layer boundary: `keywords/detail` is the traceable data layer; `keywords/market-profile` is the stable deterministic metric layer; the Agent + skill layer combines evidence and produces confidence, explanations, limitations, and recommendations.

Metric-first rule: use `market-profile` before `detail` for supported market judgments. Do not descend merely because a metric dimension has incomplete calculation coverage; both are source-related, so the missing metric input will usually remain missing. Descend only when a named Agent inference requires raw fields omitted by the metric contract, the metric endpoint is unavailable, or the user requests source evidence.

Batch-first rule: once an endpoint is selected, prefer its batch form for all subjects sharing marketplace, date/range, window, filters, and sort context. Deduplicate while preserving order, chunk at 20, and use single calls only for one subject or incompatible contexts.

CLI: `zoodata.py keyword-market-profile --keywords "yoga mat,pilates mat" --date 2026-06-29 --marketplace US`

---

## 13. /openapi/v2/keywords/trend

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | Conditional | One keyword; exactly one of `keyword` / `keywords` |
| keywords | List\<String\> | Conditional | Batch of 1–20 keywords; preserves request order |
| dateFrom | String | **Yes** | Start date `YYYY-MM-DD` |
| dateTo | String | **Yes** | End date `YYYY-MM-DD`; prefer T-1 or earlier; maximum 93-day range |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[].series[]` for both single and batch requests.

Interpretation note:
- `keywords/trend` is a weekly time series. Align returned period boundaries before comparing it with SERP or ASIN observation endpoints; those interfaces are not interchangeable evidence even when all use `week`.

Each item has `identity`, `status=ok|empty`, `series[]`, `emptyReason`, and nullable `errorCode` /
`errorMessage`. The latter are auxiliary fields, not status enums. Series fields are
`periodStartDate`, `periodEndDate`, `estimateSearchCount`, `abaRank`,
`abaTop3ClickShareRate`, and `abaTop3ConversionShareRate`.

---

## 13b. /openapi/v2/keywords/trend-profile (metric layer)

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | Conditional | Exactly one of `keyword` / `keywords` |
| keywords | String[] | Conditional | 1–20, mutually exclusive with `keyword` |
| date | String | **Yes** | As-of date `YYYY-MM-DD` |
| windowPeriods | Integer[] | **Yes** | 1–4 unique values from `4`, `8`, `12`, `26` |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[].rows[]`. Each keyword has one row per requested window. Rows return `status=ok|empty`, `rowContext`, `emptyReason`, and `trendProfile`. `status=ok` profiles expose guarded `searchDemand` and `abaRank` dimensions. Their `trendEvidence` values include an explicit direction plus slope and consistency evidence, so do not infer the server label from endpoint movement alone. Preserve null empty reasons without inventing one.

Use this metric endpoint first for trend shape and volatility; call raw `keywords/trend` only when weekly points or omitted fields are required.

---

## 14. /openapi/v2/keywords/extends

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| query | String | **Yes** | Seed keyword |
| marketplace | String | No | Only `US` is supported; default `US` |
| page | Integer | No | default 1 |
| pageSize | Integer | No | default 20, max 100 |
| queryType | String | No | `phrase` / `fuzzy` (default `phrase`) |
| sortBy | String | No | `relevanceScore` / `estimateSearchCount` / `abaRank` / `keyword` |
| sortOrder | String | No | `asc` / `desc` |
| granularity | String | No | Compatibility field; only `week` is supported |

⚠️ Uses `query`, NOT `keyword`.
⚠️ No date is required; the service uses the latest available weekly snapshot. A legacy `date` may be sent but is ignored.
⚠️ Empty `data.rows[]` is a normal success case.

**Response:** `data.context + data.query + data.queryType + data.rows[]`.

Each row contains `matchData.{query,keyword,site,relevanceScore}` and `keywordSnapshot`.
`keywordSnapshot.dataWindow.currentPeriod` provides the resolved weekly period; its metric families match
the current `keywords/detail` snapshot contract.

Do not flatten the response back to legacy `term`, `seedKeyword`, or `estimateSearchCountWeekly` fields.

---

## 15. /openapi/v2/keywords/search-results

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| keyword | String | **Yes** | Keyword to inspect |
| date | String | **Yes** | Snapshot lookup date `YYYY-MM-DD`; prefer T-1 or earlier |
| marketplace | String | No | Only `US` is supported; default `US` |
| page | Integer | No | default 1 |
| pageSize | Integer | No | default 20, max 100 |
| exploreTypes | Array\<String\> | No | `ORG` / `SP` / `SB` / `SBV` / `SPR` |
| sortBy | String | No | `absolutePosition` / `estimateImpressionPoint` / `latestObservedAt` / `price` / `rating` / `ratingCount` / `recentSales` / `asin` / `title` |
| sortOrder | String | No | `asc` / `desc` |
| granularity | String | No | Compatibility field; only `week` is supported |

⚠️ Compatibility-retained `granularity` accepts only `week`; do not send legacy `lookbackDays`. Use the returned weekly period boundaries instead of inferring a rolling window.
⚠️ Use this endpoint as the primary source for "what products are currently showing on the keyword SERP/page 1" because it already returns listing-level product fields.
⚠️ Do not replace it with `products/search` when the question is about observed Amazon keyword SERP composition or ordering.
⚠️ When analyzing this endpoint, separate `exploreType` at least into `ORG` and sponsored placements instead of collapsing all rows together.

**Response:** `data.context + data.identity + data.rows[]`.

Key row fields: `latestObservedAt`, `exploreType`, `absolutePosition`, `pageIndex`, `pagePosition`, `asin`,
`title`, `brand`, `price`, `currency`, `link`, `imageLink`, `rating`, `ratingCount`, `recentSales`,
`hasVideo`, `estimateImpressionPoint`, `keywordTotalEstimateImpressionPoint`

Interpretation rule:
- `keywords/search-results` = observed keyword SERP snapshot
- It can answer page-1 product mix, brand mix, ad vs organic composition, and visible price band questions
- If you also use `products/search`, present it as a broader catalog supplement, not as the same thing

---

## 16. /openapi/v2/keywords/product-traffic-terms

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | **Yes** | Target ASIN |
| date | String | **Yes** | Snapshot lookup date `YYYY-MM-DD`; prefer T-1 or earlier |
| marketplace | String | No | Only `US` is supported; default `US` |
| page | Integer | No | default 1 |
| pageSize | Integer | No | default 20, max 100 |
| exploreTypes | Array\<String\> | No | `ORG` / `SP` / `SB` / `SBV` / `SPR` |
| keywordContains | String | No | Optional substring filter on returned keywords |
| keywordEstimateSearchCountMin | Integer | No | Minimum estimated keyword search count; at least 0 and no greater than the maximum |
| keywordEstimateSearchCountMax | Integer | No | Maximum estimated keyword search count; at least 0 and no less than the minimum |
| keywordAbaRankMin | Integer | No | Minimum numeric ABA rank; at least 1 and no greater than the maximum |
| keywordAbaRankMax | Integer | No | Maximum numeric ABA rank; at least 1 and no less than the minimum |
| sortBy | String | No | `trafficShare` / `estimateImpressionPoint` / `absolutePosition` / `avgPosition` / `keywordEstimateSearchCount` / `keywordAbaRank` / `latestObservedAt` / `keyword` |
| sortOrder | String | No | `asc` / `desc` |
| granularity | String | No | Compatibility field; only `week` is supported |

⚠️ The MCP `competitor-product-keywords` tool is retired and returns `tool_retired` with replacement
`openapi_v2_product_traffic_terms`. Use this route for any target ASIN, including a competitor.
⚠️ Compatibility-retained `granularity` accepts only `week`; do not send legacy `lookbackDays`; use the returned weekly period boundaries.
⚠️ In skill workflows, this endpoint is a reverse-ASIN source endpoint, not a substitute for `keywords/search-results` when the question is about visible page-1 product composition.

**Response:** `data.context + data.identity + data.rows[]`.

Key row fields: `latestObservedAt`, `exploreType`, `absolutePosition`, `pageIndex`, `pagePosition`, `asin`,
`keyword`, `estimateImpressionPoint`, `asinTotalEstimateImpressionPoint`, `avgPosition`,
`daysCoverageRate`, `observationCount`, `keywordEstimateSearchCount`, `keywordAbaRank`, and
`trafficShare`.

---

## 17. /openapi/v2/keywords/product-traffic-structure-profile

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | Conditional | One target ASIN; exactly one of `asin` / `asins` |
| asins | List\<String\> | Conditional | Batch of 1–20 target ASINs; exactly one of `asin` / `asins` |
| date | String | **Yes** | Lookup date `YYYY-MM-DD`; prefer T-1 or earlier |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[]`, preserving ASIN request order.

Observed context fields: `marketplace`, `requestedDate`, nullable `resolvedDate`, `granularity`, and
`dataWindow.{currentPeriod,previousPeriod}`.

Each item contains `identity.{asin,site}`, `status=ok|empty`, `emptyReason`, and nullable
`productTrafficTermsProfile`. An unavailable current period returns `status=empty`,
`emptyReason=current_period_unavailable`, and `productTrafficTermsProfile=null`; this is a coverage
result, not evidence of weak traffic.

Billing is per successfully returned ASIN item: each item with `status=ok` is billed once, while an
item with `status=empty` is not billed. Use the response's `meta.creditsConsumed` and
`meta.creditsConsumedExact` as the authoritative usage record rather than calculating credits from
the number of requested ASINs.

A non-null `productTrafficTermsProfile` has the following observed structure. Despite the retained
response field name, this endpoint is the current-vs-previous-week traffic-structure metric, not a
multi-week trend profile:

- `summary`
  - `currEstimateImpressionPoint`, `prevEstimateImpressionPoint`
  - `impressionPointChangeCount`, `impressionPointChangeRate`
  - `currTermCount`, `prevTermCount`, `termCountChange`, `termCountChangeRate`
  - `totalIncreaseImpressionPoint`, `totalDecreaseImpressionPoint`
- `trafficStructureChange`: keyed by each traffic type returned by the service. A live response
  returned `ORG`, `SP`, `SB`, and `SPR`; do not invent an absent channel. Each channel object has
  `currEstimateImpressionPoint`, `currAsinTrafficShare`, `prevEstimateImpressionPoint`,
  `prevAsinTrafficShare`, `impressionPointChangeCount`, `impressionPointChangeRate`,
  `currTermCount`, `prevTermCount`, `termCountChange`, and `termCountChangeRate`.
- `organicStructureChange`: `currTermCount`, `prevTermCount`, `termCountChange`,
  `termCountChangeRate`, `newTermCount`, `lostTermCount`, `newTerms[]`, and `lostTerms[]`.
- `termChangeDrivers`: `gainerCount`, `loserCount`, `top10Gainers[]`, and `top10Losers[]`.

For this profile's previous-period count, share, and impression-point fields, `null` means the
previous weekly data is unavailable. A numeric `0` means the previous weekly period exists but the
relevant signal was not observed. Do not coerce `null` to zero or zero to missing data. If
`dataWindow.previousPeriod` is null, empty
comparison arrays do not establish zero new/lost/gaining/losing terms. The live response used to
validate the container structure returned
empty arrays, so their item schema remains response-led: preserve fields from a non-empty response
and do not invent array-item fields.

Treat the object as a server-calculated metric. Preserve its returned modules, channel keys,
values, and period scope. Do not read retired flat overview fields or synthesize missing profile
modules client-side.

Retired routes are intentionally absent from the bundled CLI. Generic HTTP 410 behavior is owned by
`cli-contract.md`: preserve the migration response, do not retry, and do not infer a new CLI command
from `replacementPath`.

---

## 18. /openapi/v2/keywords/product-traffic-terms-trend

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | **Yes** | Target ASIN |
| keyword | String | Conditional | One exact keyword; exactly one of `keyword` / `keywords` |
| keywords | List\<String\> | Conditional | Batch of 1–20 exact keywords for the same ASIN |
| dateFrom | String | **Yes** | Start date `YYYY-MM-DD` |
| dateTo | String | **Yes** | End date `YYYY-MM-DD`; prefer T-1 or earlier; maximum 26-week range |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[].series[]` for both single and batch requests.

Each item has `identity`, `status=ok|empty`, `series[]`, `emptyReason`, and nullable `errorCode` /
`errorMessage`. The latter are auxiliary fields, not status enums. Each series point contains
`date` plus nested `asinSnapshot`, `traffic`, `placement`,
`keywordMetrics`, and `adActivity` groups.

Exposure-position fields under `placement` are nullable for both unavailable period data and no
observed position. A null position does not distinguish those states by itself; inspect returned
period boundaries and observation/coverage fields. Never convert a null position to numeric zero.

⚠️ `granularity` accepts only `week`; do not send legacy `lookbackDays`, `page`, `pageSize`, `sortBy`, or
`sortOrder`.

Diagnosis curves and events:
- Price curve: `asinSnapshot.latestPrice`
- BSR curve: `asinSnapshot.latestBsr`, `asinSnapshot.latestSubBsr`
- Sales curve: `asinSnapshot.latestMonthlySaleCount`
- Rating curve: `asinSnapshot.latestRating`, `asinSnapshot.latestRatingCount`
- Traffic-estimate curve: `traffic.*` plus `placement.avgOrganicObservation` / `placement.avgAdObservation`
- Keyword fields: use `keywordMetrics` only as supporting context for traffic-estimate changes
- Listing events: changes in `asinSnapshot.latestTitle` / `asinSnapshot.latestMainImageLink`

Key groups: product/listing/rank fields in `asinSnapshot`; ORG/SP/SB/SBV/SPR impression points in
`traffic`; positions/pages/observation timestamps in `placement`; `keywordEstimateSearchCount`,
`keywordAbaRank`, Top3 shares, and `metricWindow` in `keywordMetrics`; observation/campaign/ad
counts in `adActivity`.

---

## 19. /openapi/v2/keywords/product-traffic-trend

This is the ASIN-level raw weekly trend across all observed keywords. It has no keyword dimension;
use `product-traffic-terms-trend` for one ASIN plus one or more named keywords.

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | Conditional | One target ASIN; exactly one of `asin` / `asins` |
| asins | List\<String\> | Conditional | Batch of 1–20 target ASINs; exactly one of `asin` / `asins` |
| dateFrom | String | **Yes** | Start date `YYYY-MM-DD` |
| dateTo | String | **Yes** | End date `YYYY-MM-DD`; prefer T-1 or earlier; maximum 26-week range |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[].series[]`, preserving ASIN request order. Inspect each
item's `status=ok|empty` before reading `series`; missing weeks are not filled with zero.

Each weekly series point includes `periodStartDate`, `periodEndDate`,
`totalEstimateImpressionPoint`, `organicEstimateImpressionPoint`, `adEstimateImpressionPoint`,
`totalTermCount`, `organicTermCount`, `adTermCount`, `organicFirst3PagesTermCount`,
`trafficByExploreType[]`, `keywordDemandRankDistribution[]`, and
`organicAcquisitionRateDistribution[]`. Impression points are estimated traffic scores, not actual
impression counts. Null shares stay unavailable; do not calculate or fill them unless the user asks
for a transparent Agent-side calculation.

Billing is once per ASIN with `status=ok`; empty items are free. Use returned credit metadata.

---

## 20. /openapi/v2/keywords/product-traffic-trend-profile

This is the server-calculated ASIN-level four-week trend metric. Use `product-traffic-trend` when
raw weekly points are required and `product-traffic-structure-profile` for current-vs-previous-week
structure and driver evidence.

| Parameter | Type | Required | Note |
|-----------|------|----------|------|
| asin | String | Conditional | One target ASIN; exactly one of `asin` / `asins` |
| asins | List\<String\> | Conditional | Batch of 1–20 target ASINs; exactly one of `asin` / `asins` |
| date | String | **Yes** | As-of date `YYYY-MM-DD`; prefer T-1 or earlier |
| windowPeriods | Integer[] | No | Defaults to `[4]`; `[4]` is the only supported value |
| detailLevel | String | No | `summary` (default) or `full` |
| marketplace | String | No | Only `US` is supported; default `US` |
| granularity | String | No | Compatibility field; only `week` is supported |

Send `granularity=week` when specifying the compatibility field; the bundled CLI sends it explicitly.

**Response:** `data.context + data.items[].rows[]`, preserving ASIN request order. Read row
`status=ok|empty`, then each component's `supported`, `calculationStatus`, and
`unsupportedReason`. A successful row contains `trafficTrendProfile`; summary mode covers
`asinTotalTraffic`, `organicTraffic`, `adTraffic`, and `termCoverage`, while full mode may add
placement and distribution breakdowns. `detailLevel` changes response detail only, not query scope
or billing.

Each component returns the server's `trend`, `volatilityLevel`, `lastPeriodWindowPosition`, and
`trendEvidence`. Treat `trend` as the conclusion for the resolved four-week window, not as a
forecast or causal explanation. Share changes are absolute decimal differences (for example,
`0.05` means five percentage points); change rates are relative. Normalized-slope magnitudes are
not comparable across ASINs and are not percentage growth.

Billing is once per ASIN with at least one `status=ok` row; empty-only ASINs are free. Use returned
credit metadata.

---

## Shared Product Object (products/search, competitors & brand-detail sampleProducts)

Boundary note:
- `products/search` is a query against ZooData's product-database snapshot
- It is useful for broader catalog analysis such as market winners, sales distribution, price bands, and variant concentration
- It does NOT represent Amazon live keyword SERP ordering
- Do not describe `products/search` output as "Amazon search results" or "Amazon首页结果" unless you are explicitly talking about the ZooData product database rather than the observed Amazon keyword SERP

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
| categoryPath | List | Full category path root→leaf; always present — lets a keyword→category lookup resolve from the search row without a realtime call |
| bsrCategory | String | BSR category name (root); fallback when `categoryPath` is absent |
