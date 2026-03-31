---
name: Amazon Daily Market Radar
version: 1.0.0
description: >
  Automated daily market monitoring and alert system for Amazon sellers.
  Tracks price changes, new competitors, BSR movements, review spikes,
  stock-out signals, and market shifts. Designed for unattended agent automation.
  Uses all 11 APIClaw API endpoints with cross-validation.
  Use when user asks about: daily monitoring, market alerts, track competitors,
  price monitoring, BSR tracking, market changes, daily briefing, market watch,
  competitor alerts, review monitoring, stock alerts, market dashboard,
  daily report, market updates, what changed today.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Daily Market Radar

> Set it. Forget it. Get alerted when it matters.
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
| `SKILL.md` (this file) | Always — execution flow + alert rules |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/reference.md` | Need exact field names or response structure |

## Setup — First Run

On first use, collect the user's watchlist:
- **my_asins**: user's own product ASINs (1-10)
- **competitor_asins**: key competitors to track (up to 20)
- **keywords**: category keywords for market-level monitoring (1-5)
- **alert_preferences**: which alerts matter most (price/BSR/reviews/competitors)

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: my_asins + keyword
 💡 Recommended (significantly improves accuracy): competitor_asins
 📌 Optional: alert_preferences"

Do NOT proceed until all required inputs are collected.

Store the watchlist and each run's snapshot data in a `data/` directory (e.g. `data/watchlist.json`, `data/last-run.json`). On repeat runs, load the previous snapshot for change detection. Without a previous run, first run establishes the baseline — no "new competitor" alerts will fire.

## Execution Flow

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

Run the `daily-radar` composite command to automatically collect ALL monitoring data:

```bash
python3 scripts/apiclaw.py daily-radar --asins "{my_asin_1},{my_asin_2},{comp_1},{comp_2}" --keyword "{keyword}" --category "{categoryPath}" > /tmp/daily-radar-data.json 2> /tmp/daily-radar-log.txt
```

This single command automatically executes:
- **Realtime snapshots** for all tracked ASINs
- **7-day historical comparison** (product-history)
- **Market pulse**: markets/search + brand-overview + brand-detail (with keyword+category fallback)
- **New competitor detection**: products/search top 20
- **Price landscape**: price-band-overview + price-band-detail
- **Review pulse**: reviews/analyze for first tracked ASIN with ≥50 reviews

After running, check the log:
```bash
cat /tmp/daily-radar-log.txt
```

Then load data for analysis:
```bash
cat /tmp/daily-radar-data.json
```

**⚠️ JSON is large (~300-400KB). Use targeted extraction, not full file read.**

### Data Analysis Guidelines

**Change detection:** Compare today's realtime data against product_history:
- Price changes >5% → 🔴 alert
- BSR moves >20% → 🟡 alert
- New ASINs in top 20 not seen before → 🟡 alert

**Trend quantification:** Calculate and report:
- Price change rate: (latest - earliest) / earliest × 100%
- BSR volatility: (max - min) / average × 100%

**Growth signal validation:**
- 📊 Sustained trend — 7+ days consistent direction
- 🔍 Possible signal — 2-3 days of change
- 💡 Single-day spike — could be promotion/restock

### Step 2 — Generate Daily Briefing

**First-run detection:** If `data/last-run.json` does not exist, this is the first run. Output a "Baseline Established" template instead of a change-detection briefing:
- State clearly: "This is the first run — baseline data has been captured. Change detection and alerts will be available starting from the next run."
- Still output the KPI Dashboard (current snapshot) and Market Shifts (current state) sections
- Save current data to `data/last-run.json` for future comparison
- Do NOT generate RED/YELLOW/GREEN alerts (no baseline to compare against)

**Subsequent runs:** Compile all changes into alert-prioritized briefing.

## Alert Rules

| Alert Level | Trigger | Example |
|------------|---------|---------|
| RED | Price drop >10% by competitor | Comp X dropped from $19.99 to $14.99 |
| RED | BSR crash >50% (your product) | Your BSR went from #23 to #60 |
| RED | 1-star review spike (3+ in 24h) | 4 new 1-star reviews detected |
| YELLOW | New competitor in Top 20 | New ASIN B0XXX entered Top 20 |
| YELLOW | Competitor price change 5-10% | Comp Y raised price by 8% |
| YELLOW | BSR change 20-50% | Your BSR moved from #23 to #35 |
| YELLOW | Brand share shift >2% | Brand Z gained 3% market share |
| GREEN | Competitor stock-out detected | Comp W BuyBox shows "Currently unavailable" |
| GREEN | Your review velocity up | 15% more reviews this week vs last |
| GREEN | Price band opportunity shift | New opportunity in $15-$20 band (opp 1.3→1.5) |

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

Daily briefing (all sections, omit any with no alerts):
1. **Alert Summary** — Count of RED/YELLOW/GREEN alerts
2. **RED Alerts** — Immediate action required, with specific recommendations
3. **YELLOW Alerts** — Monitor closely, suggested response if trend continues
4. **GREEN Opportunities** — Positive changes to capitalize on
5. **KPI Dashboard** — Your ASINs: price, BSR, rating, reviews (today vs yesterday)
6. **Competitor Movement** — Price/BSR/review changes for tracked competitors
7. **Market Shifts** — Category-level changes (size, concentration, new entrants)
8. **Action Items** — Prioritized to-do list based on alerts

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
9. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
10. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## API Budget: ~15-30 credits (depends on watchlist size)

| Step | Calls | Credits |
|------|-------|---------|
| 1 Realtime snapshot | realtime/product × (my + comp ASINs) | 5-15 |
| 2 Historical comparison | product-history × 1-2 | 1-2 |
| 3 Market pulse | market + brand-overview + brand-detail | 3 |
| 4 New competitor detection | products/search | 1 |
| 5 Price landscape | price-band-overview + detail | 2 |
| 6 Category context | categories | 1 |
| 7 Review pulse | reviews/analyze × 1-3 | 1-3 |
| **Total** | | **15-30** |

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

- Designed for daily automated runs — no user interaction needed after initial setup
- **Never show empty data rows** — omit alerts with no changes
- **Never expose internal errors** — silently fall back to alternative data
- **FORBIDDEN in output**: "fallback", "degraded", "API error", "500", "failed", "insufficient reviews"
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
- Compare against previous run data when available; first run has no comparison baseline
- Highest retention skill — users come back daily. Keep output concise and actionable
- For agent automation: can be triggered by cron/scheduler with saved watchlist
