---
name: Amazon Pricing Command Center
version: 1.0.0
description: >
  Data-driven pricing strategy engine for Amazon sellers.
  Analyzes competitor pricing, price band distribution, historical price trends,
  BuyBox dynamics, profit simulation, and market positioning to deliver
  optimal pricing recommendations with RAISE/HOLD/LOWER signals.
  Uses all 11 APIClaw API endpoints with cross-validation.
  Use when user asks about: pricing strategy, how much to price, optimal price,
  price optimization, competitor pricing, price war, BuyBox strategy,
  profit margin, pricing analysis, should I raise price, should I lower price,
  price comparison, price positioning, repricing.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Pricing Command Center

> Stop guessing. Price with data. RAISE / HOLD / LOWER.
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
- Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/api-keys) (1,000 free credits on signup, no credit card required)
- Fallback: The script also checks `config.json` in the skill root directory if the env var is not set.
- **Do NOT write keys to disk files.** Always recommend the environment variable approach.
- New keys may need 3-5 seconds to activate — if first call returns 403, wait 3 seconds and retry (max 2 retries).

## File Map

| File | When to Load |
|------|-------------|
| `SKILL.md` (this file) | Always — execution flow + pricing logic |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/reference.md` | Need exact field names or response structure |

## Execution Flow

### Step 0 — Parse Input

Extract from user message:
- **my_asin** (required): user's product ASIN
- **keyword** (required): product keyword for market context
- **cost** (optional): product cost / COGS for profit calculation. If Chinese input uses "块/元", default to RMB and convert to USD (÷7.2 approximate rate). When currency is ambiguous, ask to clarify.
- **target_margin** (optional): desired profit margin %
- **competitor_asins** (optional): specific competitors to benchmark against

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: my_asin + keyword
 💡 Recommended (significantly improves accuracy): cost (COGS), target_margin
 📌 Optional: competitor_asins"

Do NOT proceed until all required inputs are collected.

### Step 0.5 — Category Resolution (mandatory, do not skip)

Before any data collection, lock down the exact product category:

1. **Query categories endpoint** — try the user's keyword first:
   ```bash
   python3 scripts/apiclaw.py categories --keyword "{keyword}"
   ```
2. **If empty or too broad** — split/broaden the keyword and retry (e.g. "yoga mat" → "yoga", then drill into subcategories). Try up to 3 variations.
3. **If still no match** — use realtime/product on a known ASIN to extract categoryPath from its bestsellersRank field.
4. **Validate the categoryPath** — ensure it matches the user's intended product type, not a tangentially related category.

Once a precise categoryPath is confirmed, use it as the primary filter for all subsequent API calls:
- `markets/search` → use `--category "{categoryPath}"`
- `products/search` → add `--category "{categoryPath}"` alongside keyword
- For endpoints that only accept keyword (brand-overview, brand-detail, price-band), apply **post-retrieval category validation**: check each returned product's/brand's sampleProducts categoryPath against the target category. Exclude mismatches silently.

Record in the final report's Data Provenance section: the final categoryPath used, how it was resolved, and how many results were filtered out.

### Pre-Execution Checklist

Before proceeding to data collection, verify:
- ✓ `APICLAW_API_KEY` is set and valid
- ✓ categoryPath is locked (from Step 0.5)
- ✓ All required inputs collected (from Step 0)
If any check fails, stop and resolve before continuing.

### Step 1 — Current Price Snapshot (1 call)

```bash
python3 scripts/apiclaw.py product --asin {my_asin}
```

If realtime/product returns null fields (common for variant/child ASINs), use `products/search --keyword "{keyword}"` to find the parentAsin, then re-fetch with the parent ASIN.

Extract: current BuyBox price, rating, ratingBreakdown, BSR, seller count, features, images.

### Step 2 — Price Band Intelligence (2 calls, same keyword)

```bash
python3 scripts/apiclaw.py price-band-overview --keyword "{keyword}"
python3 scripts/apiclaw.py price-band-detail --keyword "{keyword}"
```

Map user's current price to a band. Identify: which band has highest sales, which has best opportunity index, where user sits relative to optimal.

### Step 3 — Competitor Price Landscape (3 calls)

```bash
# 3a. Category discovery
python3 scripts/apiclaw.py categories --keyword "{keyword}"

# 3b. Top competitors by sales (use categoryPath from 3a to filter noise)
python3 scripts/apiclaw.py products --keyword "{keyword}" --page-size 20

# 3c. More competitors for price distribution
python3 scripts/apiclaw.py competitors --keyword "{keyword}" --page-size 20
```

If competitors endpoint returns empty results, rely on products/search as the primary competitor price source.

Filter results by categoryPath to exclude irrelevant products (e.g. keyword "yoga mat" may return incense or diffusers). Only include products in the target product's category.

Build price distribution: count competitors at each price point, identify price clusters.

### Step 4 — Market Benchmarks (3 calls)

```bash
python3 scripts/apiclaw.py market --category "{categoryPath}" --topn 10
python3 scripts/apiclaw.py brand-overview --keyword "{keyword}"
python3 scripts/apiclaw.py brand-detail --keyword "{keyword}"
```

Extract: market avg price, top brand avg price, margin benchmarks. Use sampleProducts from brand-detail to see pricing patterns of leading brands.

### Step 5 — Historical Price Trends (1 call)

```bash
python3 scripts/apiclaw.py product-history --asins "{my_asin},{comp1},{comp2},{comp3},{comp4}" --start-date "{30d_ago}" --end-date "{today}"
```

For each: price trend, BSR response to price changes, sales impact. Detect if competitors ran promotions.

### Step 6 — Realtime Competitor Deep-Dive (5 calls)

```bash
python3 scripts/apiclaw.py product --asin {comp1}
python3 scripts/apiclaw.py product --asin {comp2}
python3 scripts/apiclaw.py product --asin {comp3}
python3 scripts/apiclaw.py product --asin {comp4}
python3 scripts/apiclaw.py product --asin {comp5}
```

Cross-validate prices (database vs realtime). Get BuyBox details, fulfillment method, seller info.

**DB + Realtime cross-reference principle:** Database data (products/search) provides broad quantitative metrics with ~T+1 delay. Realtime data (realtime/product) provides current qualitative content. Always compare both — discrepancies reveal promotions, listing changes, or data lag. Flag differences explicitly in the report (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

### Step 7 — Review Context (1-3 calls)

```bash
python3 scripts/apiclaw.py analyze --asin {my_asin}
python3 scripts/apiclaw.py analyze --asin {top_comp}
```

Correlate: does higher price = higher rating? Are low-price competitors getting complaints about quality? Price-quality perception mapping.

If reviews/analyze fails, silently use topReviews from Step 1/6 realtime data.

### Step 8 — Price Drill-Down (1 call)

Drill into the best opportunity price band:
```bash
python3 scripts/apiclaw.py products --keyword "{keyword}" --price-min {band_min} --price-max {band_max} --page-size 20
```

### Step 9 — Calculate & Recommend

Combine all data. Generate pricing signal and profit simulations.

## Pricing Signal Logic

| Signal | Condition |
|--------|-----------|
| **RAISE** | Current price below opportunity band AND rating >= category avg AND BSR stable/rising |
| **HOLD** | Current price in optimal band AND BSR stable AND no competitor price war detected |
| **LOWER** | Current price above hottest band AND BSR declining OR competitor undercut detected |

**Output confidence context with every recommendation:**
- State the recommendation with its confidence label (📊/🔍/💡)
- Include: "Based on [X] data points from [Y] endpoints, sample of [Z] products"
- For scores: append "(Confidence: High/Medium/Low — [brief reason])"
- Acknowledge specific data gaps that may affect the conclusion
- End with: "Recommended next step: [specific validation action] before committing resources."

### New Seller Price Band Selection

When recommending entry price for new sellers, do NOT simply pick the highest-sales band. Calculate the **Sales/Competition Ratio** per price band:

`Sales/Competition Ratio = Average Monthly Sales ÷ Average Review Count`

A high ratio means: strong demand but low review barriers — ideal for new entrants. Present this in the Price Band Heatmap:

| Band | Avg Sales | Avg Reviews | Sales/Competition Ratio | New Seller Fit |
|------|-----------|-------------|------------------------|----------------|

The band with the highest ratio (not highest sales) is the recommended entry point for new sellers.

## Profit Simulation

3 scenarios: Conservative (current price), Moderate (+/- $1-2), Aggressive (+/- $3-5).
Per scenario: Revenue = Price × Est. Sales, minus FBA Fee + Referral Fee (15%) + COGS = Net Profit & Margin.

## Output Format

**Every report must begin with this disclaimer:**

> ⚠️ **Important**: This analysis is based on APIClaw API data as of [date]. Sales figures are lower-bound estimates. Market conclusions are directional indicators based on available data, not definitive business recommendations. Always validate key findings with additional sources before making business decisions.

**Confidence labels — every conclusion or recommendation must be tagged with one of:**
**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

**Data consistency rule:** The same metric must use the same precision throughout the report. Do NOT use "10K+" in one table and "47,000" in another for the same product. Pick one level of precision and apply it consistently across all sections.

**Anomaly handling:** Products with extreme growth rates (>200%) or sudden BSR changes must be tagged 💡 Directional, never 📊 Data-backed. Do NOT claim "proves innovation works" or "confirms market opportunity" based on a single product's spike. State: "Product X showed [metric], which MAY indicate [hypothesis]. Further validation needed."

Report sections (all required, omit any with no data):
1. **Price Signal** — RAISE / HOLD / LOWER with confidence level and one-line reasoning
2. **Current Position** — Your price vs market avg, vs median, vs competitors, which band you are in
3. **Price Band Heatmap** — 5 bands with SKU count, sales share, brand count, opportunity index. Your position highlighted
4. **Competitor Price Map** — Top 10 competitors: price, sales, rating, BuyBox status. Price clusters identified
5. **30-Day Price Trend** — Your price vs top 4 competitors over time. BSR correlation with price changes
6. **Brand Pricing Patterns** — Top brands' price ranges and sampleProducts pricing strategy
7. **Profit Simulation** — 3 scenarios table: price, est. sales, revenue, fees, margin
8. **BuyBox Analysis** — Current BuyBox winner, fulfillment method, price vs your price
9. **Price-Quality Correlation** — Review sentiment at different price points
10. **Recommended Price** — Specific number with reasoning, expected impact on sales/BSR

**Actionable specificity:** If user provided COGS/cost data, calculate and present: break-even units, estimated monthly profit at target price, and timeline to recover initial investment. If COGS not provided, prompt: "Provide your product cost (COGS) for detailed profit simulation."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
11. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
12. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## API Budget: ~20-25 credits

| Step | Calls | Credits |
|------|-------|---------|
| 1 Current snapshot | realtime/product | 1 |
| 2 Price bands | overview + detail | 2 |
| 3 Competitor landscape | categories + products + competitors | 3 |
| 4 Market benchmarks | market + brand-overview + brand-detail | 3 |
| 5 Historical trends | product-history | 1 |
| 6 Realtime competitors | realtime/product × 5 | 5 |
| 7 Review context | reviews/analyze × 2 | 2 |
| 8 Price drill-down | products | 1 |
| Buffer | additional lookups | 2-7 |
| **Total** | | **20-25** |

## Important Notes

- **Never show empty data rows** — omit dimensions with no data
- **Never expose internal errors** — silently fall back to alternative data
- **FORBIDDEN in output**: "fallback", "degraded", "API error", "500", "failed", "insufficient reviews"
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
- FBA fees from products/search are estimates; recommend user verify with Amazon FBA calculator
- Price sensitivity varies by category; use BSR-price correlation from history to quantify
- Seasonal pricing patterns (detected via history) should be flagged in recommendations
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- If user provides COGS, use exact numbers; otherwise estimate from profitMargin field
