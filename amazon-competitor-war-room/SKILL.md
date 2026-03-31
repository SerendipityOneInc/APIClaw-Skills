---
name: Amazon Competitor War Room
version: 1.0.0
description: >
  Deep competitor intelligence and battle-ready insights for Amazon sellers.
  Side-by-side competitor comparison with pricing maps, review sentiment analysis,
  brand strength ranking, historical trend tracking, and actionable battle strategies.
  Uses all 11 APIClaw API endpoints with cross-validation.
  Use when user asks about: competitor analysis, who are my competitors, competitive landscape,
  competitor tracking, battle card, competitive intelligence, spy on competitors,
  competitor comparison, benchmark against competitors, competitor strengths weaknesses,
  track competitor pricing, competitor review analysis.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Competitor War Room

> Know your enemy. Know yourself. Win every battle.
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
| `SKILL.md` (this file) | Always — execution flow + output spec |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/reference.md` | Need exact field names or response structure |

## Execution Flow

### Step 0 — Parse Input

Extract from user message:
- **my_asin** (optional): user's own product ASIN
- **competitor_asins** (optional): specific competitor ASINs to analyze
- **keyword** (required if no ASINs given): product keyword to discover competitors
- **brand** (optional): specific competitor brand to focus on

If user provides only a keyword, discover competitors automatically. If user provides ASINs, use those directly.

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: keyword or my_asin
 💡 Recommended (significantly improves accuracy): competitor_asins
 📌 Optional: brand"

Do NOT proceed until all required inputs are collected.

**If user provides only ASIN(s) and no keyword:** Derive the keyword using this fallback chain:

1. First try `realtime/product` for the given ASIN:
```bash
python3 scripts/apiclaw.py product --asin {my_asin}
```
2. If realtime returns null (common for variant ASINs), search for the ASIN via products/search:
```bash
python3 scripts/apiclaw.py products --keyword "{my_asin}" --page-size 1
```
3. If still no result, ask the user to provide a keyword.

Extract 2-3 core keywords from the title (e.g. "Apple iPad Air" → "ipad air", "BalanceFrom Yoga Mat" → "yoga mat"). Use the extracted keyword for all subsequent keyword-based API calls.

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

Run the `competitor-analysis` composite command to automatically collect ALL data:

```bash
python3 scripts/apiclaw.py competitor-analysis --keyword "{keyword}" --category "{categoryPath}" > /tmp/competitor-analysis-data.json 2> /tmp/competitor-analysis-log.txt
```

This single command automatically executes:
- **Competitor discovery**: products/search + competitor-lookup
- **Market context**: markets/search + brand-overview + brand-detail
- **Price landscape**: price-band-overview + price-band-detail
- **Realtime deep-dive**: realtime/product × Top 10 competitors (deduplicated)
- **Historical trends**: product-history (your ASIN + top 5, 30 days)
- **Review intelligence**: reviews/analyze per competitor (ASIN mode, category fallback)
- **Brand drill-down**: top brand's product matrix

Optional: add `--my-asin "{my_asin}"` to include your product in comparison.

**Total: all relevant endpoints, fully automated with fallback logic.**

After running, check the log:
```bash
cat /tmp/competitor-analysis-log.txt
```

Then load data for analysis:
```bash
cat /tmp/competitor-analysis-data.json
```

**⚠️ JSON is large (~300-700KB). Use targeted extraction, not full file read.**

### Step 2 — Analysis & Report
### Step 8 — Synthesize Battle Plan

Combine all data. Generate competitive matrix, identify weaknesses, recommend actions.

## Competitive Scoring (per competitor, 1-100)

> Based on industry research. See `../scoring-methodology.md` for rationale.

| Dimension | Weight | Meaning |
|-----------|--------|---------|
| Sales Dominance | 25% | Monthly sales, revenue, market share |
| Brand Strength | 20% | Brand sales rate, SKU count, price range |
| Listing Quality | 20% | Images, bullets, A+, title optimization |
| Customer Satisfaction | 20% | Rating, sentiment, pain point severity |
| Trend Momentum | 15% | BSR direction, sales growth, price stability |

Higher score = stronger competitor = harder to beat.

**Scoring transparency:** In the Scoring Breakdown table, add a "Basis" column explaining WHY each dimension received its score. Example: "Competition: 45/100 — CR10=49.3% falls in 'Medium' range (40-60%), plus 106K review barrier on #1 competitor."

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

Report sections (all required, omit any section with no data):
1. **Battlefield Overview** — Market size, your position vs competitors, key metrics
2. **Competitor Comparison Matrix** — Side-by-side table: price, sales, rating, reviews, BSR, fulfillment, listing quality indicators
3. **Brand Power Ranking** — Each competitor's brand: market share, SKU count, price range, avg rating
4. **Price Positioning Map** — Where each competitor sits in the 5 price bands, who is in opportunity zone
5. **30-Day Trend Report** — Price/BSR/sales trends per competitor, who is rising/falling
6. **Review Battle** — Sentiment comparison, top pain points per competitor, where they are vulnerable
7. **Listing Audit Comparison** — Image count, bullet count, A+ status, title keyword density
8. **Competitive Strength Scores** — Per-competitor score (1-100) with dimension breakdown
9. **Battle Strategy** — Specific actions: pricing moves, listing improvements, review opportunities, differentiation angles

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
10. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
11. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## API Budget: ~28-35 credits

| Step | Calls | Credits |
|------|-------|---------|
| 1 Competitor discovery | competitors + products | 2 |
| 2 Market context | categories + market + brand-overview + brand-detail | 4 |
| 3 Price landscape | price-band-overview + detail | 2 |
| 4 Realtime Top 10 | realtime/product × 10 | 10 |
| 5 Historical trends | product-history | 1 |
| 6 Review intelligence | reviews/analyze × 5 | 5 |
| 7 Brand drill-down | products × 2 | 2 |
| Buffer | additional lookups | 2-9 |
| **Total** | | **28-35** |

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

- Cross-validate database vs realtime data. When prices differ, note "Database: $X, Realtime: $Y (likely promotion)" 
- **Never show empty data rows** — omit competitors/dimensions with no data entirely
- **Never expose internal errors to users** — silently fall back to alternative data sources
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
- If user provides their own ASIN, always include it in comparisons as the reference point
- reviews/analyze needs 50+ reviews; for low-review competitors, use topReviews from realtime
- Brand drill-down keyword must match original search keyword (condition consistency)
