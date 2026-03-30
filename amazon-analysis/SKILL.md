---
name: Amazon Product Research & Seller Analytics
version: 1.1.3
description: >-
  Amazon product research and seller analytics. 14 selection strategies, competitor tracking,
  BSR trends, review analysis, sales estimation, listing optimization, market opportunities.
  200M+ product database via APIClaw API. Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/Amazon-analysis-skill
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---
# APIClaw — Amazon Seller Data Analysis
> **Language rule**: Always respond in the user's language.
> All API calls via `scripts/apiclaw.py` — 11 endpoints, built-in error handling.

## Credentials
`APICLAW_API_KEY` env var → `https://api.apiclaw.io`. Free key at apiclaw.io/api-keys (1,000 credits).
New keys need 3-5s to activate — retry once on 403. Do NOT write keys to disk.

## File Map
| File | When to Load |
|------|-------------|
| `SKILL.md` (this file) | Always — endpoints, routing, output rules |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/execution-guide.md` | Full Mode analysis — complete execution protocols |
| `references/reference.md` | Need exact field names or response structure |
| `references/scenarios-composite.md` | Comprehensive recommendations (2.10) or Chinese seller cases (3.4) |
| `references/scenarios-eval.md` | Product evaluation, risk assessment, review analysis (4.x) |
| `references/scenarios-pricing.md` | Pricing strategy, profit estimation, listing reference (5.x) |
| `references/scenarios-ops.md` | Market monitoring, competitor tracking, anomaly alerts (6.x) |
| `references/scenarios-expand.md` | Product expansion, trends, discontinuation decisions (7.x) |
| `references/scenarios-listing.md` | Listing writing, optimization, content creation (8.x) |

## Category Resolution (mandatory)
1. `categories --keyword` → if empty, split/broaden (up to 3 tries) → still empty, extract from `product --asin`
2. Validate categoryPath matches intended product; use as primary filter for all calls
3. Broad interests → use `market` to scan subcategories, rank by opportunity score

## Input Collection
Collect missing inputs in ONE message: ✅ keyword/categoryPath (required) | 💡 marketplace, ASIN, budget | 📌 competitor ASINs, brand

## Script Usage
All commands output JSON. `.data` type varies by endpoint: **array** for list endpoints (products, competitors, categories, markets) — use `.data[0]`; **object** for single-result endpoints (realtime/product, price-band-overview, brand-overview) — use `.data.fieldName` directly.

### categories — Category tree lookup
```bash
python3 scripts/apiclaw.py categories --keyword "pet supplies"
```

### market — Market-level aggregates
```bash
python3 scripts/apiclaw.py market --category "Pet Supplies,Dogs" --topn 10
```

### products — Product selection (14 built-in modes)
```bash
python3 scripts/apiclaw.py products --keyword "yoga mat" --mode beginner
python3 scripts/apiclaw.py products --keyword "yoga mat" --mode beginner --price-max 30
```
⚠️ Default `fuzzy` matching may hit brand names. Use `--keyword-match-type exact|phrase` + `--category`.
Category with commas: use ` > ` separator.

### competitors — Competitor lookup
```bash
python3 scripts/apiclaw.py competitors --keyword "wireless earbuds"
python3 scripts/apiclaw.py competitors --asin B09V3KXJPB
```
⚠️ Broad keywords may return empty results — use `products` sorted by sales as an alternative source when needed.
⚠️ Field name: uses `brand` (not `brandName` like products/search).

### product — Single ASIN real-time detail
```bash
python3 scripts/apiclaw.py product --asin B09V3KXJPB
```
⚠️ Null fields → find parentAsin via `products --keyword "{asin}"`, re-fetch with parent.

### analyze — AI review insights (11 dimensions)
```bash
python3 scripts/apiclaw.py analyze --asin B09V3KXJPB
python3 scripts/apiclaw.py analyze --category "Pet Supplies,Dogs,Toys" --period 90d
```
Labels: scenarios, issues, positives, improvements, buyingFactors, painPoints, keywords, userProfiles, usageTimes, usageLocations, behaviors.
⚠️ Needs 50+ reviews. Falls back to realtime topReviews. Analyze brands independently, never mix ASINs.
⚠️ If category mode returns no results, auto-switch to ASIN mode with top 3 ASINs from products/search.

### price-band-overview / price-band-detail — Price segment analysis
```bash
python3 scripts/apiclaw.py price-band-overview --keyword "yoga mat"
python3 scripts/apiclaw.py price-band-detail --keyword "yoga mat" --price-min 20 --price-max 40
```

### brand-overview / brand-detail — Brand landscape
```bash
python3 scripts/apiclaw.py brand-overview --keyword "yoga mat"
python3 scripts/apiclaw.py brand-detail --keyword "yoga mat" --brand "Manduka"
```

### product-history — Historical trends
```bash
python3 scripts/apiclaw.py product-history --asins B09V3KXJPB,B08YYYYY --start-date 2026-03-01 --end-date 2026-03-30
```
⚠️ Uses `--asins` (plural) + `--start-date`/`--end-date`. Does NOT accept `--asin` or `--period`.

### report / opportunity — Composite commands
```bash
python3 scripts/apiclaw.py report --keyword "pet supplies"
python3 scripts/apiclaw.py opportunity --keyword "pet supplies" --mode fast-movers
```
`report` runs: categories → market → products (top 50) → realtime (top 1). ~4-5 credits.
`opportunity` runs: categories → market → products (filtered) → realtime (top 3). ~5-7 credits.

## Intent Routing

| User Says | Command | Scenario File |
|-----------|---------|---------------|
| "which category has opportunity" | `market` + `categories` | — |
| "check B09XXX" / "analyze ASIN" | `product --asin` | — |
| "find products" / "select products" | `products --mode XXX` | — |
| "comprehensive recs" / "what to sell" | `products` (multi-mode) + `market` | scenarios-composite § 2.10 |
| "Chinese seller cases" | `competitors --page-size 50` | scenarios-composite § 3.4 |
| "pain points" / "consumer insights" | `analyze --asin` + `product --asin` | scenarios-eval § 4.2 |
| "category pain points" / "user portrait" | `analyze --category` | scenarios-eval § 4.6 |
| "compare products" | `competitors` / multiple `product` | scenarios-eval § 4.3 |
| "risk assessment" / "can I do this" | `product` + `market` + `competitors` | scenarios-eval § 4.4 |
| "monthly sales" / "estimate sales" | `competitors --asin` | scenarios-eval § 4.5 |
| "pricing strategy" | `market` + `products` | scenarios-pricing § 5.1 |
| "profit estimation" | `competitors` | scenarios-pricing § 5.2 |
| "listing reference" | `product --asin` | scenarios-pricing § 5.3 |
| "market changes" | `market` + `products` | scenarios-ops § 6.1 |
| "competitor updates" | `competitors --brand` | scenarios-ops § 6.2 |
| "trends" / "rising" | `products --growth-min 0.2` | scenarios-expand § 7.3 |
| "should I delist" | `competitors --asin` + `market` | scenarios-expand § 7.4 |
| "write listing" / "bullet points" | `product --asin` (+ competitors) | scenarios-listing § 8.2 |
| "optimize listing" / "diagnosis" | `product --asin` + `competitors` | scenarios-listing § 8.3 |
| "price band" / "price distribution" | `price-band-overview` + `detail` | scenarios-pricing |
| "brand analysis" / "brand share" | `brand-overview` + `detail` | scenarios-composite |
| "historical trend" / "BSR history" | `product-history --asins` | scenarios-ops |

### Product Selection Modes (14 types)

| Intent | Mode | Key Filters |
|--------|------|-------------|
| beginner / new seller | `beginner` | Sales≥300, $15-60, auto-excludes red ocean |
| fast turnover | `fast-movers` | Sales≥300, growth≥10% |
| emerging / rising | `emerging` | Sales≤600, growth≥10%, ≤180d |
| single variant | `single-variant` | Growth≥20%, variants=1 |
| high demand low barrier | `high-demand-low-barrier` | Sales≥300, reviews≤50 |
| niche / long tail | `long-tail` | Sales≤300, BSR 10K-50K, ≤$30 |
| has pain points | `underserved` | Sales≥300, rating≤3.7 |
| new release | `new-release` | Sales≤500, NR tag |
| FBM / self-fulfillment | `fbm-friendly` | Sales≥300, FBM |
| cheap / low price | `low-price` | ≤$10 |
| broad catalog | `broad-catalog` | BSR growth≥99%, reviews≤10 |
| selective catalog | `selective-catalog` | BSR growth≥99% |
| speculative / piggyback | `speculative` | Sales≥600, sellers≥3 |
| top sellers / best sellers | `top-bsr` | Sub-cat BSR≤1000 |

## Quick Evaluation Criteria

| Metric (market) | Good | Warning |
|-----------------|------|---------|
| Concentration (topSalesRate, topN=10) | < 40% | > 60% |
| New SKU rate | > 15% | < 5% |
| FBA rate | > 50% | < 30% |
| Brand count | > 50 | < 20 |
| Top 10 brand sales rate | < 40% | > 60% |

| Metric (product) | High | Low |
|-------------------|------|-----|
| BSR | Top 1000 | > 5000 |
| Reviews | < 200 | > 1000 |
| Rating | > 4.3 | < 4.0 |
| Price band Opportunity Index | > 1.0 | < 0.5 |

> For full evaluation criteria and growth signal validation, see `references/execution-guide.md`

## Output Standards (Full Mode)

Every Full-mode response MUST include:
1. **Disclaimer** — "Based on APIClaw data as of [date]. Sales are lower-bound estimates. Validate before decisions."
2. **Confidence labels** on every conclusion: 📊 Data-backed/数据验证 | 🔍 Inferred/合理推断 | 💡 Directional/方向参考 (use label in user's language)
3. **Data Provenance** block — keyword, categoryPath, marketplace, timestamp, sample size, endpoints, credits
4. **API Usage** table (ALL modes, mandatory) — interface calls, credits consumed/remaining

⚠️ Self-check: if `📊 **API Usage**` is missing from your response, ADD IT before sending.

**Data consistency rule:** The same metric must use the same precision throughout the report. Do NOT use "10K+" in one table and "47,000" in another for the same product. Pick one level of precision and apply it consistently across all sections.

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."

**Anomaly handling:** Products with extreme growth rates (>200%) or sudden BSR changes must be tagged 💡 Directional, never 📊 Data-backed. Do NOT claim "proves innovation works" or "confirms market opportunity" based on a single product's spike. State: "Product X showed [metric], which MAY indicate [hypothesis]. Further validation needed."

> For complete output templates, see `references/execution-guide.md` § Output Standards

## Known Issues

- `reviewCountMin/Max` filter may not work reliably → use `--sort ratingCount --order asc --sales-min 300` as workaround
- Broad keyword matching pollutes results → always add `--category`
- `reviews/analyze` may return no data for some ASINs → skip and try alternative ASIN
- Use single `labelType` per request for best results
- Single product growth ≠ category trend → validate against `market` data
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.

## Limitations

- No keyword research / reverse ASIN / ABA data / traffic source analysis
- No historical sales curves (14-month) or historical price/BSR charts
- No raw review text export (use `realtime/product` topReviews for quotes)
- Non-US marketplace: core fields OK, sales may be null
- Niche keywords may return empty → use `--category` instead

> For complete error handling, API coverage, and field reference, see `references/execution-guide.md`
