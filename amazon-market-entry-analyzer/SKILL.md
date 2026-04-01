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

# APIClaw — Amazon Market Entry Analyzer

> One input. Complete market viability assessment. GO / CAUTION / AVOID.
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
| `SKILL.md` (this file) | Always — execution flow + evaluation criteria |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/reference.md` | Need exact field names or response structure |

## Execution Flow

### Step 0 — Parse Input

Extract from user message:
- **keyword** (required): product keyword or niche (e.g. "yoga mat", "wireless earbuds")
- **category** (optional): Amazon category path
- **marketplace** (optional): default US

If only a vague idea given (e.g. "pet products"), ask one clarifying question to narrow scope.

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: keyword or categoryPath
 💡 Recommended (significantly improves accuracy): marketplace
 📌 Optional: (none)"

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

Once a precise categoryPath is confirmed, use it as the primary filter for **ALL** subsequent API calls:
- `markets/search` → use `--category "{categoryPath}"`
- `products/search` → add `--category "{categoryPath}"` alongside keyword
- `brand-overview` → add `--category "{categoryPath}"` alongside keyword
- `brand-detail` → add `--category "{categoryPath}"` alongside keyword
- `price-band-overview` → add `--category "{categoryPath}"` alongside keyword
- `price-band-detail` → add `--category "{categoryPath}"` alongside keyword
- `competitors` → add `--category "{categoryPath}"` alongside keyword

**⚠️ CRITICAL: EVERY endpoint that accepts --category MUST include it.** Without category filtering, keyword-only queries will return cross-category contamination (e.g. "liquid foundation" returns foundation brushes/sponges alongside actual liquid foundation products). This corrupts brand concentration, price structure, and all derived metrics.

Record in the final report's Data Provenance section: the final categoryPath used, how it was resolved, and how many results were filtered out.

### Pre-Execution Checklist

Before proceeding to data collection, verify:
- ✓ `APICLAW_API_KEY` is set and valid
- ✓ categoryPath is locked (from Step 0.5)
- ✓ All required inputs collected (from Step 0)
If any check fails, stop and resolve before continuing.

### Step 1 — Automated Data Collection (ONE command)

Run the `market-entry` composite command to automatically collect ALL data:

```bash
python3 scripts/apiclaw.py market-entry --keyword "{keyword}" --category "{categoryPath}" > /tmp/market-entry-data.json 2> /tmp/market-entry-log.txt
```

This single command automatically executes:
- **Market landscape**: markets/search + brand-overview + brand-detail (with keyword+category fallback to category-only)
- **Price structure**: price-band-overview + price-band-detail
- **Product supply**: products/search × 5 pages (100 records)
- **Competitors**: competitor-lookup + realtime/product × Top 5 (deduplicated by parentAsin)
- **Trends**: product-history × Top 3 (with automatic ASIN retry if empty)
- **Consumer insights**: reviews/analyze × 3 labelTypes (category mode first, ASIN fallback)

**Total: ~20 API calls, all 11 endpoints, fully automated with fallback logic.**

After running, check the log for completion status:
```bash
cat /tmp/market-entry-log.txt
```

Expected output:
```
✅ Market entry analysis complete!
   Steps: market_landscape, price_structure, product_supply, competitor_deepdive, trend_analysis, consumer_insights
   Products: 100 | Realtime: 5 | History: N
   Reviews mode: category
```

If any step shows ⚠️ warnings, note them for the Data Provenance section.

Then load the data JSON for analysis:
```bash
cat /tmp/market-entry-data.json
```

**⚠️ The JSON output is large (~500-700KB). Do NOT read the entire file into context.** Instead, use targeted extraction:
```bash
# Extract key metrics
python3 -c "
import json
with open('/tmp/market-entry-data.json') as f:
    d = json.load(f)
# Access specific sections: d['market'], d['brand_overview'], d['brand_detail'],
# d['price_band_overview'], d['price_band_detail'], d['products'],
# d['competitors'], d['realtime'], d['product_history'], d['reviews']
"
```

### Data Analysis Guidelines

When analyzing the collected data:

**DB + Realtime cross-reference:** Compare products data (DB, ~T+1 delay) with realtime data. Flag discrepancies explicitly (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

**Trend quantification:** Don't just label trends. Calculate:
- Price change rate: (latest - earliest) / earliest × 100%
- BSR volatility: (max - min) / average × 100%

**Pain points with proportion:** "Top pain point: durability issues — mentioned in 27/471 reviews (5.7%), avg rating 2.4 when mentioned."

### Step 2 — Cross-Validate & Score

Cross-validate data across all 11 data sources. When data conflicts, note the discrepancy.

## Scoring Framework

### Market Viability Score (1-100)

> Methodology based on industry research of Jungle Scout, Helium 10, AMZScout, SmartScout, Viral Launch.
> See `../scoring-methodology.md` for detailed rationale and industry benchmarks.

| Dimension | Weight | Source Endpoints | Good | Medium | Warning |
|-----------|--------|-----------------|------|--------|---------|
| Market Size | 15% | markets/search | >$10M/mo | $5-10M | <$5M |
| Market Trend | 10% | product-history (BSR/sales trend) | Rising | Stable | Declining |
| Competition | 25% | markets + brand-overview + brand-detail + realtime | CR10<40% | 40-60% | >60% |
| Price Opportunity | 15% | price-band-overview + detail | sampleOpportunityIndex>1.0 | 0.5-1.0 | <0.5 |
| New Entrant Space | 10% | markets (newSkuRate) + brand-detail | >15% | 5-15% | <5% |
| Consumer Pain Points | 15% | reviews/analyze | Clear gaps | Some gaps | No gaps |
| Profit Potential | 10% | products (profitMargin, fbaFee) + realtime (buyboxWinner) | >30% margin | 15-30% | <15% |

**Scoring transparency:** In the Scoring Breakdown table, add a "Basis" column explaining WHY each dimension received its score. Example: "Competition: 45/100 — CR10=49.3% falls in 'Medium' range (40-60%), plus 106K review barrier on #1 competitor."

### Final Recommendation

| Score | Signal | Meaning |
|-------|--------|---------|
| 70-100 | ✅ **GO** | Strong opportunity, proceed with product development |
| 40-69 | ⚠️ **CAUTION** | Possible but risky, needs differentiation strategy |
| 0-39 | 🔴 **AVOID** | Too competitive or too small, look elsewhere |

**Output confidence context with every recommendation:**
- State the recommendation with its confidence label (📊/🔍/💡)
- Include: "Based on [X] data points from [Y] endpoints, sample of [Z] products"
- For scores: append "(Confidence: High/Medium/Low — [brief reason])"
- Acknowledge specific data gaps that may affect the conclusion
- End with: "Recommended next step: [specific validation action] before committing resources."

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

Report sections (all required):
1. **📊 Executive Summary** — Score (1-100), GO/CAUTION/AVOID, one-paragraph verdict
2. **📈 Market Overview** — Market value, SKU count, avg sales/price, new product rate
3. **📉 Market Trend** — 30-day BSR/price/sales trend for Top 3, market direction (rising/stable/declining)
4. **🏷️ Brand Landscape** — Brand count, CR10, Top 5 brands table, entry difficulty
5. **💰 Price Structure** — Hottest/opportunity bands, 5-band table, recommended entry price
6. **🏆 Top 5 Competitors** — Side-by-side comparison (with realtime data), strengths/weaknesses
7. **💬 Consumer Insights** — Top 5 pain points, buying factors, differentiation opportunities
8. **📋 Scoring Breakdown** — 7-dimension table with scores and key data points
9. **🎯 Entry Strategy** — Target price, differentiation angle, expected sales, risks

**Actionable specificity:** If user provided COGS/cost data, calculate and present: break-even units, estimated monthly profit at target price, and timeline to recover initial investment. If COGS not provided, prompt: "Provide your product cost (COGS) for detailed profit simulation."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
10. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
11. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## ⚠️ Important Notes

### User Decision Standards (MANDATORY)
**If the user specifies decision criteria (e.g. "CR10 < 50%", "margin > 30%", "monthly sales > 1000"), you MUST:**
1. Explicitly evaluate each criterion against the data
2. If ANY criterion is NOT met, mark as ⚠️ CAUTION or 🔴 AVOID — do NOT override with your own judgment
3. Present the evaluation in a clear pass/fail table before giving your recommendation
4. **FORBIDDEN: Recommending GO when user-defined criteria are not met, regardless of your own analysis**

### Data Field Usage (MANDATORY)
**Always use API-provided fields directly. Do NOT calculate metrics when the API already provides them:**
- Revenue → use `sampleAvgMonthlyRevenue` or `sampleGroupMonthlyRevenue`, **NEVER** calculate as avgPrice × totalSales (this systematically overestimates by 30-70%)
- Opportunity → use `sampleOpportunityIndex` from price-band endpoints, **NEVER** invent your own formula
- Concentration → use `sampleTop10BrandSalesRate` (brand-overview) or `topBrandSalesRate` (markets/search) directly
- Sales → use `atLeastMonthlySales` directly, label as "lower bound estimate"

### Data Provenance (MANDATORY)
**Every key data point in the report MUST be traceable:**
- The composite command's JSON output contains `_query` fields recording exact API calls and parameters
- In the Data Provenance section, reference the specific endpoint and parameters for each major finding
- If you performed any manual calculation, show the formula AND the raw API fields used
- **FORBIDDEN: Presenting numbers without indicating which API endpoint they came from**

- Monthly sales are **lower bound estimates** — actual may be higher
- Database data has ~T+1 delay
- Concentration metrics depend on topN parameter
- reviews/analyze needs 50+ reviews; fall back to top ASINs if category mode fails
- Always paginate products/search to get 100+ records for reliable analysis
- **Never show empty data rows** — omit categories/ASINs with no data entirely
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- **Never expose internal errors to users** — silently fall back to alternative data sources if an API call fails
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
