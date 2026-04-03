---
name: Amazon Listing Audit Pro — 8-Dimension Health Check
version: 1.0.0
description: >
  Comprehensive listing health check and optimization engine for Amazon sellers.
  Scores listings across 8 dimensions, benchmarks against category leaders,
  identifies keyword gaps, and generates data-backed improvement recommendations.
  Supports single ASIN or bulk audit (10-100+ ASINs for agencies).
  Uses all 11 APIClaw API endpoints with cross-validation.
  Use when user asks about: listing audit, listing optimization, listing score,
  listing quality, improve my listing, listing review, listing diagnosis,
  title optimization, bullet point optimization, keyword gaps, listing benchmark,
  A+ content, listing health check, listing comparison.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Listing Audit Pro

> 8-dimension health check. Benchmark against leaders. Fix what matters most. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `references/reference.md` | Load for exact field names or response structure |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input

Required: my_asin + keyword. Collect missing inputs in ONE message.

## API Pitfalls (CRITICAL)

1. **Category first**: MUST resolve categoryPath via `categories --keyword` before data collection
2. **All keyword-based endpoints MUST include `--category`**; ASIN-specific endpoints do NOT
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`monthlySalesFloor`, opportunity=`sampleOpportunityIndex`
4. **reviews/analysis**: needs 50+ reviews; ASIN mode first, category fallback
5. **Sales null fallback**: Monthly sales ≈ 300,000 / BSR^0.65, tag 🔍

## Execution

1. Resolve & lock categoryPath
2. `listing-audit --my-asin X --keyword Y --category Z` (composite, runs all endpoints automatically)
3. Score 8 dimensions → generate report with improvements

## 8 Scoring Dimensions

| Dimension | Weight | 90-100 | 60-89 | 30-59 | 0-29 |
|-----------|--------|--------|-------|-------|------|
| Title | 15% | 150+ chars, top 3 KW, brand first | 100-150, 2 KW | <100 or stuffed | Missing key terms |
| Bullets | 15% | 5+, benefit-led, KW each | 5, features only | 3-4, generic | <3 bullets |
| Images | 15% | 7+, infographic+lifestyle | 5-6, decent | 3-4, basic | 1-2 images |
| A+ Content | 10% | Rich A+, comparison, brand story | Basic A+ | No A+ w/ description | Nothing |
| Reviews | 15% | 1000+, 4.5+, <5% 1-star | 200-1K, 4.0-4.5 | 50-200, 3.5-4.0 | <50 or <3.5 |
| Keywords | 10% | Top 5 competitor KW covered | 3-4 covered | 1-2 covered | None matched |
| Category Fit | 10% | Optimal category, top 1% BSR | Top 5% | Suboptimal | Wrong category |
| Pricing | 10% | In opportunity band, margin >25% | Hottest band | Outside top bands | Overpriced/<10% margin |

Score each 0-100, calculate weighted total. Include "Basis" column explaining each score.

## Output Spec

Sections: Overall Score (X/100, A-F grade) → 8-Dimension Scorecard → Title Audit (analysis + suggested rewrite) → Bullets Audit (vs leaders, missing points, rewrites) → Image Audit → Review Health → Keyword Gap Analysis (vs Top 5 leader titles/bullets) → vs Category Leaders (side-by-side Top 3) → Priority Fix List (lowest scores first) → Data Provenance → API Usage.

Suggested rewrites should incorporate high-frequency positive review language.

Confidence labels: 📊 Data-backed | 🔍 Inferred | 💡 Directional. Strategy is NEVER 📊. User criteria override AI judgment.

Bulk audit: share market data across ASINs, run audit per ASIN.

## API Budget: ~20-25 credits

Audit target(1) + Categories/Products/Competitors(3) + Realtime×5(5) + Market/Brand(3) + Price(2) + Reviews(2) + History(1) + Buffer(3-8).
