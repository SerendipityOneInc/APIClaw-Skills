---
name: Amazon Analysis — Full-Spectrum Research & Seller Intelligence
version: 1.1.4
description: >
  Amazon seller data analysis tool. Features: market research, product selection, competitor analysis, ASIN evaluation, pricing reference, category research.
  Uses {skill_base_dir}/scripts/apiclaw.py to call APIClaw API, requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Seller Data Analysis

> AI-powered Amazon product research. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `{skill_base_dir}/scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `{skill_base_dir}/references/reference.md` | Load when you need exact field names or filter details |


## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys). Stored in `{skill_base_dir}/config.json` in skill root.

## Input

User provides: keyword, category, ASIN, or brand — depending on intent. Use intent routing below.

## API Pitfalls (CRITICAL)

1. **Category first**: keyword search is broad → MUST lock `categoryPath` via `categories` endpoint before other calls
2. **Brand + category**: Brand queries MUST include `--category` to avoid cross-category contamination
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER calculate price×sales), sales=`monthlySalesFloor` (lower bound), opportunity=`sampleOpportunityIndex`
4. **reviews/analysis**: needs 50+ reviews per ASIN; try category mode first (single call returns all dimensions), ASIN mode only if category call fails. Filter by `labelType` client-side from the `consumerInsights` array.
5. **Aggregation without categoryPath**: produces severely distorted data
6. **`.data` is array**: use `.data[0]`, not `.data.field`
7. **labelType**: NOT an API request parameter — it is a field in the response `consumerInsights` array, used for client-side filtering
8. **history empty**: try oldest-listed ASINs first, up to 3 rounds of different ASINs before giving up
9. **Sales null fallback**: Monthly sales ≈ 300,000 / BSR^0.65

## 14 Product Selection Modes

| Mode | One-line Description |
|------|---------------------|
| `hot-products` | High sales + strong growth momentum |
| `rising-stars` | Low base + rapid growth trajectory |
| `underserved` | Monthly sales≥300, rating≤3.7 — improvable products |
| `high-demand-low-barrier` | Monthly sales≥300, reviews≤50 — easy entry |
| `beginner` | $15-60, FBA, monthly sales≥300 — new seller friendly |
| `fast-movers` | Monthly sales≥300, growth≥10% — quick turnover |
| `emerging` | Monthly sales≤600, growth≥10%, ≤6 months old |
| `single-variant` | Growth≥20%, 1 variant, ≤6 months — small & rising |
| `long-tail` | BSR 10K-50K, ≤$30, exclusive sellers — niche |
| `new-release` | Monthly sales≤500, New Release tag |
| `low-price` | ≤$10 products |
| `top-bsr` | BSR≤1000 best sellers |
| `fbm-friendly` | Monthly sales≥300, self-fulfilled |
| `broad-catalog` | BSR growth≥99%, reviews≤10, ≤90 days |

Modes can combine with explicit filters (`--price-max`, `--sales-min`, etc). Overrides win.

## Composite Commands

- `report --keyword X` → categories + market + products(top50) + realtime(top1)
- `opportunity --keyword X [--mode Y]` → categories + market + products(filtered) + realtime(top3)

## Analysis Framework

Every analysis should address these dimensions where data is available:

### Market Health Assessment
| Indicator | Good | Caution | Warning |
|-----------|------|---------|---------|
| Monthly demand (sampleAvgMonthlySales) | >1,500 units 📊 | 500-1,500 📊 | <500 📊 |
| Brand concentration (CR10) | <40% 📊 | 40-60% 📊 | >60% 📊 |
| New entrant rate (sampleNewSkuRate) | >15% 📊 | 5-15% 📊 | <5% 📊 |
| Avg review count (sampleAvgRatingCount) | <500 📊 | 500-5,000 📊 | >5,000 📊 |
| FBA rate (sampleFbaRate) | >60% 📊 | 40-60% 📊 | <40% 📊 |

### Competitive Position Assessment
- **Price vs category avg**: >20% above = premium positioning, >20% below = value play 🔍
- **Rating vs category avg**: ≥0.3 above = quality advantage, ≥0.3 below = quality risk 🔍
- **Review count vs Top 10 avg**: <10% of leaders = high barrier, >50% = competitive 🔍
- **BSR trend (30d)**: Improving = momentum, stable = holding, declining = losing share 🔍

### Opportunity Viability
When user asks "should I sell X" or "is this a good niche":
- ALL of: demand >500, CR10 <60%, avgReviewCount <5,000 → Likely viable 🔍
- ANY of: demand <200, CR10 >80%, avgReviewCount >10,000 → Likely not viable 🔍
- Mixed signals → Present data, let user decide with their domain knowledge 💡

### Sales Estimation Notes
- `monthlySalesFloor` is a **lower-bound** estimate 📊
- Null sales fallback: Monthly sales ≈ 300,000 / BSR^0.65 🔍
- Revenue = `sampleAvgMonthlyRevenue` directly — NEVER calculate price × sales 📊

## Output Spec

Sections: Analysis findings → Data Source & Conditions table (interfaces, category, dateRange, sampleType, topN, filters) → Data Notes (estimated values, T+1 delay, sampling basis).

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "CR10 = 54.8% 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "brand concentration is moderate 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "consider entering $10-15 band 💡")

Rules: Strategy recommendations are NEVER 📊. Anomalies (>200% growth) are always 💡. User criteria override AI judgment.

### Data Provenance (required)

Include a table at the end of every report:

| Data | Endpoint | Key Params | Notes |
|------|----------|------------|-------|
| (e.g. Market Overview) | `markets/search` | categoryPath, topN=10 | 📊 Top N sampling, sales are lower-bound |
| ... | ... | ... | ... |

Extract endpoint and params from `_query` in JSON output. Add notes: sampling method, T+1 delay, realtime vs DB, minimum review threshold, etc.

### API Usage (required)

| Endpoint | Calls | Credits |
|----------|-------|---------|
| (each endpoint used) | N | N |
| **Total** | **N** | **N** |

Extract from `meta.creditsConsumed` per response. End with `Credits remaining: N`.

## Limitations

Cannot do: keyword research, reverse ASIN, ABA data, traffic source analysis, historical price/BSR charts. Niche keywords may return empty — use category path instead.
