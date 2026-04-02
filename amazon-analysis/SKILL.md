---
name: Amazon Analysis — Full-Spectrum Research & Seller Intelligence
version: 1.1.4
description: >
  Amazon seller data analysis tool. Features: market research, product selection, competitor analysis, ASIN evaluation, pricing reference, category research.
  Uses scripts/apiclaw.py to call APIClaw API, requires APICLAW_API_KEY.
---

# APIClaw — Amazon Seller Data Analysis

> AI-powered Amazon product research. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `references/reference.md` | Load when you need exact field names or filter details |


## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys). Stored in `config.json` in skill root.

## Input

User provides: keyword, category, ASIN, or brand — depending on intent. Use intent routing below.

## API Pitfalls (CRITICAL)

1. **Category first**: keyword search is broad → MUST lock `categoryPath` via `categories` endpoint before other calls
2. **Brand + category**: Brand queries MUST include `--category` to avoid cross-category contamination
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER calculate price×sales), sales=`atLeastMonthlySales` (lower bound), opportunity=`sampleOpportunityIndex`
4. **reviews/analyze**: needs 50+ reviews per ASIN; try category mode first (3 calls for painPoints/buyingFactors/improvements), ASIN mode only if all 3 category calls fail
5. **Aggregation without categoryPath**: produces severely distorted data
6. **`.data` is array**: use `.data[0]`, not `.data.field`
7. **labelType**: only accepts ONE value per call — do NOT comma-separate
8. **product-history empty**: try oldest-listed ASINs first, up to 3 rounds of different ASINs before giving up
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

## Output Spec

Sections: Analysis findings → Data Source & Conditions table (interfaces, category, dateRange, sampleType, topN, filters) → Data Notes (estimated values, T+1 delay, sampling basis).

Confidence labels: 📊 Data-backed | 🔍 Inferred | 💡 Directional. User criteria override AI judgment.

## Limitations

Cannot do: keyword research, reverse ASIN, ABA data, traffic source analysis, historical price/BSR charts. Niche keywords may return empty — use category path instead.
