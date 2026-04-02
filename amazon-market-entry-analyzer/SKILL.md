---
name: Amazon Market Entry Analyzer — GO/CAUTION/AVOID Verdicts
version: 1.0.0
description: >
  One-click market viability assessment for Amazon sellers.
  Analyzes market size, competition intensity, brand landscape, pricing structure,
  and consumer pain points to deliver a GO/CAUTION/AVOID recommendation.
  Uses all 11 APIClaw API endpoints with cross-validation for data-backed decisions.
  Use when user asks about: market entry, can I sell, should I enter, market viability,
  is this niche worth it, category analysis, market opportunity, market assessment,
  niche evaluation, product category research.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# Amazon Market Entry Analyzer — GO / CAUTION / AVOID

One input (keyword/category). Full market viability assessment with sub-market discovery.

## Files
- **Script**: `scripts/apiclaw.py` (execute, don't read) — run `--help` for params
- **Reference**: `references/reference.md` (field names & response structure)

## Credential
Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys)

## Input
- **Required**: keyword or categoryPath
- **Optional**: marketplace (default US)

## API Pitfalls (shared with apiclaw skill — critical!)
- Keyword search is broad → **MUST lock categoryPath first** via `categories` endpoint
- Brand/price-band queries **MUST include --category** to avoid cross-category contamination
- Revenue = `sampleAvgMonthlyRevenue` (NEVER calculate avgPrice × totalSales — overestimates 30-70%)
- Sales = `atLeastMonthlySales` (lower bound). Fallback: 300,000 / BSR^0.65, tag 🔍
- Use `sampleOpportunityIndex`, `sampleTop10BrandSalesRate` directly — never reinvent
- `reviews/analyze` needs 50+ reviews; fallback to realtime ratingBreakdown
- Aggregation endpoints without categoryPath produce severely distorted data

## Unique Logic

### Sub-Market Discovery
Run `market --category "{path}" --topn 10 --page-size 20`, paginate all pages. Score each sub-market (1-100):

| Dimension | Weight | Field | Good→100 | Bad→0 |
|-----------|--------|-------|----------|-------|
| Demand | 25% | sampleAvgMonthlySales | ≥1500 | <200 |
| Profit | 25% | sampleAvgGrossMargin | ≥0.35 | <0.15 |
| New Entrant | 20% | sampleNewSkuRate | ≥0.20 | <0.05 |
| Brand Openness | 20% | topBrandSalesRate | ≤0.50 | ≥0.90 (inverted) |
| Capacity | 10% | totalSkuCount | 300-8000 | extreme |

**Fallback** (grossMargin=0 for all): redistribute to Demand 30%, New Entrant 25%, Brand 25%, Capacity 20%.

Present TOP 10 sub-markets. Ask user which to deep-dive (default: top 3). If ≤3 sub-markets, deep-dive all.

### Market Viability Score (1-100)

| Dimension | Weight | Good | Medium | Warning |
|-----------|--------|------|--------|---------|
| Market Size | 15% | >$10M/mo | $5-10M | <$5M |
| Market Trend | 10% | Rising | Stable | Declining |
| Competition | 25% | CR10<40% | 40-60% | >60% |
| Price Opportunity | 15% | oppIndex>1.0 | 0.5-1.0 | <0.5 |
| New Entrant Space | 10% | >15% | 5-15% | <5% |
| Consumer Pain Points | 15% | Clear gaps | Some | None |
| Profit Potential | 10% | >30% | 15-30% | <15% |

### Go/No-Go Decision
| Score | Signal | Action |
|-------|--------|--------|
| 70-100 | ✅ GO | Proceed with product development |
| 40-69 | ⚠️ CAUTION | Possible but needs differentiation |
| 0-39 | 🔴 AVOID | Too competitive or too small |

**CR10 dual-level check**: Category CR10 PASS + sub-market CR10 FAIL → ⚠️ CAUTION. Both FAIL → AVOID.
**User criteria override**: If user sets thresholds, ANY fail → CAUTION/AVOID. Never override.

## Composite Command
```bash
python3 scripts/apiclaw.py market-entry --keyword "{kw}" --category "{path}"
```
Runs all 11 endpoints (~20 calls). Output JSON is large — use targeted extraction, not full read.

## Output
Respond in user's language. Tag every conclusion: 📊 Data-backed / 🔍 Inferred / 💡 Directional.

Sections: Sub-Market Landscape → Executive Summary → Market Overview → Trend → Brand Landscape → Price Structure → Top 5 Competitors → Consumer Insights → Scoring Breakdown (with "Basis" column) → Entry Strategy → Data Provenance → API Usage → Cross-Market Comparison

Begin with disclaimer: data is as-of date, sales are lower-bound, validate before decisions.
If user provides COGS, calculate break-even and profit. If not, prompt for it.

## API Budget: ~20 calls
