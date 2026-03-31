---
name: Amazon Review Intelligence Engine
version: 1.0.0
description: >
  Deep consumer insights from 1B+ pre-analyzed Amazon reviews.
  Extracts pain points, buying factors, user profiles, usage patterns,
  and differentiation opportunities across 11 analysis dimensions.
  Compares review sentiment across competitors and generates listing copy suggestions.
  Uses all 11 APIClaw API endpoints with cross-validation.
  Use when user asks about: review analysis, customer feedback, pain points, what customers say,
  review insights, sentiment analysis, consumer insights, product improvements, voice of customer,
  review comparison, negative reviews, customer complaints, buying factors, user profile.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Review Intelligence Engine

> 1B+ reviews pre-analyzed. 11 insight dimensions. 95% token savings vs DIY NLP.
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

## 11 Analysis Dimensions

| Dimension | labelType | What It Reveals |
|-----------|-----------|----------------|
| Pain Points | `painPoints` | What customers hate — product defects, missing features |
| Issues | `issues` | Specific problems reported |
| Positives | `positives` | What customers love — key selling points |
| Improvements | `improvements` | What customers wish was better |
| Buying Factors | `buyingFactors` | Why customers chose this product |
| Keywords | `keywords` | Most mentioned terms in reviews |
| User Profiles | `userProfiles` | Who is buying — demographics, use cases |
| Usage Scenarios | `scenarios` | How and where products are used |
| Usage Times | `usageTimes` | When products are used (seasonal, daily) |
| Usage Locations | `usageLocations` | Where products are used |
| Behaviors | `behaviors` | Post-purchase behavior patterns |

## Execution Flow

### Step 0 — Parse Input

Extract from user message:
- **target_asin** (optional): specific ASIN to analyze
- **competitor_asins** (optional): ASINs for cross-comparison
- **keyword** (optional): find top products to analyze by keyword
- **category** (optional): category-level review analysis

Determine mode: Single ASIN | Multi-ASIN Comparison | Category-wide

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: target_asin or keyword
 💡 Recommended (significantly improves accuracy): competitor_asins
 📌 Optional: category"

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

Run the `review-deepdive` composite command to automatically collect ALL data:

```bash
python3 scripts/apiclaw.py review-deepdive --target-asin "{target_asin}" --keyword "{keyword}" --category "{categoryPath}" > /tmp/review-deepdive-data.json 2> /tmp/review-deepdive-log.txt
```

This single command automatically executes:
- **Target identification**: realtime/product (or auto-discover from keyword)
- **Full review analysis**: reviews/analyze × 11 dimensions for target ASIN
- **Competitor comparison**: reviews/analyze (painPoints + positives) for up to 2 competitors
- **Realtime detail**: realtime/product for competitors
- **Market context**: markets/search + brand-overview + competitor-lookup
- **Price & trend**: price-band-overview + product-history

Optional: add `--comp-asins "{asin1},{asin2}"` for competitor comparison.

**Total: all relevant endpoints, fully automated with fallback logic.**

After running, check the log:
```bash
cat /tmp/review-deepdive-log.txt
```

Then load data for analysis:
```bash
cat /tmp/review-deepdive-data.json
```

**⚠️ JSON is large (~300-700KB). Use targeted extraction, not full file read.**

### Step 2 — Analysis & Report
### Step 6 — Synthesize Insights

Combine review data with market context. Generate actionable recommendations.

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

Report sections (all required, omit any with no data):
1. **Review Snapshot** — Total reviews, avg rating, star distribution, sentiment split, verified purchase rate
2. **Top 10 Pain Points** — Ranked by frequency (count + % of reviews), with avg rating per pain point
3. **Top 10 Positives** — What customers love, ranked by mention frequency
4. **Buying Decision Factors** — Why customers chose this product (ranked)
5. **Improvement Wishlist** — What customers want improved (ranked, with specific quotes)
6. **Consumer Profile** — Who buys: demographics, use cases, experience level
7. **Usage Patterns** — When, where, and how the product is used
8. **Competitor Review Comparison** — Side-by-side: your pain points vs theirs, your positives vs theirs. If competitor review data is unavailable, use brand-detail sampleProducts to compare category-level pain points and positives, and note the limitation
9. **Listing Copy Suggestions** — Bullet points and title keywords derived directly from positive review language
10. **Differentiation Roadmap** — Product improvements ranked by impact (pain point frequency × avg rating delta)

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
11. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
12. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## API Budget: ~20-30 credits

| Step | Calls | Credits |
|------|-------|---------|
| 1 Target identification | products + categories | 2 |
| 2 Review analysis | analyze × 4 (target) + × 5 (competitors) | 9 |
| 3 Realtime detail | realtime/product × 6 | 6 |
| 4 Market context | market + brand-overview + brand-detail + competitors | 4 |
| 5 Price & trend | price-band-overview + detail + history | 3 |
| Buffer | additional lookups | 1-6 |
| **Total** | | **20-30** |

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

- reviews/analyze needs 50+ reviews for meaningful analysis; use topReviews from realtime as fallback
- **Never show empty data rows** — omit dimensions with no data
- **Never expose internal errors to users** — silently fall back to alternative data
- InsightItem field: `reviewRate` (not `reviewPercentage`) for mention frequency
- Quote actual customer words in Listing Copy Suggestions — these are proven converting phrases
- When comparing competitors, align dimensions (pain points vs pain points) for clear comparison
- Star distribution from ratingBreakdown should cross-validate sentiment from reviews/analyze
- **FORBIDDEN in output**: "fallback", "degraded", "API error", "500", "failed", "insufficient reviews", "interface limitation", "pending recovery". The user must never see any hint of internal API issues.
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
