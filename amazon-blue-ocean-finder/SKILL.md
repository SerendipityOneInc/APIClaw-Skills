---
name: Amazon Blue Ocean Finder — Untapped Product Discovery
version: 1.0.0
description: >
  Discover untapped, high-demand, low-competition products on Amazon.
  Scans using emerging, underserved, and high-demand-low-barrier modes to find
  blue ocean opportunities. Validates top candidates with all 11 APIClaw endpoints.
  Supports three entry modes: specific market, broad direction, or full-site scan.
  Use when user asks about: blue ocean, find products to sell, untapped niche,
  low competition products, what should I sell, product discovery, hidden gems,
  high demand low competition, find me opportunities, 蓝海产品, 找蓝海.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Blue Ocean Finder

> Find untapped products. High demand, low competition, real data.
>
> **Language rule**: Always respond in the user's language. Chinese input → Chinese output.
> All API calls go through `scripts/apiclaw.py`.

## Credentials

- Required: `APICLAW_API_KEY`
- Scope: used only for `https://api.apiclaw.io`
- Setup: Guide user to set the environment variable:
  ```bash
  export APICLAW_API_KEY='hms_live_xxxxxx'
  ```
- Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) (1,000 free credits on signup, no credit card required)
- Fallback: The script also checks `config.json` in the skill root directory if the env var is not set.
- **Do NOT write keys to disk files.** Always recommend the environment variable approach.
- New keys may need 3-5 seconds to activate — if first call returns 403, wait 3 seconds and retry (max 2 retries).

## File Map

| File | When to Load |
|------|-------------|
| `SKILL.md` (this file) | Always — execution flow + scoring criteria |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/reference.md` | Need exact field names or response structure |

## Execution Flow

### Step 0 — Parse Input & Determine Entry Mode

Analyze the user's message to determine which entry mode to use:

| Entry Mode | User Says | What To Do |
|------------|-----------|------------|
| **Specific Market** | "瑜伽垫蓝海" / "blue ocean in yoga mats" | Go to Step 0.5 for category resolution |
| **Broad Direction** | "家居类蓝海" / "home products blue ocean" | Go to Step 0.5, expect multiple categories |
| **Full-Site Scan** | "找蓝海" / "find blue ocean products" | Skip Step 0.5, go directly to Step 1 |

**Optional questions to improve results** (ask only if user hasn't specified):
- "Any price range preference?" → directly maps to `--price-min / --price-max`
- "FBA or FBM?" → maps to `--fulfillment`
- "Any product type preference?" → helps determine entry mode

**Do NOT ask questions that can't be used for API filtering:**
- ❌ Budget/startup capital (no API filter for this)
- ❌ Supply chain location (no API data)
- ❌ Experience level (doesn't affect search results)

If the user provides filtering criteria (e.g. "月销300+、评论<100、$15-35"), translate them directly to API params:

| User Says | API Param |
|-----------|-----------|
| "月销300+" / "at least 300 sales" | `--sales-min 300` |
| "评论不超过100" / "less than 100 reviews" | `--ratings-max 100` |
| "价格$15-35" | `--price-min 15 --price-max 35` |
| "评分4.3以下" | `--rating-max 4.3` |

### Step 0.5 — Category Resolution (Specific Market & Broad Direction only)

**Skip this step for Full-Site Scan mode.**

1. **Query categories endpoint**:
   ```bash
   python3 scripts/apiclaw.py categories --keyword "{keyword}"
   ```
2. **If multiple categories returned** — present ALL matching categories to the user and ask them to confirm which one(s) to scan:
   ```
   Found multiple matching categories:
   1. Home & Kitchen > Storage & Organization
   2. Office Products > Office Storage
   3. Closet Storage & Organization
   
   Which category(s) would you like me to scan for blue ocean products? You can select multiple.
   ```
   **Do NOT auto-select.** Wait for user confirmation.
3. **If empty** — broaden the keyword and retry (up to 3 variations).
4. **If still no match** — suggest switching to Full-Site Scan mode.

### Step 1 — Blue Ocean Scan

Scan for products using three blue-ocean-specific modes: `emerging`, `underserved`, `high-demand-low-barrier`.

**For Specific Market / Broad Direction** (category confirmed):
```bash
python3 scripts/apiclaw.py opportunity-scan --keyword "{keyword}" --category "{categoryPath}" --modes "emerging,underserved,high-demand-low-barrier" > /tmp/blue-ocean-scan.json 2> /tmp/blue-ocean-log.txt
```

**For Full-Site Scan** (no keyword, no category):
```bash
python3 scripts/apiclaw.py opportunity-scan --modes "emerging,underserved,high-demand-low-barrier" > /tmp/blue-ocean-scan.json 2> /tmp/blue-ocean-log.txt
```

**With user-specified filters** (stack on top of mode defaults):
```bash
python3 scripts/apiclaw.py opportunity-scan --modes "emerging,underserved,high-demand-low-barrier" --price-min 15 --price-max 35 --ratings-max 100 > /tmp/blue-ocean-scan.json 2> /tmp/blue-ocean-log.txt
```

This command automatically executes:
- **Product scan**: products/search × 3 modes × 5 pages (up to 300 products, deduplicated)
- **Market context**: markets/search + brand-overview + brand-detail
- **Price opportunity**: price-band-overview + price-band-detail
- **Realtime validation**: realtime/product × Top 10 candidates
- **Trend check**: product-history × Top 5
- **Consumer insights**: reviews/analyze × 3 labelTypes

**⚠️ Mode built-in parameters (these STACK with user filters):**

| Mode | Built-in Params |
|------|----------------|
| `emerging` | monthlySalesMax=600, salesGrowthRateMin=0.1, listingAge≤180d |
| `underserved` | monthlySalesMin=300, ratingMax=3.7, listingAge≤180d |
| `high-demand-low-barrier` | monthlySalesMin=300, ratingCountMax=50, listingAge≤180d |

**When user adds extra filters, they COMBINE with mode defaults.** Example: user says "$15-35" + mode=emerging (no price filter) → search range is $15-35. But mode=underserved (monthlySalesMin=300) + user says "月销200+" → actual is monthlySalesMin=300 (mode default takes precedence if higher). Always report the ACTUAL search parameters in the output.

After running, check the log:
```bash
cat /tmp/blue-ocean-log.txt
```

### ⚠️ CRITICAL RULES (read before ANY data analysis)

These rules are non-negotiable. Violating them invalidates the entire report.

1. **Revenue**: Use `sampleAvgMonthlyRevenue` or `sampleGroupMonthlyRevenue` DIRECTLY. **NEVER** calculate as avgPrice × totalSales — this overestimates by 30-70%.
2. **CR10 — Dual-level evaluation**: When evaluating brand concentration:
   - Check **category-level** CR10 (`sampleTop10BrandSalesRate` from brand-overview)
   - Check **sub-market-level** CR10 (`topBrandSalesRate` from markets/search)
   - If category low but sub-market high → note: "Category is fragmented overall, but this specific sub-market has higher brand concentration."
3. **User decision criteria**: If the user sets specific thresholds, evaluate EVERY criterion explicitly. If ANY fails → flag it clearly. **NEVER** hide unmet criteria.
4. **Mode built-in parameters**: See table above. User filters COMBINE with mode defaults, they don't replace them.
5. **Category filtering**: When a category is locked, EVERY endpoint that accepts --category MUST include it.
6. **Opportunity/concentration metrics**: Use API-provided fields directly (`sampleOpportunityIndex`, `sampleTop10BrandSalesRate`). NEVER invent your own formula when an API field exists.
7. **Trend data insufficiency**: 
   - ≥5 data points → normal scoring (0-100)
   - 1-4 data points → score capped at 60, tag 💡 Directional
   - No data → fixed 50, tag 💡 "Trend cannot be assessed"
   - Always note: "Trend analysis based on [N] data point(s) for [M] product(s)."
8. **Limitations honesty**: If a user criterion cannot be evaluated with available API data, say so explicitly. Do NOT make up data or silently skip the criterion. Example: "Your requirement for 'advertising cost < $2 CPC' cannot be evaluated — APIClaw does not provide CPC data. The results below are based on all other criteria."
9. **Per-product Price Opportunity**: Do NOT use a single global `sampleOpportunityIndex` for all candidates. For TOP 20 candidates, call `price-band-overview` with each product's category to get category-specific opportunity data. Different categories have vastly different opportunity landscapes.

### Step 2 — Score & Rank Candidates

From the scan results (up to 300 products, deduplicated), score each candidate:

**Blue Ocean Score (1-100):**

| Dimension | Weight | Source | Scoring Logic |
|-----------|--------|--------|---------------|
| Demand Signal | 27.5% | `atLeastMonthlySales` | 300-1000→60, 1000-5000→80, 5000-10000→90, >10000→100, <300→0 |
| Competition Gap | 27.5% | `ratingCount` (realtime-verified) | <10→100, 10-30→90, 30-50→80, 50-100→70, 100-500→40, >500→0 |
| Price Opportunity | 15% | `sampleOpportunityIndex` | >1.0→100, 0.5-1.0→linear, <0.5→0 |
| Trend Momentum | 15% | product-history BSR/sales | rising→100, stable→60, declining→20 |
| Profit Margin | 15% | `profitMargin` or estimated | >30%→100, 15-30%→linear, <15%→0 |

**Scoring notes:**
- Demand and Competition use **gradient scoring**, not pass/fail. All candidates already passed the user's minimum thresholds — the score differentiates "good" from "great".
- **Profit Margin fallback** (when `profitMargin` is null):
  1. If `fbaFee` is available: estimate as `(price - fbaFee) / price`. Tag 🔍 Inferred.
  2. If `fbaFee` is also null: use formula `1 - (0.15 + 6/price)` (15% Amazon commission + ~$6 avg FBA fee for small/light items). Tag 🔍 Inferred.
  3. If price < $10: auto-flag ⚠️ (low-price products have thin margins).
- **Trend Momentum** when product-history data is limited:
  - ≥5 data points → normal scoring (0-100)
  - 1-4 data points → score capped at 60, tag 💡 Directional
  - No data → fixed 50, tag 💡 "Trend cannot be assessed"

**Tier assignment:**

| Score | Tier | Label |
|-------|------|-------|
| 80-100 | 🔥 S | Hot Blue Ocean — act fast |
| 60-79 | ✅ A | Strong Opportunity — worth pursuing |
| 40-59 | ⚠️ B | Moderate — needs differentiation |
| 0-39 | ❌ C | Not a real blue ocean — skip |

Select **TOP 20** by score for deep validation in Step 3.

### Step 3 — Deep Validation (TOP 20)

For the top 20 candidates, run deep validation:

**Per-product validation (TOP 20):**
- `realtime/product` — get live price, BSR, current rating, review count, features, variants

**Per-category analysis (group TOP 20 by category, one call per unique category):**
- `brand-overview` — brand concentration (CR10) for each product's category
- `price-band-overview` — get category-specific `sampleOpportunityIndex` for Price Opportunity scoring. **Do NOT reuse a single global value for all products.**
- `brand-detail` — per-brand breakdown

**Selective deep-dive (TOP 5 only):**
- `product-history` — 30-day trend for top 5 candidates
- `reviews/analyze` — consumer insights (only if reviews ≥ 50, skip for typical blue ocean products)

**Cross-validation checks:**
- DB price vs realtime price: >20% gap → flag as "possible promotion, verify before sourcing"
- DB sales vs BSR trajectory: rising BSR (worse rank) + high DB sales → flag as "sales may be declining"
- Low reviews + high sales → genuine blue ocean signal ✅
- Low reviews + low sales → not blue ocean, just unpopular ❌

### Step 4 — Final Selection & Report

After scoring and validation, output the final report.

## Output Format

**Every report must begin with this disclaimer:**

> ⚠️ **Important**: This analysis is based on APIClaw API data as of [date]. Sales figures are lower-bound estimates. Blue ocean status is a directional assessment based on available data — always validate with additional research before committing resources.

**Confidence labels — EVERY data point MUST be tagged:**
- 📊 **Data-backed** — Direct API data
- 🔍 **Inferred** — Logical reasoning from data
- 💡 **Directional** — Suggestions, hypotheses

Report sections (all required):

1. **🔍 Scan Overview** — Entry mode used, modes run, total products scanned, deduplication count, user filters applied (with ACTUAL search parameters after mode defaults)
2. **🏆 TOP 10 Blue Ocean Products** — The core deliverable:

| # | ASIN | Title | Price | Monthly Sales | Rating | Reviews | Category | Blue Ocean Score | Tier |
|---|------|-------|-------|--------------|--------|---------|----------|-----------------|------|

3. **📋 TOP 3 Detailed Analysis** — For each:
   - Why it's blue ocean (demand vs competition gap)
   - Brand landscape in its category (CR10, top brands)
   - Price positioning (which band, opportunity index)
   - Consumer pain points (from reviews/analyze — differentiation angles)
   - Trend direction (from product-history)
   - Suggested entry strategy (💡)

4. **⚠️ Risk Alerts** — Products flagged for:
   - Declining BSR trend
   - Thin margins (<15%)
   - Seasonal patterns
   - Brand-dominated category (CR10 >70%)
   - Price-vs-realtime discrepancy (possible temporary promotion)

5. **📊 Scoring Breakdown (TOP 3)** — 5-dimension score (Demand 27.5%, Competition 27.5%, Price 15%, Trend 15%, Profit 15%) with "Basis" column explaining WHY each score was given

6. **🎯 Recommended Next Steps**:
   - 🔥 S-tier: "Buy a sample and start product development"
   - ✅ A-tier: "Run a deeper analysis (use Market Entry Analyzer)"
   - ⚠️ B-tier: "Add to watchlist, monitor for 2-4 weeks"
   - ❌ C-tier: not shown in final output

7. **📋 Data Provenance** — Query conditions, sample coverage, data freshness, known limitations

8. **📊 API Usage** — Per-endpoint call count, total credits consumed

**Scope acknowledgment:** End the report with: "This analysis covers demand signals, competition level, pricing opportunity, consumer sentiment, and short-term trends. NOT covered: advertising costs (CPC/ACoS), keyword search volume, supply chain logistics, and regulatory compliance."

## API Budget: ~60-80 credits

| Step | Calls | Credits |
|------|-------|---------|
| Category resolution | categories × 1-3 | 1-3 |
| Product scan | products/search × 3 modes × 5 pages | 15 |
| Realtime validation | realtime/product × 20 | 20 |
| Per-category brand | brand-overview × ~5-10 unique categories | 5-10 |
| Per-category pricing | price-band-overview × ~5-10 unique categories | 5-10 |
| Brand detail | brand-detail × ~3-5 | 3-5 |
| Trend check | product-history × 5 | 1-5 |
| Consumer insights | reviews/analyze × 3 (if reviews ≥ 50) | 0-3 |
| Market context | markets/search × 1-3 | 1-3 |
| **Total** | | **~60-80** |

## ⚠️ Important Notes

### Data Field Usage (MANDATORY)
- Revenue → use `sampleAvgMonthlyRevenue` or `sampleGroupMonthlyRevenue`, **NEVER** avgPrice × totalSales
- Opportunity → use `sampleOpportunityIndex`, **NEVER** invent your own formula
- Concentration → use `sampleTop10BrandSalesRate` or `topBrandSalesRate` directly
- Sales → use `atLeastMonthlySales`, label as "lower bound estimate"
- Profit margin → use `profitMargin` from products/search when available; if null, estimate as (price - fbaFee) / price and tag 🔍

### Blue Ocean Validation (MANDATORY)
A product is NOT blue ocean if ANY of these are true:
- `ratingCount` > 500 AND category CR10 > 60% → it's a competitive market, not blue ocean
- `atLeastMonthlySales` < 50 → it's not "high demand low competition", it's just unpopular
- Price is in the hottest band (highest sales share) with CR3 > 50% → that price band is already crowded

### Data Provenance (MANDATORY)
- Every key data point MUST be traceable to a specific API endpoint
- If manual calculation was done, show formula AND raw API fields
- **FORBIDDEN**: Presenting numbers without source, exposing HTTP errors, using words like "fallback", "degraded", "retry"

### Deduplication
- Same ASIN may appear across multiple modes (e.g. emerging AND underserved)
- Deduplicate by ASIN, keep the entry with the best supporting data
- Report: "Scanned [X] products across [Y] modes, [Z] unique after deduplication"
