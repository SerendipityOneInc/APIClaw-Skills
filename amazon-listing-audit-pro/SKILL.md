---
name: Amazon Listing Audit Pro
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

> 8-dimension health check. Benchmark against leaders. Fix what matters most.
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

## 8 Scoring Dimensions

> Based on Amazon Listing Quality Score methodology + industry best practices.

| # | Dimension | Weight | What is Evaluated |
|---|-----------|--------|-------------------|
| 1 | Title | 15% | Keyword coverage, length (80-200 chars), readability, brand placement |
| 2 | Bullet Points | 15% | Feature coverage, benefit-driven, keyword usage, formatting |
| 3 | Images | 15% | Count (7+ ideal), main image quality, infographics, lifestyle shots |
| 4 | A+ Content | 10% | Present or not, quality, brand story, comparison tables |
| 5 | Reviews & Rating | 15% | Count, avg rating, star distribution, recent review velocity |
| 6 | Keywords | 10% | Title keyword density, bullet keyword coverage vs top competitors |
| 7 | Category Fit | 10% | Correct category placement, BSR relative to category size |
| 8 | Pricing | 10% | vs category avg, vs price band optimal, margin viability |

## Execution Flow

### Step 0 — Parse Input

- **my_asin** (required): ASIN to audit
- **keyword** (required): primary keyword for benchmark context

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: my_asin + keyword
 💡 Recommended: (none)
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

Run the `listing-audit` composite command to automatically collect ALL data:

```bash
python3 scripts/apiclaw.py listing-audit --my-asin "{my_asin}" --keyword "{keyword}" --category "{categoryPath}" > /tmp/listing-audit-data.json 2> /tmp/listing-audit-log.txt
```

This single command automatically executes:
- **Audit target**: realtime/product for your ASIN
- **Category leaders**: products/search + competitor-lookup (Top 20, deduplicated)
- **Benchmark realtime**: realtime/product × Top 5 leaders
- **Market context**: markets/search + brand-overview + brand-detail
- **Price context**: price-band-overview + price-band-detail
- **Review intelligence**: reviews/analyze (ASIN mode first, category fallback)
- **Trend context**: product-history (your ASIN + top 2 leaders, 30 days)

**Total: all relevant endpoints, fully automated with fallback logic.**

After running, check the log:
```bash
cat /tmp/listing-audit-log.txt
```

Then load data for analysis:
```bash
cat /tmp/listing-audit-data.json
```

**⚠️ JSON is large (~300-700KB). Use targeted extraction, not full file read.**

### Step 2 — Analysis & Report
### Step 8 — Score & Report

Score each dimension 0-100. Calculate weighted total. Generate specific improvements.

## Scoring Thresholds

| Dimension | 90-100 (Excellent) | 60-89 (Good) | 30-59 (Needs Work) | 0-29 (Critical) |
|-----------|-------------------|--------------|--------------------|-----------------| 
| Title | 150+ chars, top 3 keywords, brand first | 100-150 chars, 2 keywords | <100 chars or keyword stuffed | Missing key terms |
| Bullets | 5+, benefit-led, keywords in each | 5, features only | 3-4, generic | <3 bullets |
| Images | 7+, infographic+lifestyle | 5-6, decent quality | 3-4, basic | 1-2 images |
| A+ | Rich A+, comparison table, brand story | Basic A+ present | No A+ but has description | No A+, no description |
| Reviews | 1000+, 4.5+, <5% 1-star | 200-1K, 4.0-4.5 | 50-200, 3.5-4.0 | <50 or <3.5 |
| Keywords | Top 5 competitor keywords covered | 3-4 covered | 1-2 covered | None matched |
| Category | Optimal category, top 1% BSR | Good category, top 5% | Suboptimal category | Wrong category |
| Pricing | In opportunity band, margin >25% | In hottest band | Outside top bands | Overpriced or margin <10% |

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

Report sections (all required, omit any with no data):
1. **Overall Score** — X/100 with letter grade (A/B/C/D/F) and one-line verdict
2. **8-Dimension Scorecard** — Table with dimension, score, grade, key finding, vs benchmark avg
3. **Title Audit** — Current title analysis, keyword coverage, suggested rewrite
4. **Bullets Audit** — Current vs leader comparison, missing selling points, suggested rewrites
5. **Image Audit** — Count vs leaders, missing types (infographic/lifestyle/comparison)
6. **Review Health** — Star distribution, sentiment, review velocity trend
7. **Keyword Gap Analysis** — Keywords in leader titles/bullets missing from yours
8. **vs Category Leaders** — Side-by-side comparison table (your listing vs Top 3)
9. **Priority Fix List** — Ranked improvements by expected impact (lowest scores first)

**Actionable specificity:** If user provided COGS/cost data, calculate and present: break-even units, estimated monthly profit at target price, and timeline to recover initial investment. If COGS not provided, prompt: "Provide your product cost (COGS) for detailed profit simulation."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
10. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
11. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## API Budget: ~20-25 credits

| Step | Calls | Credits |
|------|-------|---------|
| 1 Audit target | realtime/product | 1 |
| 2 Category leaders | categories + products + competitors | 3 |
| 3 Benchmark realtime | realtime/product × 5 | 5 |
| 4 Market context | market + brand-overview + brand-detail | 3 |
| 5 Price context | price-band-overview + detail | 2 |
| 6 Review intelligence | reviews/analyze × 2 | 2 |
| 7 Trend context | product-history | 1 |
| Buffer | additional lookups | 3-8 |
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
- For bulk audit (agencies), run Steps 1-8 per ASIN but share Steps 2-5 market data across ASINs
- Keyword gap analysis compares against Top 5 leader titles + bullets, not just one competitor
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- Suggested rewrites should incorporate high-frequency positive review language from Step 6
