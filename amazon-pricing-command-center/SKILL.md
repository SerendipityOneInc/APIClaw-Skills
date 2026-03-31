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
- Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) (1,000 free credits on signup, no credit card required)
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

Once a precise categoryPath is confirmed, use it as the primary filter for **ALL** subsequent keyword-based list/stats API calls:
- `products/search` → add `--category "{categoryPath}"`
- `brand-overview` → add `--category "{categoryPath}"`
- `brand-detail` → add `--category "{categoryPath}"`
- `price-band-overview` → add `--category "{categoryPath}"`
- `price-band-detail` → add `--category "{categoryPath}"`
- `competitors` → add `--category "{categoryPath}"`
- `markets/search` → use `--category "{categoryPath}"`

**⚠️ CRITICAL: All keyword-based list/stats endpoints MUST include --category when categoryPath is locked.** Without it, keyword-only queries return cross-category contamination. ASIN-specific endpoints (realtime/product, product-history, reviews/analyze by ASIN) do NOT need --category.

Record in the final report's Data Provenance section: the final categoryPath used, how it was resolved, and how many results were filtered out.

### Pre-Execution Checklist

Before proceeding to data collection, verify:
- ✓ `APICLAW_API_KEY` is set and valid
- ✓ categoryPath is locked (from Step 0.5)
- ✓ All required inputs collected (from Step 0)
If any check fails, stop and resolve before continuing.

### Step 1 — Automated Data Collection (ONE command)

Run the `pricing-analysis` composite command to automatically collect ALL data:

```bash
python3 scripts/apiclaw.py pricing-analysis --my-asin "{my_asin}" --keyword "{keyword}" --category "{categoryPath}" > /tmp/pricing-analysis-data.json 2> /tmp/pricing-analysis-log.txt
```

This single command automatically executes:
- **Price snapshot**: realtime/product for your ASIN
- **Price bands**: price-band-overview + price-band-detail
- **Competitor landscape**: products/search + competitor-lookup
- **Market benchmarks**: markets/search + brand-overview + brand-detail
- **Historical trends**: product-history (your ASIN + top 4 competitors, 30 days)
- **Competitor deep-dive**: realtime/product × Top 5 competitors
- **Review context**: reviews/analyze (ASIN mode first, category fallback)
- **Price drill-down**: products/search in best opportunity price band

**Total: all relevant endpoints, fully automated with fallback logic.**

After running, check the log:
```bash
cat /tmp/pricing-analysis-log.txt
```

Then load data for analysis:
```bash
cat /tmp/pricing-analysis-data.json
```

**⚠️ JSON is large (~300-700KB). Use targeted extraction, not full file read.**

### Step 2 — Analysis & Report
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

**Confidence labels — EVERY conclusion, data point, and recommendation MUST be tagged with exactly one of:**
- 📊 **Data-backed** / **数据验证** — Direct API data (numbers, metrics, rankings)
- 🔍 **Inferred** / **合理推断** — Logical reasoning based on data (comparisons, cause-effect, pattern recognition)
- 💡 **Directional** / **方向参考** — Suggestions, hypotheses, predictions (entry strategy, pricing advice, budget estimates)

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

**⚠️ Tagging rules (MANDATORY — do NOT over-use 📊):**

| Content Type | Correct Tag | Examples |
|-------------|------------|---------|
| Raw API metrics | 📊 | CR10=73.4%, FBA率=98%, 月销=2000, 新品率=14% |
| Rankings and lists from API | 📊 | Top 10 品牌表, 价格带数据, 评论痛点排名 |
| Comparisons and patterns | 🔍 | "无大牌壁垒", "市场在扩张", "评论壁垒低" |
| Cause-effect reasoning | 🔍 | "头部做促销说明市场在增长", "新品率高意味着进入机会大" |
| Cross-data validation conclusions | 🔍 | "DB价格 vs 实时价格差异说明有促销活动" |
| Entry strategy recommendations | 💡 | 建议入场价, 目标月销, 差异化方向 |
| Budget and timeline estimates | 💡 | 启动预算, 投资回收周期 |
| Supply chain and sourcing advice | 💡 | "义乌供应链优势", "供应链成本低" |
| Risk assessment | 🔍 or 💡 | 基于数据的风险=🔍, 泛化假设=💡 |
| Scoring rationale | 📊 + 🔍 | 数字部分=📊, 解释部分=🔍 |

**⚠️ FORBIDDEN: Tagging strategy recommendations or subjective conclusions as 📊 Data-backed. If it involves any interpretation, comparison, or suggestion, it MUST be 🔍 or 💡.**

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

### User Decision Standards (MANDATORY)
**If the user specifies decision criteria (e.g. "CR10 < 50%", "margin > 30%", "monthly sales > 1000"), you MUST:**
1. Explicitly evaluate each criterion against the data
2. If ANY criterion is NOT met, mark as ⚠️ CAUTION or 🔴 AVOID — do NOT override with your own judgment
3. Present the evaluation in a clear pass/fail table before giving your recommendation
4. **FORBIDDEN: Recommending GO when user-defined criteria are not met, regardless of your own analysis**

### Data Field Usage (MANDATORY)
**Always use API-provided fields directly. Do NOT calculate metrics when the API already provides them:**
- Revenue → use `sampleAvgMonthlyRevenue` or `sampleGroupMonthlyRevenue`, **NEVER** calculate as avgPrice × totalSales (overestimates 30-70%)
- Opportunity → use `sampleOpportunityIndex` from price-band endpoints, **NEVER** invent your own formula
- Concentration → use `sampleTop10BrandSalesRate` or `topBrandSalesRate` directly
- Sales → use `atLeastMonthlySales` directly, label as "lower bound estimate"

### Data Provenance (MANDATORY)
**Every key data point MUST be traceable:**
- Reference specific endpoint and parameters for each major finding
- If you performed any manual calculation, show the formula AND the raw API fields used
- **FORBIDDEN: Presenting numbers without indicating which API endpoint they came from**

- **Never show empty data rows** — omit dimensions with no data
- **Never expose internal errors** — silently fall back to alternative data
- **FORBIDDEN in output**: "fallback", "degraded", "API error", "500", "failed", "insufficient reviews"
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
- FBA fees from products/search are estimates; recommend user verify with Amazon FBA calculator
- Price sensitivity varies by category; use BSR-price correlation from history to quantify
- Seasonal pricing patterns (detected via history) should be flagged in recommendations
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- If user provides COGS, use exact numbers; otherwise estimate from profitMargin field
