# ZooData Keyword and Supporting Acquisition Reference

> Read before choosing tools or interpreting fields. This file is the production capability whitelist; every listed route must be deployed and callable through its documented ZooData production surface.

## Contents

- [Layer model](#layer-model)
- [Production availability](#production-availability)
- [Common keyword endpoint contract](#common-keyword-endpoint-contract)
- [Live endpoints by layer](#live-endpoints-by-layer)
- [Authorized supporting acquisition surfaces](#authorized-supporting-acquisition-surfaces)
- [Evidence boundaries](#evidence-boundaries)
- [CLI and callable mapping](#cli-and-callable-mapping)

## Layer model

Keep the four layers distinct:

1. **Data endpoints** return traceable snapshots and details in `items[]`, `rows[]`, or `series[]`.
2. **Metric endpoints** return deterministic aggregate objects, context, coverage, and evidence—not full detail rows.
3. **Supporting acquisition surfaces** return current product fields or selected external-page representations required by a named diagnosis branch.
4. **Agent + skill workflows** combine evidence, explain it, add confidence and limitations, and recommend actions.

Do not move Agent outputs such as `recommendedAction`, `conclusion`, `reasoning`, root cause, or Mermaid diagrams into the API layer. Do not describe an Agent calculation as an API field.

## Production availability

| Endpoint | Layer | Live status | Verified live body |
|---|---|---|---|
| `keywords/detail` | data | available | `data.context + data.items[]` |
| `keywords/market-profile` | metric | published and available | `data.context + data.items[].marketProfile` |
| `keywords/trend-profile` | metric | published and live-validated | `data.context + data.items[].rows[]` |
| `keywords/trend` | data | available | `data.context + data.items[].series[]` |
| `keywords/extends` | data | available | `data.context + data.query + data.queryType + data.rows[]` |
| `keywords/search-results` | data | available | `data.context + data.identity + data.rows[]` |
| `keywords/product-traffic-terms` | data | available | `data.context + data.identity + data.rows[]` |
| `keywords/product-traffic-terms-trend` | data | available and live-validated | `data.context + data.items[].series[]` |
| `keywords/product-traffic-structure-profile` | aggregate metric | available and live-validated | `data.context + data.items[].productTrafficTermsProfile` |
| `keywords/product-traffic-trend` | data | available and live-validated | `data.context + data.items[].series[]` |
| `keywords/product-traffic-trend-profile` | metric | available and live-validated | `data.context + data.items[].rows[].trafficTrendProfile` |
| `realtime/product` | supporting product data | available | current ASIN product, offer, listing, and asset fields in `data` |
| WebTools `/search` | supporting URL discovery | available | `data.query + data.results[]` |
| WebTools `/scrape` | supporting page acquisition | available | requested page formats plus `data.meta` |
| WebTools `/scrape-interactive` | supporting interactive page acquisition | available | requested page formats plus `data.meta` after actions |

## Common keyword endpoint contract

### Identity and context

- Keyword identity: `{ keyword, site }`.
- ASIN identity: `{ asin, site }`.
- ASIN + keyword identity: `{ asin, keyword, site }`.
- Single query objects use `data.identity`; batch endpoints use `data.items[].identity`.
- `requestedDate*` records the request. `resolvedDate*` records the actual available observation; endpoint-specific context or series fields expose the returned period boundaries.
- Snapshot/current-window endpoints may contain `dataWindow.currentPeriod`; range endpoints use `resolvedDateFrom`, `resolvedDateTo`, and series dates instead.
- `latestObservedAt` is row collection time rather than a snapshot-period field.
- A null `resolvedDate*` returned with `status=empty` means the requested date resolved to no published observation: the date is outside the available window — more recent than the latest published week, or older than retained history — and is distinct from a resolved snapshot that simply does not contain the keyword. Weekly `date` / `dateTo` endpoints publish with a lag, so target a recent completed week rather than today.

### Batch behavior

The following live endpoints support batch subjects:

| Endpoint | Single subject | Batch subject | Limit |
|---|---|---|---:|
| `keywords/detail` | `keyword` | `keywords[]` | 20 |
| `keywords/market-profile` | `keyword` | `keywords[]` | 20 |
| `keywords/trend-profile` | `keyword` | `keywords[]` | 20 |
| `keywords/trend` | `keyword` | `keywords[]` | 20 |
| `keywords/product-traffic-structure-profile` | `asin` | `asins[]` | 20 |
| `keywords/product-traffic-terms-trend` | `asin + keyword` | `asin + keywords[]` | 20 keywords for one ASIN |
| `keywords/product-traffic-trend` | `asin` | `asins[]` | 20 |
| `keywords/product-traffic-trend-profile` | `asin` | `asins[]` | 20 |

Rules:

- Send exactly one of the single or batch fields.
- Batch only subjects with the same marketplace, snapshot/range, `granularity=week`, window, filters, and sort context; traffic-term trend batches must share one ASIN.
- Normalize every batch keyword to `LOWER(TRIM(value))` before calling, then deduplicate; uppercase, surrounding whitespace, or duplicate batch values return validation errors. Single-keyword request fields retain their endpoint-specific normalization behavior.
- Preserve input order in `data.items[]` and when merging multiple chunks.
- Outer `success` is service execution status, not proof that every item has data.
- Billing is per `status=ok` subject for batch keyword and product-traffic endpoints. `trend-profile` bills a keyword when at least one requested window row has `status=ok`. For the structure endpoint, each successfully returned ASIN item with `status=ok` is billed once, while an ASIN item with `status=empty` is not billed; raw ASIN trends follow the same per-successful-ASIN rule. Product traffic trend profiles bill an ASIN when at least one requested window row has `status=ok`. Empty-only subjects are not billed. Always use returned credit metadata rather than calculating credits from subject or row counts.

CLI examples:

```bash
python {skill_base_dir}/scripts/zoodata.py keyword-detail \
  --keywords "yoga mat,pilates mat" --date 2026-07-12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py keyword-market-profile \
  --keywords "yoga mat,pilates mat" --date 2026-07-12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py keyword-trend-profile \
  --keywords "yoga mat,pilates mat" --date 2026-07-12 \
  --window-periods 4,12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py keyword-trend \
  --keywords "yoga mat,pilates mat" \
  --date-from 2026-06-01 --date-to 2026-07-12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py product-traffic-structure-profile \
  --asins "B01CGLCGRA,B07FR2V8SH" --date 2026-07-12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py product-traffic-terms-trend \
  --asin B01CGLCGRA --keywords "yoga mat,pilates mat" \
  --date-from 2026-07-06 --date-to 2026-07-12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py product-traffic-trend \
  --asins "B01CGLCGRA,B07FR2V8SH" \
  --date-from 2026-06-01 --date-to 2026-07-12 --marketplace US

python {skill_base_dir}/scripts/zoodata.py product-traffic-trend-profile \
  --asin B01CGLCGRA --date 2026-07-12 \
  --window-periods 4 --detail-level summary --marketplace US
```

One request cannot contain more than 20 subjects. Each response preserves order only within that response and carries its own usage metadata.

### Empty results and errors

- Apply the local `cli-contract.md` for authoritative transport status, retry exhaustion, terminal-interface classification, process exit, and partial-result handling.
- `status=empty` means no matching observation in the resolved snapshot/window. It does not prove low demand.
- Distinguish the two empties by `resolvedDate*`: a non-null `resolvedDate*` with `status=empty` is a genuine no-observation result for that resolved snapshot; a null `resolvedDate*` is an out-of-window date selection, not evidence about the keyword.
- `keywords/extends` may return an empty `rows[]`; this is a valid successful response.
- Endpoint-specific validation details remain authoritative only when the shared contract classifies the outer response as HTTP 422. All eleven current keyword and product-traffic request schemas retain `granularity` for compatibility and accept only `week`; all currently support only marketplace `US`, and the bundled CLI sends both values explicitly. Legacy `lookbackDays` remains unsupported.

### Credits

Bundled CLI responses expose `_query.endpoint`, `_query.params`, and returned `meta.creditsConsumed` / `meta.creditsRemaining` when available. WebTools responses expose their own route-specific credit metadata when available.

## Live endpoints by layer

### Data layer: `keywords/detail`

Request:

- exactly one of `keyword` or `keywords[]` (1–20)
- required `date` (`YYYY-MM-DD`)
- `marketplace=US` only; default `US`
- compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: marketplace, site, requested/resolved date, weekly granularity, current period
- `data.items[]`: identity, `status=ok|empty`, `snapshotData`, `emptyReason`, and nullable `errorCode` / `errorMessage`
- `snapshotData`: `estimateSearchCount`, `abaRank`, Top3 click/conversion shares, market characteristics, SKU/brand/title coverage, `organicRolloverRate`, organic/ad counts, and Top48 organic-product benchmarks

`organicRolloverRate` is a direct snapshot field, but the published contract does not specify its formula, Top-N scope, observation cadence, or position-level meaning. Interpretation and inference limits for this field are owned by `serp-and-rollover.md`.

The current response uses `snapshotData.estimateSearchCount`, `totalSkuCount`, and item status; it does not expose the legacy `estimateSearchCountWeekly`, `totalSkuCnt`, or top-level `data:null` shape.

### Metric layer: `keywords/market-profile`

Availability:

- Production MCP tool name: `openapi_v2_keyword_market_profile`.
- The default CLI target is production. Use `ZOODATA_BASE_URL` only when an explicitly scoped alternate surface must be tested.

Request:

- exactly one of `keyword` or `keywords[]` (1–20)
- required `date` (`YYYY-MM-DD`)
- `marketplace=US` only; default `US`
- compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: marketplace, site, requested/resolved date, weekly period, and `scoringSpec` (`id`, `version`, `scoreType`, `scoreRange`, `referenceScope`)
- `data.items[]`: input-order identity, `status=ok|empty`, `marketProfile`, and `emptyReason`
- `marketProfile`: `marketCharacteristics`, `demandScale`, `top3Concentration`, `adActivity`, `top20OrganicEntryDifficulty`, `supplySaturation`, `brandStructure`, and `organicProductBenchmark`
- current profile objects use camelCase fields. Each scored dimension returns `supported`, `level`, `interpretation`, `calculationStatus`, `unsupportedReason`, and `levelEvidence.score.{value,direction}`
- internal objects are versioned by `context.scoringSpec`, which returns the model id/version, normalized range, and reference scope
- every dimension independently returns its own `supported`, `calculationStatus`, `level`, `levelEvidence.score.value`, and `unsupportedReason`; the current contract has no aggregate `calculationCoverage` object
- `marketCharacteristics.volatility` exposes its own support/status boundary, `type`, source value, and mapping-confidence evidence
- `marketCharacteristics.annualSeasonality` independently exposes support/status, `classification`, year-over-year correlation, eligible pair count, peak-pattern detection, and `peakPeriods`

This endpoint returns deterministic weekly snapshot evidence. It does not return history, strategy advice, root cause, recommended actions, or seller-private ABA-SQP conversion data. An unmatched keyword returns `status=empty`, `marketProfile=null`, and a descriptive `emptyReason`; context fields such as `resolvedDate`, `dataWindow`, and `scoringSpec` may then be null. Empty items are not billed; the response reports billing through `meta.creditsConsumed` / `meta.creditsConsumedExact`.

Layer fact: `keywords/market-profile` supplies server-calculated multidimensional profile objects; `keywords/detail` supplies raw snapshot fields. Unsupported profile dimensions do not imply that the raw endpoint contains their missing calculation inputs.

### Data layer: `keywords/trend`

Request:

- exactly one of `keyword` or `keywords[]` (1–20)
- `dateFrom`, `dateTo`; maximum 93-day range
- `marketplace=US` only; compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: requested/resolved range and weekly granularity
- `data.items[].series[]`: `periodStartDate`, `periodEndDate`, `estimateSearchCount`, `abaRank`, `abaTop3ClickShareRate`, `abaTop3ConversionShareRate`

This endpoint returns raw weekly history rather than fixed-window profile objects.

### Metric layer: `keywords/trend-profile`

Request:

- exactly one of `keyword` or `keywords[]` (1–20)
- required as-of `date` (`YYYY-MM-DD`)
- required `windowPeriods[]`: 1–4 unique values selected from `4`, `8`, `12`, `26`
- `marketplace=US` only; compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: marketplace/site, requested/resolved date, weekly granularity, and requested windows
- `data.items[]`: input-ordered keyword identity and one `rows[]` entry per requested window
- each row contains `rowContext`, `status=ok|empty`, `emptyReason`, and `trendProfile`
- available profiles contain `searchDemand` and `abaRank`; inspect `supported`, `calculationStatus`, and `unsupportedReason` independently
- `trendEvidence` fields are `{ value, direction }` pairs covering first/last/change evidence, normalized slope, direction consistency, and eligible/aligned period counts

This endpoint returns server-calculated fixed-window trend profiles, including normalized slope and direction-consistency evidence. Nullable `emptyReason` / `observedPeriodCount` remain null when the service does not return a value. Billing is per keyword with at least one `status=ok` row; use returned credit metadata.

### Data layer: `keywords/extends`

Request:

- required `query`; do not rename it to `keyword`
- `queryType=phrase|fuzzy`
- optional marketplace, page, pageSize (1–100), sortBy, sortOrder
- compatibility-retained `granularity` supports only `week`
- no date is required; the service uses the latest available weekly snapshot. A legacy `date` may be sent but is ignored.
- `sortBy=relevanceScore|estimateSearchCount|abaRank|keyword`

Response:

- `data.context.coverageType` and `coverageReason`
- `data.query`, `data.queryType`
- `data.rows[].matchData`: query, keyword, site, relevanceScore
- `data.rows[].keywordSnapshot`: `dataWindow.currentPeriod` plus the same core snapshot families as detail

The returned rows are paginated related-term recall for the requested query and query type. The contract does not define them as an exhaustive root-keyword universe or return a root-universe aggregate demand field.

The current response does not expose the legacy flattened `term`, `seedKeyword`, or `estimateSearchCountWeekly` fields.

### Data layer: `keywords/search-results`

Request:

- required `keyword`, `date`
- compatibility-retained `granularity` supports only `week`; do not send legacy `lookbackDays`
- optional `exploreTypes=ORG|SP|SB|SBV|SPR`, page/pageSize
- `sortBy=absolutePosition|estimateImpressionPoint|latestObservedAt|price|rating|ratingCount|recentSales|asin|title`

Response:

- `data.context`: requested/resolved date and returned period boundaries
- `data.identity`
- `data.rows[]`: `latestObservedAt`, placement/position, listing fields, `estimateImpressionPoint`, `keywordTotalEstimateImpressionPoint`

`keywords/search-results` is the documented observed-SERP contract. Returned rows distinguish `ORG` from sponsored placement types; `products/search` is not part of this SERP contract.

Interpretation, comparison, aggregation, and inference limits for `exploreType`, `estimateImpressionPoint`, and the repeated keyword-level `keywordTotalEstimateImpressionPoint` are owned by `serp-and-rollover.md`.

### Data layer: `keywords/product-traffic-terms`

Request:

- required `asin`, `date`
- compatibility-retained `granularity` supports only `week`; do not send legacy `lookbackDays`
- optional `keywordContains`, `exploreTypes`, page/pageSize
- optional `keywordEstimateSearchCountMin` / `keywordEstimateSearchCountMax` (integers >= 0) and `keywordAbaRankMin` / `keywordAbaRankMax` (integers >= 1); each minimum must not exceed its maximum
- `sortBy=trafficShare|estimateImpressionPoint|absolutePosition|avgPosition|keywordEstimateSearchCount|keywordAbaRank|latestObservedAt|keyword`

Response:

- `data.context`, `data.identity`, `data.rows[]`
- rows include placement/position, keyword, impression points, `trafficShare`, `avgPosition`, coverage/observation counts, estimated keyword search count, and numeric ABA rank

Use `product-traffic-terms` for any target ASIN, including a competitor. The MCP `competitor-product-keywords` tool is retired and returns `tool_retired` with replacement `openapi_v2_product_traffic_terms`; it has no separate competitor/overlap contract.

Interpret `trafficShare`, placement, contribution, and coverage fields through `traffic-observation-semantics.md`.

### Data layer: `keywords/product-traffic-terms-trend`

Request:

- one ASIN and exactly one of `keyword` or `keywords[]` (1–20)
- `dateFrom`, `dateTo`; maximum 26-week range
- compatibility-retained `granularity` supports only `week`; do not send legacy `lookbackDays`
- no page/pageSize pagination for series

Response:

- `data.context`: requested/resolved range, granularity, and returned period boundaries
- `data.items[].identity`, `status=ok|empty`, `series[]`, `emptyReason`, and nullable `errorCode` / `errorMessage`
- each series point contains:
  - `date`
  - `asinSnapshot`: title, price, link/image, brand, badges, sales, rating, BSR, video
  - `traffic`: ORG/SP/SB/SBV/SPR impression points
  - `placement`: organic/ad positions, pages, observation timestamps, average observations
  - `keywordMetrics`: `metricWindow`, `keywordEstimateSearchCount`, `keywordAbaRank`, and Top3 shares
  - `adActivity`: observation count, day coverage, campaign count, ad count

Interpret the series' snapshot, weekly-period, metric-window, placement, traffic, and ad-activity fields through `traffic-observation-semantics.md`.

### Metric layer: `keywords/product-traffic-structure-profile`

Request:

- required `date` and exactly one of `asin` / `asins[]` (1–20)
- optional `marketplace`; compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: marketplace, requested/resolved date, granularity, and current/previous data windows
- input-ordered `data.items[]`: `identity`, `status=ok|empty`, `emptyReason`, and nullable `productTrafficTermsProfile`
- `status=empty` with `emptyReason=current_period_unavailable` is a coverage boundary, not low-traffic evidence

Observed non-null `productTrafficTermsProfile` modules and fields. The retained response field name
does not change this endpoint's role as a current-vs-previous-week structure metric:

- `summary`: `currEstimateImpressionPoint`, `prevEstimateImpressionPoint`,
  `impressionPointChangeCount`, `impressionPointChangeRate`, `currTermCount`, `prevTermCount`,
  `termCountChange`, `termCountChangeRate`, `totalIncreaseImpressionPoint`, and
  `totalDecreaseImpressionPoint`
- `trafficStructureChange`: objects keyed by returned traffic type (observed live: `ORG`, `SP`, `SB`,
  `SPR`); each channel object contains `currEstimateImpressionPoint`, `currAsinTrafficShare`,
  `prevEstimateImpressionPoint`, `prevAsinTrafficShare`, `impressionPointChangeCount`,
  `impressionPointChangeRate`, `currTermCount`, `prevTermCount`, `termCountChange`, and
  `termCountChangeRate`
- `organicStructureChange`: `currTermCount`, `prevTermCount`, `termCountChange`,
  `termCountChangeRate`, `newTermCount`, `lostTermCount`, `newTerms[]`, and `lostTerms[]`
- `termChangeDrivers`: `gainerCount`, `loserCount`, `top10Gainers[]`, and `top10Losers[]`

Preserve these exact field names. Previous-period fields and comparison arrays are nullable or
empty according to the returned response schema. Interpret their meanings, comparison boundaries,
and prohibited reconstructions only through `traffic-observation-semantics.md`.

### Data layer: `keywords/product-traffic-trend`

Request:

- exactly one of `asin` / `asins[]` (1–20)
- required `dateFrom`, `dateTo`; maximum 26-week range
- optional `marketplace`; compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: requested and resolved weekly range
- input-ordered `data.items[]`: ASIN identity, `status=ok|empty`, `emptyReason`, and `series[]`
- each series point: period boundaries, total/organic/ad impression points, total/organic/ad term
  counts, organic first-three-page term count, channel traffic, keyword-demand-rank distribution,
  and organic-acquisition-rate distribution

This endpoint is ASIN-level across all observed keywords and has no keyword dimension. Missing
weeks are not zero-filled. Interpret returned traffic, coverage, and distribution fields only
through `traffic-observation-semantics.md`.

### Metric layer: `keywords/product-traffic-trend-profile`

Request:

- exactly one of `asin` / `asins[]` (1–20)
- required as-of `date`
- optional `windowPeriods`, default `[4]`; `[4]` is the only supported value
- optional `detailLevel=summary|full` and `marketplace`; compatibility-retained `granularity` supports only `week`

Response:

- `data.context`: detail level, requested/resolved date, weekly granularity, and requested window
- input-ordered `data.items[].rows[]`; read row `status`, then component `supported`,
  `calculationStatus`, and `unsupportedReason`
- `trafficTrendProfile`: total, organic, and ad traffic plus term coverage; summary mode returns
  core classifications and evidence, while full mode may add placement/distribution breakdowns

Interpret returned trend conclusions, evidence values, change units, and comparison limits only
through `traffic-observation-semantics.md`.

## Authorized supporting acquisition surfaces

These supporting surfaces are part of this skill's production whitelist only when a named product or page observation is required for the active scenario's subject-level inference. They do not replace keyword demand, trend, SERP, traffic-term, timeline, or seller-funnel evidence.

### Structured product data: `realtime/product`

Request:

- required `asin`
- optional `marketplace`; use the active keyword workflow marketplace

Response fields include current title, brand, rating/review count, features, description, specifications, variants, bestsellers rank, Buy Box/price, images, dimensions, and weight when available.

This endpoint supplies the current ASIN representation, offer, listing text, and asset URLs. It is a current product snapshot, not a historical event stream, seller conversion funnel, or causal explanation. An asset URL proves availability, not visual quality.

### ZooData WebTools: `/search`, `/scrape`, and `/scrape-interactive`

Base surface: `/openapi/v2/webtools/*`, authenticated with `ZOODATA_API_KEY`.

Route roles:

- `/search` discovers candidate URLs from a required query. It is WebTools URL discovery, never `products/search`; result titles and snippets are source-selection metadata, not selected-page content.
- `/scrape` acquires requested representations for a known full URL.
- `/scrape-interactive` acquires requested representations for a known URL after explicit rendering or page actions; actions support wait, click, write, press, scroll, scrape, and JavaScript execution.

Contract boundaries:

- `/search` requires `query`; optional fields include `limit` (1–20), sources, time filter, and bare-hostname domain filters. Omit `scrapeOptions` for discovery-only use.
- `/scrape` requires a full `url`; `/scrape-interactive` requires `url` plus an actions array. Prefer structured JSON for evidence extraction.
- Check `success`, the returned target URL, and `data.meta.statusCode`. A successful WebTools envelope may still contain a target-page error.
- Preserve the acquired representation and page scope. Page content is direct page evidence, not proof of Amazon ranking logic, attribution, conversion, profitability, or causality.
- Search deep-scrape can bill per returned result; discovery-only search does not require `scrapeOptions`.

These routes have no bundled CLI subcommand and are callable only through an exposed ZooData WebTools session/callable surface whose live schema matches the requested route.

## Evidence boundaries

### Generic analytical capabilities

These are capability facts derived from the documented endpoints and user-provided seller data. Scenario files select applicable combinations; they do not create new capabilities.

| Capability | Evidence source | Contract boundary |
|---|---|---|
| Query/seed relation | `keywords/extends` match data, query wording, and `keywords/search-results` when retrieved | Describes relation to the query and observed returned rows; it is not product conversion or campaign-fit evidence. |
| Demand and weekly trend | `keywords/market-profile`, `keywords/trend-profile`, and documented raw snapshot/trend fields | Snapshot scale and weekly movement are distinct; these endpoints do not forecast. |
| Market structure and SERP | Market-profile dimensions and `keywords/search-results` rows | Each metric retains its returned subject, population, and scope; no composite score is provided. |
| Current ASIN posture | `realtime/product`, placement, traffic-term, structure-profile, and trend endpoints | Observes the returned ASIN/keyword subject and period; it does not supply seller conversion funnel data. |
| Page or asset observation | WebTools `/search` for URL discovery, then `/scrape` or `/scrape-interactive` for the selected page | Preserves the acquired page representation; it does not establish ranking logic, attribution, conversion, or cause. |
| Seller funnel and advertising economics | User-provided ABA-SQP and Amazon Ads search-term data | These are user-provided first-party inputs, not ZooData keyword endpoint outputs. |

### Capability-to-contract matrix

| Capability | Contract that supplies it | Returned evidence boundary |
|---|---|---|
| Candidate recall | `keywords/extends` | Related-term rows and match data; latest weekly snapshot only. |
| Raw demand snapshot / official rollover | `keywords/detail` | Snapshot search/rank/share/count fields and `organicRolloverRate`. |
| Weekly market dimensions | `keywords/market-profile` | Server-calculated profile dimensions with per-item and per-dimension status. |
| Weekly trend shape | `keywords/trend-profile` | Fixed-window demand and ABA-rank profile rows. |
| Raw weekly trend points | `keywords/trend` | Weekly search-count, ABA-rank, and Top-3 share series. |
| Observed keyword SERP | `keywords/search-results` | Returned product, placement, and impression-point rows. |
| Current ASIN traffic terms | `keywords/product-traffic-terms` | ASIN keyword rows, traffic share, placement, and keyword snapshot fields for any target ASIN, including a competitor. |
| ASIN × keyword movement | `keywords/product-traffic-terms-trend` | Nested product, traffic, placement, keyword-metric, and ad-activity time-series groups. |
| ASIN aggregate current structure/change | `keywords/product-traffic-structure-profile` | Server-returned structure dimensions, status/coverage, evidence, and current/previous period scope. |
| ASIN-wide raw weekly trend | `keywords/product-traffic-trend` | Weekly total/organic/ad traffic and term-coverage series across all keywords. |
| ASIN-wide four-week trend conclusion | `keywords/product-traffic-trend-profile` | Server-returned component conclusions, support status, and trend evidence. |
| Current product/listing inspection | `realtime/product` | Current ASIN product, offer, listing, and asset-link fields only. |
| URL discovery | WebTools `/search` | Candidate result URLs and snippets for selecting a source; not product search or page-content proof. |
| Known-page acquisition | WebTools `/scrape` or `/scrape-interactive` | Returned content for the selected URL and representation; interactive mode is reserved for rendering/actions. |

The endpoint sections above contain the exact parameters, limits, date behavior, status meanings, fields, and billing facts.

## CLI and callable mapping

The bundled CLI mapping for `python {skill_base_dir}/scripts/zoodata.py` is:

| HTTP endpoint | CLI subcommand |
|---|---|
| `keywords/detail` | `keyword-detail` |
| `keywords/market-profile` | `keyword-market-profile` |
| `keywords/trend-profile` | `keyword-trend-profile` |
| `keywords/trend` | `keyword-trend` |
| `keywords/extends` | `keyword-extends` |
| `keywords/search-results` | `keyword-search-results` |
| `keywords/product-traffic-terms` | `keyword-product-traffic-terms` |
| `keywords/product-traffic-structure-profile` | `product-traffic-structure-profile` |
| `keywords/product-traffic-terms-trend` | `product-traffic-terms-trend` |
| `keywords/product-traffic-trend` | `product-traffic-trend` |
| `keywords/product-traffic-trend-profile` | `product-traffic-trend-profile` |
| `realtime/product` | `product` |

WebTools `/search`, `/scrape`, and `/scrape-interactive` are authorized only through an exposed ZooData WebTools session/callable surface. Inspect its exact live schema first; never infer a callable name from an HTTP path or treat `products/search` as WebTools `/search`.

If using any MCP/session tool, inspect the live tool surface and exact schema first. Never infer a callable name from an HTTP path or draft name.
