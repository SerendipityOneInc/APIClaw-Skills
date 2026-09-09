---
name: zoodata
description: >
  API endpoint reference for ZooData's Amazon commerce and keyword-intelligence
  surfaces, including request/response schemas, parameter quirks, authentication,
  credit metadata, product-traffic structure and trend APIs, and the Local Review
  Toolkit.
  Use when the user asks about the API itself: which endpoints exist, how
  to call them (e.g. /products/search), field schemas returned by an
  endpoint, parameter quirks, how to authenticate, how credit consumption
  is reported, how to get started, or how the Local Review Toolkit works.
  Requires ZOODATA_API_KEY.
metadata:
  version: "1.3.0"
  author: SerendipityOneInc
  homepage: https://github.com/SerendipityOneInc/ZooData-Skills
  openclaw: {"requires": {"env": ["ZOODATA_API_KEY"]}, "primaryEnv": "ZOODATA_API_KEY"}
---

> **📋 Live API Reference**: Field names and parameters may change. For MCP calls, refresh and
> inspect the current ZooData MCP `inputSchema`; for direct HTTP calls, also consult the OpenAPI
> spec at https://zoodata.ai/api/v1/openapi-spec.
> Keyword compatibility field: all eleven current keyword and product-traffic request schemas
> retain `granularity`, but the only supported value is `week`. The bundled CLI always sends
> `granularity=week`. Never send `day`, `month`, `lately_day`, or legacy `lookbackDays`; use the
> weekly period boundaries returned by the service.

# ZooData — Commerce Data Infrastructure for AI Agents

200M+ Amazon products. 23 Amazon and keyword-intelligence endpoints. One API key.

## Quick Start
1. Get key: [zoodata.ai/api-keys](https://zoodata.ai/en/api-keys) (1,000 free credits)
2. `export ZOODATA_API_KEY='hms_live_xxx'`
3. Base URL: `https://api.zoodata.ai/openapi/v2` — all POST with JSON body
4. Auth: `Authorization: Bearer YOUR_API_KEY`
5. New keys need 3-5s to activate. If 403, wait and retry.

## Capabilities & Data Flow

- **Network**: only `https://api.zoodata.ai` (Bearer `ZOODATA_API_KEY`). Setting `ZOODATA_BASE_URL` to an untrusted host (anything other than `api.zoodata.ai` / `*.zoodata.ai` / localhost) makes the CLI **refuse the request and withhold the key** — the Bearer token is never sent to an untrusted host.
- **Execution**: bundled shared ZooData CLI `{skill_base_dir}/scripts/zoodata.py` (Python 3, stdlib-only). This data-layer reference skill allows the complete literal subcommand surface exposed by the bundled client's current top-level help.
- **Local files**: none by default; reads the optional credential store `~/.zoodata/config.json`; the Local Review Toolkit uses a private temporary working dir (created with `mktemp -d`, removed when the fallback completes) during the review fallback.
- **Sent to the API**: keywords, category paths, ASINs, marketplace/date and numeric filter values only. **Never sent**: budget, experience level, risk tolerance, or any other user-profile text — profile inputs map client-side to numeric filters.
- **Credits**: every API call consumes account credits. For broad or ambiguous requests, state the estimated credit cost and confirm with the user before running multi-call scans.

## Shared CLI contract

Before selecting or invoking a bundled CLI command, read and apply `references/cli-contract.md`; reapply it after every result. It is the local source of truth for invocation, command identity, execution-environment permission handling, composite reuse, exit-status handling, authoritative transport status, retries, terminal interface failures, and partial results.

### Local Interface Failure Output

For this API-reference skill, a terminal interface failure must produce one concise localized notice stating that the ZooData API lookup could not be completed, followed by the succeeded and failed endpoint identifiers. Do not continue into endpoint guidance, schema interpretation, or another API call. Do not expose control tokens or internal retry logs unless the user requests diagnostics.

## ⚠️ Critical API Pitfalls (ALL skills must follow)
1. **Commerce product/market search using a broad query** → resolve and lock `categoryPath` before interpreting category-sensitive product, market, competitor, brand, or price-band results. An explicitly labeled `products/search` category probe may run without a locked category only to resolve that category. Do **not** apply this rule to `/openapi/v2/keywords/*` Keyword Intelligence endpoints: their `keyword` / `query` inputs are Amazon search queries and do not require `categoryPath`.
2. **Brand/price-band queries MUST include --category** to avoid cross-category contamination
3. **Revenue** = `sampleAvgMonthlyRevenue` directly. **NEVER** calculate avgPrice × totalSales (overestimates 30-70%)
4. **Sales** = `monthlySalesFloor` (lower bound). Fallback: 300,000 / BSR^0.65, tag as 🔍
5. **Use API fields directly**: `sampleOpportunityIndex`, `sampleTop10BrandSalesRate` — never reinvent
6. **reviews/analysis** needs 50+ reviews. Fallback chain when sample is insufficient:
   1. Lightweight: `realtime/product` → `ratingBreakdown` (star distribution only, no themes)
   2. Full 11-dim insights: `realtime/reviews` (raw text, up to 100) + local Map/Reduce via the
      Local Review Toolkit below — see "Local Review Toolkit" section
7. **Aggregation endpoints** (price-band, brand) without categoryPath produce severely distorted data
8. **Price-band and brand endpoints only accept `keyword`** (not categoryPath) — cross-validate returned products
9. **`mode` is CLI-local, NOT an API parameter** → `zoodata.py` expands `--mode` client-side into the filter sets in `PRODUCT_MODES` (`{skill_base_dir}/scripts/zoodata.py`, 13 presets) before the request; sending `mode` raw → 422
10. **CLI filter flags ≠ API field names** → `--sales-min` → `monthlySalesMin`; `--ratings-max` (review count) → `ratingCountMax`, **not** `ratingMax` (a different valid field — max star rating — that returns wrong results silently, no 422). Pass `categoryPath` as a JSON array (`["Electronics"]`), never a string. Unknown fields (`salesMin`, `ratingsMax`, …) → 422

## On Missing Key (no credentials configured)

**BEFORE calling any endpoint**, verify credentials are configured. The reliable check is `python {skill_base_dir}/scripts/zoodata.py check` — credentials-only by default, no endpoint calls and no credit usage; exits non-zero if no key is found in env vars OR config files. A `[ -z "$ZOODATA_API_KEY" ]` test alone is NOT sufficient — a user may have only `~/.zoodata/config.json` set.

When no key is found through any mechanism:

1. **STOP.** Do not run the workflow. Do not call `zoodata.py` (you'll just get the same credential error and burn tokens).
2. **Do NOT fall back to a "partial analysis from training data" / "industry common-sense headlines" / "for reference only" preview.** Your training data is stale, has no per-ASIN granularity, and presenting it as analysis — even disclaimed — misrepresents what this skill produces. The deliverable is data-backed; without data, there is no deliverable.
3. **Tell the user, in their language**, all three of:
   - "`ZOODATA_API_KEY` is not set — I need this to run the analysis."
   - **Get a free key** (1,000 credits, no credit card): https://zoodata.ai/en/api-keys
   - **Configure** via one of:
     - `export ZOODATA_API_KEY='hms_live_xxx'` (session only)
     - `mkdir -p ~/.zoodata && chmod 700 ~/.zoodata && (umask 077; echo '{"api_key":"hms_live_xxx"}' > ~/.zoodata/config.json)` (persistent; keep the file private — 0600)
4. **Optionally** state in **one sentence** what the workflow will produce once the key is configured (deliverable shape only — no numbers, no market color, no "common sense" preview).

## On 401 Invalid Key

When `zoodata.py` returns a structured error with `_transport.status=401`, apply this route regardless of whether the preserved server `error` object contains `status` or uses the CLI fallback message:

1. **STOP further endpoint calls immediately.** Do not retry — a rejected key won't be accepted on a second try; every subsequent call will return 401 too.
2. **Keep the selected credential authoritative.** Do not inspect, compare, export, or switch to a lower-priority legacy credential after rejection. A legacy credential may be selected only when neither new source is configured; trying another endpoint or asking to continue does not change this precedence.
3. **Report to the user**:
   - The selected ZooData credential was rejected (likely invalid, revoked, or expired)
   - If any partial findings were collected before the failure, show them and mark as partial
   - Fix at https://zoodata.ai/en/api-keys (verify the key, regenerate if needed)
4. **Do not fabricate or guess** the data the failed calls would have returned. This includes "training-data fallback" / "industry common-sense" headlines disguised as preview — those are fabrications.

## On 402 Credit Exhausted

When `zoodata.py` returns a structured error with `_transport.status=402`, apply this route regardless of whether the preserved server `error` object contains `status` or uses the CLI fallback message:

1. **STOP further endpoint calls immediately.** Do not retry. Do not switch endpoints as a workaround — 402 is account-level (key/subscription), not endpoint-level.
2. **Report to the user** with all four of:
   - Which step in the workflow was reached (e.g. "Completed step 3/5: brand analysis")
   - Partial findings already collected (show the actual data, not just a list of completed steps)
   - Returned credit metadata when available; if it is absent, say it was not returned rather than estimating it
   - Top-up link: https://zoodata.ai/en/pricing
3. **Do not fabricate or guess** the missing data to "complete" the report. Mark partial findings explicitly as partial. **No "training-data fallback" / "industry common-sense" filler** — substituting public-knowledge prose for missing endpoint data is still fabrication.

## On 422 Validation Error

For every parsed HTTP response from `zoodata.py`, treat `_transport.status` as the authoritative outer status; response-body and nested status-like fields do not override it. When the CLI returns HTTP 422 / `VALIDATION_ERROR`, read the preserved structured server error on stdout, including its message/details and `_query.params`. Do not retry the unchanged request. Correct the named fields first; the CLI exits non-zero while preserving the server error fields for the calling agent. Current keyword requests retain `granularity` for compatibility but accept only `week`; legacy `lookbackDays` remains unsupported.

## 23 Amazon and Keyword Endpoints

| # | Endpoint | Purpose | Key Output |
|---|----------|---------|------------|
| 1 | `categories` | Browse/search category tree | categoryPath, productCount |
| 2 | `markets/search` | Market-level metrics | sampleAvgMonthlySales, sampleAvgPrice, topSalesRate, sampleNewSkuRate |
| 3 | `products/search` | Product search (20+ filter fields) | asin, price, monthlySalesFloor, rating, ratingCount, fbaFee |
| 4 | `products/competitors` | Competitor discovery | same fields as products/search |
| 5 | `realtime/product` | Live ASIN detail | rating, features, bestsellersRank[], buyboxWinner.price, variants |
| 6 | `reviews/analysis` | AI review insights (11 dims) | sentimentDistribution, consumerInsights, topKeywords |
| 7 | `realtime/reviews` | Live raw review text (cursor paginated, max 100) | reviews[], nextCursor — feeds Local Review Toolkit |
| 8 | `products/price-band-overview` | Price band summary | hottestBand, bestOpportunityBand, sampleOpportunityIndex |
| 9 | `products/price-band-detail` | Full 5-band distribution | priceBands[] with sales, brands, ratings per band |
| 10 | `products/brand-overview` | Brand concentration | sampleTop10BrandSalesRate (CR10), sampleBrandCount |
| 11 | `products/brand-detail` | Per-brand breakdown | brands[] with sales, revenue, sampleProducts |
| 12 | `products/history` | Time series (single ASIN per call) | timestamps[], price[], bsr[], monthlySalesFloor[], rating[], ratingCount[], sellerCount[], title/imageUrl/bestSeller/newRelease/aPlus/inventoryStatus changelogs |
| 13 | `/openapi/v2/keywords/detail` | Keyword summary from the nearest available weekly snapshot | `data.context + data.items[].snapshotData` with `estimateSearchCount`, `abaRank`, market/SKU/ad fields |
| 14 | `/openapi/v2/keywords/market-profile` | Multidimensional weekly keyword profile | demand scale, Top3 concentration, ad activity, organic-entry difficulty, saturation, brand structure, organic benchmark, coverage |
| 15 | `/openapi/v2/keywords/trend` | Weekly keyword time series | `data.context + data.items[].series[]` with search count, ABA rank, Top3 shares, period bounds |
| 16 | `/openapi/v2/keywords/trend-profile` | Server-calculated trend profile over fixed weekly windows | trend shape, volatility, normalized slope, direction consistency, ABA-rank evidence |
| 17 | `/openapi/v2/keywords/extends` | Keyword expansion / long-tail discovery | `data.context + data.rows[].{matchData,keywordSnapshot}`; may return empty `rows[]` |
| 18 | `/openapi/v2/keywords/search-results` | Weekly keyword SERP snapshot | `data.context + data.identity + data.rows[]` with placement, product, and impression fields |
| 19 | `/openapi/v2/keywords/product-traffic-terms` | Traffic-driving keywords for any target ASIN, including a competitor | `data.context + data.identity + data.rows[]` with keyword, position, demand, ABA rank, and traffic share |
| 20 | `/openapi/v2/keywords/product-traffic-structure-profile` | Current-vs-previous-week ASIN traffic structure and change drivers | `data.context + data.items[].productTrafficTermsProfile` for one ASIN or a batch of up to 20 |
| 21 | `/openapi/v2/keywords/product-traffic-terms-trend` | Per-keyword weekly traffic trend for one ASIN | `data.context + data.items[].series[]` with nested ASIN, traffic, placement, keyword, and ad groups |
| 22 | `/openapi/v2/keywords/product-traffic-trend` | ASIN-level weekly raw traffic across all keywords | `data.context + data.items[].series[]` with total/organic/ad traffic and term coverage |
| 23 | `/openapi/v2/keywords/product-traffic-trend-profile` | Server-calculated four-week ASIN traffic conclusions | `data.context + data.items[].rows[].trafficTrendProfile` |

## Known Quirks
- `topN`, `listingAge`, `newProductPeriod` are **strings** (`"10"` not `10`)
- Many search/list endpoints return `.data` as an **array** — use `.data[0]` for the first record. But some commands may return non-array payloads inside `data`, so inspect the actual response shape before indexing.
- `ratingCount` not `reviewCount` everywhere
- `bsr` (int) in products vs `bestsellersRank` (array) in realtime
- `buyboxWinner.price` — NOT top-level `price` in realtime
- `realtime/product` does NOT return: monthlySalesFloor, fbaFee, sellerCount
- `realtime/product` cold-start: first call for an uncached ASIN may return `success: true` with an EMPTY `data` (`asin: ""`) while the live fetch warms up — retry once after a few seconds before concluding "no data" (still billed 1 credit per call)
- `reviewCountMin/Max` filters currently broken (API-56)
- `reviews/analysis` may 500 for certain ASINs (API-58) — retry different ASIN
- Rate limit: 100 req/min, 10 req/sec burst
- `categories` uses `categoryKeyword` (not `keyword`) and `parentCategoryPath` (not `parentCategoryName`)
- `reviews/analysis`: `mode` required ("asin"/"category"), use `asins` (plural array) not `asin`
- `realtime/reviews`: returns 10 reviews/page fixed (no `pageSize` param); 1 credit/page; cursor-paginated; hard cap = 100 reviews (10 pages); supports `marketplace` US/UK only
- `keywords/detail` accepts exactly one of `keyword` / `keywords[]` (max 20), resolves `date` to the nearest available weekly snapshot, and returns input-ordered `data.items[]`; an unmatched item has `status=empty`, not top-level `data: null`
- `keywords/market-profile` accepts one of `keyword` / `keywords[]` (max 20), requires `date`, supports weekly granularity only, and returns input-ordered `data.items[]` with `status=ok|empty`. `emptyReason` is descriptive no-result text, not an enum. A subject-specific calculation failure can return HTTP 500 for the whole batch.
- `keywords/trend-profile` accepts one of `keyword` / `keywords[]` (max 20), requires `date` and 1–4 unique `windowPeriods` selected from 4/8/12/26, and supports weekly granularity only.
- `keywords/extends` requires `query` (not `keyword`), uses the latest available weekly snapshot, supports `queryType` = `phrase` or `fuzzy`, and may legitimately return empty `data.rows[]`; legacy `date` is optional and ignored
- All eleven current keyword and product-traffic request schemas retain `granularity` for compatibility and accept only `week`; all currently support only marketplace `US`. The bundled CLI sends both values explicitly. Never send another granularity or legacy `lookbackDays`. Use returned weekly period boundaries instead of inferring a rolling window.
- Batch keyword fields on `detail`, `market-profile`, `trend`, `trend-profile`, and `product-traffic-terms-trend` must already equal `LOWER(TRIM(value))`; the bundled CLI normalizes them. Single-keyword fields accept surrounding whitespace and letter case where the endpoint schema says so.
- Keyword endpoints are keyword-query workflows; for inputs named `keyword` or `query`, use the Amazon search query / keyword phrase being analyzed
- For keyword endpoints that require `date` or `dateTo`, prefer T-1 or earlier and avoid the current date unless the user explicitly asks for today's lookup
- `keywords/search-results` requires `date` + `keyword`; `exploreTypes` values are `ORG`, `SP`, `SB`, `SBV`, `SPR`
- Competitor traffic-term lookup is consolidated into `keywords/product-traffic-terms`; route retired-interface behavior and the exact request contract to `references/openapi-reference.md § 16`.
- `keywords/product-traffic-structure-profile` compares the resolved current week with the previous week; it is not a multi-week trend. See `references/openapi-reference.md § 17` for its exact contract.
- `keywords/product-traffic-terms-trend` requires `asin` + exactly one of `keyword` / `keywords[]` + `dateFrom` + `dateTo`; the date range cannot exceed 26 weeks and the series request has no pagination or sort parameters.
- `keywords/product-traffic-trend` is ASIN-level across all keywords and has no keyword dimension; use `product-traffic-terms-trend` for an ASIN × keyword series.
- `keywords/product-traffic-trend-profile` provides the server-calculated ASIN-wide trend profile; route exact window, detail, and billing questions to `references/openapi-reference.md § 20`.
- `keywords/search-results` is the default source for explaining what products currently appear on a keyword SERP because it already returns listing-level product fields
- `products/search` is a broader ZooData product-database query and must not be presented as Amazon live keyword SERP ordering

## Keyword Intelligence Endpoints

These eleven endpoints fill the gap between raw
catalog data and search-demand/search-visibility intelligence.

Keyword value boundary:
- Keyword endpoints provide estimated search, visibility, rank, traffic-share, and impression-point signals
- They do not provide a seller's first-party ABA Search Query Performance funnel by themselves
- Treat keyword value, profitability, and conversion potential as directional unless the user supplies ABA-SQP impressions, clicks, cart adds, purchases, click share, purchase share, and conversion rate
- Seller-artifact acquisition, stage selection, field interpretation, and user-facing output policy belong to the `amazon-keyword-traffic-analysis` skill. This API reference does not prescribe a blanket caveat or one seller view for every subject.

### `/openapi/v2/keywords/detail`
- Input: exactly one of `keyword` / `keywords[]` (1–20), required `date`, optional `marketplace`; compatibility-retained `granularity` supports only `week`
- Data window: resolves the requested `date` to the nearest available weekly snapshot at or before that date
- Date rule: prefer T-1 or earlier for `date`; avoid current-date lookup unless explicitly requested
- Response shape: `data.context + data.items[]`, preserving request order
- Item fields: `identity`, `status=ok|empty`, `snapshotData`, `emptyReason`, nullable `errorCode`, nullable `errorMessage`
- `snapshotData` fields include `estimateSearchCount`, `abaRank`, Top3 click/conversion shares,
  `marketCharacteristics`, `totalSkuCount`, SKU/brand/title coverage, organic/ad counts, and Top48 benchmarks
- Do not read legacy `estimateSearchCountWeekly`, `totalSkuCnt`, or top-level `data:null`

### `/openapi/v2/keywords/market-profile` (metric layer)
- Availability: standard production endpoint under the documented base URL
- Input: exactly one of `keyword` or `keywords[]` (1–20), required `date`, optional `marketplace`; compatibility-retained `granularity` supports only `week`
- Response shape: `data.context + data.items[]`, preserving request order
- Context fields: `requestedDate`, `resolvedDate`, `dataWindow.currentPeriod`, `scoringSpec`, marketplace/site/granularity
- Item fields: `identity`, `status=ok|empty`, `marketProfile`, `emptyReason`
- `marketProfile` dimensions: `marketCharacteristics`, `demandScale`, `top3Concentration`, `adActivity`, `top20OrganicEntryDifficulty`, `supplySaturation`, `brandStructure`, `organicProductBenchmark`
- Interpret scores only with `context.scoringSpec` (`id`, `version`, `scoreType`, `scoreRange`, `referenceScope`). Scored dimensions expose `supported`, `calculationStatus`, `unsupportedReason`, `level`, `interpretation`, and `levelEvidence.score.{value,direction}`. There is no aggregate coverage object.
- `marketCharacteristics.volatility` and `marketCharacteristics.annualSeasonality` are independent evidence objects. Do not collapse their classifications, let one override the other, or invent peak periods from an empty list.
- Unmatched keywords return `status=empty`, `marketProfile=null`, and a descriptive `emptyReason`; resolved context and `scoringSpec` may be null
- A subject-specific calculation failure can currently produce HTTP 500 for the whole batch. Treat it as a service failure, not an item-level `empty` result; do not automatically fan out all subjects into single calls.
- Three-layer boundary: use data-layer `keywords/detail` for source snapshot fields, metric-layer `keywords/market-profile` for stable deterministic profile objects, and the Agent + skill layer for evidence composition, confidence, explanations, limitations, and actions
- Metric-first access: call the matching metric before its source data endpoint. Descend only when the Agent needs an indicator or evidence grain omitted by the metric contract, the metric endpoint is unavailable and transparent data-based calculation is valid, no metric exists, or raw evidence is explicitly requested. Incomplete metric calculation coverage is a conclusion limit—not by itself a reason to call same-source data.
- Batch-first execution: after selecting the endpoint, collect all subjects with identical non-subject context and prefer its batch contract over repeated single calls. Deduplicate case-insensitively, preserve order, chunk compatible sets at the endpoint limit (20 for current keyword batches), and merge results back into global input order. Batch support never justifies an extra cross-layer call.

### `/openapi/v2/keywords/trend`
- Input: exactly one of `keyword` / `keywords[]` (1–20), required `dateFrom` / `dateTo`, optional `marketplace`; compatibility-retained `granularity` supports only `week`; maximum 93-day range
- Data window: weekly-granularity points across the requested date range
- Date rule: prefer T-1 or earlier for `dateTo`; avoid current-date lookup unless explicitly requested
- Response shape: `data.context + data.items[].series[]`, preserving request order
- Item fields: `identity`, `status=ok|empty`, `series[]`, `emptyReason`, nullable `errorCode`, nullable `errorMessage`
- Series fields: `periodStartDate`, `periodEndDate`, `estimateSearchCount`, `abaRank`,
  `abaTop3ClickShareRate`, `abaTop3ConversionShareRate`

### `/openapi/v2/keywords/trend-profile` (metric layer)
- Input: exactly one of `keyword` / `keywords[]` (1–20), required `date`, required unique `windowPeriods[]` selected from 4/8/12/26, optional `marketplace`; compatibility-retained `granularity` supports only `week`
- Response: `data.context + data.items[].rows[]`; every requested window returns one row with `rowContext`, `status=ok|empty`, `emptyReason`, and `trendProfile`
- Available profiles contain independently guarded `searchDemand` and `abaRank` dimensions with `trend`, `trendPattern`, and `{value,direction}` entries under `trendEvidence`
- Evidence includes first/last/change values, normalized slope, direction consistency, aligned/eligible period counts, plus demand volatility/window position or ABA best/worst rank
- Use this metric endpoint before raw `keywords/trend` for trend-shape and volatility judgments. Descend only for required weekly points or fields omitted from the profile.
- Preserve null empty reasons rather than inventing one. Billing is per keyword with at least one `status=ok` window; use returned credit metadata.

### `/openapi/v2/keywords/extends`
- Input: required `query`; optional `marketplace`, `page`, `pageSize`, `queryType`, `sortBy`, `sortOrder`; compatibility-retained `granularity` supports only `week`; no date is required
- Important quirk: seed field is `query`, not `keyword`; `queryType` supports `phrase` and `fuzzy`
- Data window: latest available weekly snapshot; a legacy `date` may be sent but is ignored
- Response shape: `data.context + data.query + data.queryType + data.rows[]`
- Row fields: `matchData.{query,keyword,site,relevanceScore}` and `keywordSnapshot`, whose
  `dataWindow.currentPeriod` and snapshot metrics use the same current field families as `keywords/detail`
- Do not flatten rows to legacy `term`, `seedKeyword`, or `estimateSearchCountWeekly`; empty `rows[]` is normal

### `/openapi/v2/keywords/search-results`
- Input: required `keyword` / `date`; optional `marketplace`, `page`, `pageSize`, `exploreTypes`, `sortBy`, `sortOrder`
- Compatibility-retained `granularity` supports only `week`; do not send legacy `lookbackDays`
- Data window: latest available weekly period at or before the requested date; use the returned period boundaries
- Date rule: prefer T-1 or earlier for `date`; avoid current-date lookup unless explicitly requested
- Response shape: `data.context + data.identity + data.rows[]`
- Row fields include `latestObservedAt`, `exploreType`, `absolutePosition`, `pageIndex`,
  `pagePosition`, `asin`, `title`, `brand`, `price`, `currency`, `link`, `imageLink`, `rating`,
  `ratingCount`, `recentSales`, `hasVideo`, `estimateImpressionPoint`,
  `keywordTotalEstimateImpressionPoint`
- Interpretation rule: use this endpoint first for "what is on page 1 / what products dominate this keyword / what does the SERP look like"
- Do not substitute `products/search` when the question is about observed keyword SERP composition or ordering

### `/openapi/v2/keywords/product-traffic-terms`
- Provides traffic-driving keyword rows for any target ASIN, including competitor research; the former competitor-specific lookup is consolidated into this route.
- Read `references/openapi-reference.md § 16` for the request, response, field, date, filtering, pagination, retirement, and billing contract.
- Apply `references/cli-contract.md` to every result.

### `/openapi/v2/keywords/product-traffic-structure-profile`
- Production supports one ASIN or a batch of up to 20 ASINs, retains `granularity` with `week` as its only supported value, and compares the resolved current week with the previous week.
- Read `references/openapi-reference.md § 17` for the request, response, status, field, date, batching, and billing contract.
- Apply `references/cli-contract.md` to every result, including a server-provided endpoint migration response.

### `/openapi/v2/keywords/product-traffic-terms-trend`
- Input: required `asin`, exactly one of `keyword` / `keywords[]` (1–20), `dateFrom`, `dateTo`; optional `marketplace`; compatibility-retained `granularity` supports only `week`
- Do not send legacy `lookbackDays`, `page`, `pageSize`, `sortBy`, or `sortOrder`
- Data window: ASIN + keyword weekly trend across the requested date range; date range cannot exceed 26 weeks
- Date rule: prefer T-1 or earlier for `dateTo`; avoid current-date lookup unless explicitly requested
- Response shape: `data.context + data.items[].series[]`, preserving keyword request order
- Item fields: `identity`, `status=ok|empty`, `series[]`, `emptyReason`, nullable `errorCode`, nullable `errorMessage`
- Each series point groups fields under `asinSnapshot`, `traffic`, `placement`, `keywordMetrics`, and `adActivity`; keep their returned period boundaries separate
- Diagnosis curves/events: price (`asinSnapshot.latestPrice`), BSR (`asinSnapshot.latestBsr`,
  `asinSnapshot.latestSubBsr`), sales (`asinSnapshot.latestMonthlySaleCount`), rating
  (`asinSnapshot.latestRating`, `asinSnapshot.latestRatingCount`), traffic estimate (`traffic.*`
  plus placement averages), and listing events (`asinSnapshot.latestTitle`, `asinSnapshot.latestMainImageLink`)
- Key groups: listing/product/rank fields in `asinSnapshot`; ORG/SP/SB/SBV/SPR impression points
  in `traffic`; positions/pages/observation times in `placement`; `keywordEstimateSearchCount`,
  `keywordAbaRank`, Top3 shares, and `metricWindow` in `keywordMetrics`;
  observation/campaign/ad counts in `adActivity`

### `/openapi/v2/keywords/product-traffic-trend`
- Provides ASIN-wide raw weekly traffic and term-coverage history across all observed keywords; it is the weekly-detail companion to the four-week metric profile.
- Read `references/openapi-reference.md § 19` for the request, response, status, field, date, batching, and billing contract.
- Apply `references/cli-contract.md` to every result.

### `/openapi/v2/keywords/product-traffic-trend-profile`
- Provides the server-calculated ASIN-wide four-week trend profile; use the raw trend endpoint when weekly points are required.
- Read `references/openapi-reference.md § 20` for the request, response, status, field, date, batching, and billing contract.
- Apply `references/cli-contract.md` to every result.

## Local Review Toolkit

When `/reviews/analysis` lacks aggregation (ASIN has <50 reviews or no daily snapshot),
fall back to live raw reviews + your own LLM. The toolkit does NOT call any external
LLM — you (the calling skill's LLM) perform the Map/Reduce steps.

**Workflow:**

```bash
# 1. Fetch raw reviews (up to 100, cursor-paginated, ~60s, 10 credits at full)
zoodata.py reviews-raw --asin B0XXXXXXXX [--marketplace US] [--max-pages 10]

# 2. For EACH review, render the per-review Map prompt
zoodata.py review-tag-prompt --review '<single review JSON>' \
    [--product-title "..."] [--product-category "..."]
# → Your LLM produces a JSON object with sentiment + 11 dimension arrays
#   (mentioned_scenarios, mentioned_issues, mentioned_positives, mentioned_improvements,
#    mentioned_buying_factors, mentioned_pain_points, user_profiles, mentioned_usage_times,
#    mentioned_usage_locations, mentioned_behaviors, keywords)
# Suggested map parallelism: ~20 concurrent if your LLM supports it

# 3. Collect candidate phrases per dimension. For EACH dimension render the Reduce prompt
zoodata.py review-reduce-prompt --label-type positives \
    --candidates '["comfortable","comfy","very comfortable",...]'
# → Your LLM produces {clusters: [{canonical, members}, ...]}
# Suggested chunk size for `keywords` dim when >150 candidates: 150 per call

# 4. Aggregate into reviews/analysis-compatible consumerInsights
zoodata.py review-aggregate --reviews raw.json --tagged tags.json --clusters clusters.json
# → Output shape matches /reviews/analysis: reviewCount, avgRating,
#   sentimentDistribution, consumerInsights[], topKeywords[]
```

**When to use the toolkit instead of `reviews/analysis`:**
- ASIN has fewer than 50 reviews
- `reviews/analysis` returns sparse `consumerInsights` (missing dimensions)
- Need the freshest possible data (Spider scrape vs. T+1 BigQuery snapshot)
- Need to analyze a brand-new product that has no daily snapshot yet

## Field Differences Across Endpoints

| Data | markets | products/competitors | realtime/product | reviews/analysis | realtime/reviews | price-band | brand | history |
|------|---------|---------------------|----------|---------|---------|------------|-------|---------|
| Sales | sampleAvgMonthlySales | monthlySalesFloor | ❌ | ❌ | ❌ | sampleSalesRate | sampleGroupMonthlySales | monthlySalesFloor[] |
| Price | sampleAvgPrice | price | buyboxWinner.price | ❌ | ❌ | bandMin/MaxPrice | sampleAvgPrice | price[] |
| BSR | sampleAvgBsr | bsr (int) | bestsellersRank[] | ❌ | ❌ | ❌ | ❌ | bsr[] |
| Rating | sampleAvgRating | rating | rating | avgRating | rating (per review) | sampleAvgRating | sampleAvgRating | rating[] |
| Reviews | sampleAvgReviewCount | ratingCount | ratingCount | reviewCount | reviews[] (raw text, max 100) | ❌ | sampleAvgRatingCount | ratingCount[] |
| Insights | ❌ | ❌ | ❌ | ✅ consumerInsights | ❌ (raw only — feeds Local Review Toolkit) | ❌ | ❌ | ❌ |
| Concentration | topSalesRate | ❌ | ❌ | ❌ | ❌ | sampleTop3BrandSalesRate | CR10 | ❌ |
| Opportunity | ❌ | ❌ | ❌ | ❌ | ❌ | sampleOpportunityIndex | ❌ | ❌ |

## Confidence Labels (all skills)
- 📊 **Data-backed** — direct API data
- 🔍 **Inferred** — logical reasoning from data
- 💡 **Directional** — suggestions, predictions

Strategy recommendations and subjective conclusions are NEVER 📊. Extreme growth (>200%) = 💡 only.

## Data Notes
- Sales (`monthlySalesFloor`) = lower-bound estimate
- Realtime = live; products/competitors = ~T+1 delay
- Marketplace coverage varies by endpoint; follow each endpoint schema
- Each call consumes credits; check `meta.creditsConsumed`

## Links
- [zoodata.ai](https://zoodata.ai) · [API Docs](https://api.zoodata.ai/api-docs) · [GitHub](https://github.com/SerendipityOneInc/ZooData-Skills) · support@zoodata.ai
