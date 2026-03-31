---
name: Amazon Opportunity Discoverer
version: 1.0.0
description: >
  Automated product opportunity scanner for Amazon sellers.
  Scans categories using 14 preset selection strategies, validates candidates with
  real-time data, brand analysis, and price structure, then ranks opportunities
  by composite score (1-100). Uses all 11 APIClaw API endpoints.
  Use when user asks about: find products to sell, product opportunity, what should I sell,
  niche discovery, profitable products, selection strategy, product scanner, opportunity scan,
  winning products, untapped niches, product ideas, market gaps.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Opportunity Discoverer

> Tell me your budget and experience level. I will find opportunities for you.
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

### Step 0 — Collect User Profile

Ask the user (one message, allow shorthand answers):
- **Budget**: Low (<$2K) / Medium ($2-10K) / High (>$10K)
- **Experience**: Beginner / Intermediate / Advanced
- **Risk tolerance**: Conservative / Moderate / Aggressive
- **Category preference** (optional): any category or keyword they are interested in
- **Fulfillment preference** (optional): FBA / FBM / either

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: keyword or category + budget + experience level
 💡 Recommended (significantly improves accuracy): risk tolerance, category preference
 📌 Optional: fulfillment preference (FBA/FBM)"

Do NOT proceed until all required inputs are collected.

Map user profile to scan strategy:

| Profile | Primary Modes | Price Range | Max Reviews |
|---------|--------------|-------------|-------------|
| Beginner + Conservative | beginner, long-tail, fbm-friendly | $15-60 | <50 |
| Beginner + Moderate | beginner, emerging, low-price | $10-50 | <100 |
| Intermediate + Moderate | fast-movers, underserved, single-variant | $15-80 | <200 |
| Intermediate + Aggressive | high-demand-low-barrier, speculative | $10-100 | <500 |
| Advanced + Aggressive | fast-movers, speculative, top-bsr | any | any |

**Quick-Scan Mode (~10 credits):** If the user has limited credits or wants a fast exploration, offer a lightweight option:
- Run 2 modes × 1 page each (instead of 5 modes × 5 pages)
- Skip realtime validation (Step 4) and trend check (Step 5)
- Keep brand-overview + price-band-overview for context
- Clearly label the output: "Quick Scan — reduced sample, directional only. Run Full Scan for validated recommendations."

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

### Step 0.75 — Data-Driven Category Selection (when no specific category given)

If the user provides a broad interest (e.g. "home products", "kitchen") instead of a specific niche, do NOT pick categories based on general knowledge. Use market data to select:

```bash
# Scan subcategories across the user's interest area
python3 scripts/apiclaw.py market --keyword "{broad_keyword}" --topn 10 --page-size 20
```

From the returned subcategories, rank by a composite score combining:
- **New SKU rate** (sampleNewSkuRate) > 10% — market is actively expanding
- **Brand concentration** (topBrandSalesRate) < 60% — not monopolized
- **FBA rate** > 50% — logistics standardized, suitable for sellers
- **Average price** $10-$50 — reasonable profit margin range
- **Average monthly sales** > 200 — real demand exists

Select Top 3-5 subcategories that score highest across these dimensions. Use their categoryPaths for the multi-mode scan in Step 1.

This replaces "pick 3 categories from experience" with "let data tell you which categories are worth scanning."

### Pre-Execution Checklist

Before proceeding to data collection, verify:
- ✓ `APICLAW_API_KEY` is set and valid
- ✓ categoryPath is locked (from Step 0.5)
- ✓ All required inputs collected (from Step 0)
If any check fails, stop and resolve before continuing.

### Step 1 — Automated Data Collection (ONE command)

Run the `opportunity-scan` composite command to automatically collect ALL data:

**Two scanning approaches — choose based on user needs:**

**Approach A — Preset Modes** (user says "find me blue ocean products"):
```bash
python3 scripts/apiclaw.py opportunity-scan --keyword "{keyword}" --category "{categoryPath}" --modes "beginner,emerging,underserved" > /tmp/opportunity-scan-data.json 2> /tmp/opportunity-scan-log.txt
```

**Approach B — Custom Filters** (user has specific criteria like "月销300+、评论<100、$15-35"):
```bash
python3 scripts/apiclaw.py opportunity-scan --keyword "{keyword}" --category "{categoryPath}" --sales-min 300 --ratings-max 100 --price-min 15 --price-max 35 --rating-max 4.3 > /tmp/opportunity-scan-data.json 2> /tmp/opportunity-scan-log.txt
```

**Approach C — Combined** (preset modes + custom overrides):
```bash
python3 scripts/apiclaw.py opportunity-scan --keyword "{keyword}" --category "{categoryPath}" --modes "high-demand-low-barrier,emerging" --price-min 15 --price-max 35 > /tmp/opportunity-scan-data.json 2> /tmp/opportunity-scan-log.txt
```

**⚠️ IMPORTANT: Always translate user's criteria into the corresponding filter params:**

| User Says | Param |
|-----------|-------|
| "月销300+" / "at least 300 sales" | `--sales-min 300` |
| "评论不超过100" / "less than 100 reviews" | `--ratings-max 100` |
| "价格$15-35" / "between $15 and $35" | `--price-min 15 --price-max 35` |
| "评分4.3以下" / "rating below 4.3" | `--rating-max 4.3` |
| "找蓝海" (no specific criteria) | Use default modes: beginner,emerging,underserved |

**If user provides specific numeric criteria, ALWAYS use custom filters (Approach B/C).** Do NOT ignore user criteria and use default modes instead.

This single command automatically executes:
- **Product scan**: products/search × 5 pages per mode/filter (up to 100 products per scan)
- **Market context**: markets/search + brand-overview + brand-detail
- **Price opportunity**: price-band-overview + price-band-detail
- **Realtime validation**: realtime/product × Top 10 candidates (deduplicated)
- **Trend check**: product-history for Top 5
- **Consumer insights**: reviews/analyze × 3 labelTypes (category mode first)

Optional: `--modes "fast-movers,long-tail,high-demand-low-barrier"` to customize scan modes.

**⚠️ IMPORTANT: Each mode has built-in filter parameters that stack with user-specified filters:**

| Mode | Built-in Params | Effect |
|------|----------------|--------|
| beginner | priceMin:15, priceMax:60, excludeKeywords:long-list | Only -60 products |
| fast-movers | monthlySalesMin:300, salesGrowthRateMin:0.1 | High-velocity products |
| emerging | monthlySalesMax:600, salesGrowthRateMin:0.1, listingAge:180 | New trending products |
| high-demand-low-barrier | monthlySalesMin:300, ratingCountMax:50, listingAge:180 | High sales + few reviews |
| long-tail | bsrMin:10000, bsrMax:50000, priceMax:30, sellerCountMax:1, monthlySalesMax:300 | Niche long-tail |
| underserved | monthlySalesMin:300, ratingMax:3.7, listingAge:180 | Low-rated but selling |
| new-release | monthlySalesMax:500, badges:New Release | Newly launched |
| fbm-friendly | monthlySalesMin:300, fulfillment:FBM, listingAge:180 | FBM-suitable |

**When user specifies additional price/sales filters, they STACK with mode defaults.** Example: user says "-25" + mode=beginner (priceMin:15) → actual range is -25, NOT -25. Always report the ACTUAL search range in the output.

**Total: all relevant endpoints, fully automated with fallback logic.**

After running, check the log:
```bash
cat /tmp/opportunity-scan-log.txt
```

Then load data for analysis:
```bash
cat /tmp/opportunity-scan-data.json
```

**⚠️ JSON is large (~300-700KB). Use targeted extraction, not full file read.**

### Step 2 — Analysis & Report
### Step 8 — Score, Rank & Present

Score each candidate using the framework below. Rank by composite score. Present Top 10.

## Scoring Framework (per candidate, 1-100)

> Based on industry research. See `../scoring-methodology.md` for rationale.

| Dimension | Weight | Good | Medium | Warning |
|-----------|--------|------|--------|---------|
| Demand Signal | 20% | sales>300/mo, revenue>$5K | 100-300 | <100 |
| Competition Gap | 20% | reviews<200, CR10<40% | 200-1K, 40-60% | >1K, >60% |
| Price Opportunity | 15% | in best opportunity band, opp>1.0 | opp 0.5-1.0 | <0.5 |
| Trend Momentum | 15% | BSR rising, sales growing | stable | declining |
| Profit Margin | 15% | >30% margin | 15-30% | <15% |
| Differentiation | 10% | clear pain points, few A+ listings | some gaps | no gaps |
| Profile Fit | 5% | matches user's budget/experience/risk | partial match | mismatch |

### Opportunity Tiers

**Scoring transparency:** In the Scoring Breakdown table, add a "Basis" column explaining WHY each dimension received its score. Example: "Competition: 45/100 — CR10=49.3% falls in 'Medium' range (40-60%), plus 106K review barrier on #1 competitor."

| Score | Tier | Label |
|-------|------|-------|
| 80-100 | S | Hot Opportunity — act fast |
| 60-79 | A | Strong Opportunity — worth pursuing |
| 40-59 | B | Moderate — needs differentiation |
| 0-39 | C | Weak — skip unless you have an edge |

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
1. **Scan Summary** — Modes used, products scanned, categories covered, user profile
2. **Top 10 Opportunities Table** — Rank, ASIN, title, price, monthly sales, rating, reviews, score, tier, key insight
3. **Detailed Analysis (Top 3)** — For each: market context, brand landscape, price positioning, trend, consumer insights, why it scored high
4. **Category Heatmap** — Which categories had the most opportunities and why
5. **Risk Alerts** — Flagged items (declining trend, thin margins, seasonal, brand-dominated)
6. **Recommended Next Steps** — Per-tier action plan (S: buy sample now, A: deep-dive, B: watch list)

**Actionable specificity:** If user provided COGS/cost data, calculate and present: break-even units, estimated monthly profit at target price, and timeline to recover initial investment. If COGS not provided, prompt: "Provide your product cost (COGS) for detailed profit simulation."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
7. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
8. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## API Budget: ~50-60 credits

| Step | Calls | Credits |
|------|-------|---------|
| 1 Multi-mode scan | products/search × 5 modes × 5 pages | 25 |
| 2 Market context | market + brand-overview + brand-detail | 3+ |
| 3 Price analysis | price-band-overview + detail | 2 |
| 4 Realtime validation | realtime/product × 10 | 10 |
| 5 Trend check | product-history | 1 |
| 6 Consumer insights | reviews/analyze × 3 | 3 |
| 7 Competitor check | competitors | 1 |
| 8 Category discovery | categories | 1 |
| Buffer for drill-downs | brand-products, price-drill | 4+ |
| **Total** | | **50-60** |

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

- Deduplicate ASINs across modes — same product may appear in multiple scans
- Sample sizes differ: market (top 100 by category), price-band/brand (~top 100 per subcategory)
- Monthly sales are lower bound estimates
- reviews/analyze needs 50+ reviews; skip for low-review candidates
- Seasonal products should be flagged, not automatically excluded
- Profile mapping is a guide, not rigid — override if data shows better options outside profile
- **Never show empty data rows** — if a category/ASIN has no data, omit it entirely from the output. Do not display "—" or "N/A" rows.
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- **Never expose internal errors to users** — if an API call fails, silently fall back to alternative data sources (e.g. use realtime topReviews instead of reviews/analyze). The user should see complete, professional output without knowing which calls failed.
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
