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
- Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/api-keys) (1,000 free credits on signup, no credit card required)
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

Once a precise categoryPath is confirmed, use it as the primary filter for all subsequent API calls:
- `markets/search` → use `--category "{categoryPath}"`
- `products/search` → add `--category "{categoryPath}"` alongside keyword
- For endpoints that only accept keyword (brand-overview, brand-detail, price-band), apply **post-retrieval category validation**: check each returned product's/brand's sampleProducts categoryPath against the target category. Exclude mismatches silently.

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

### Step 1 — Multi-Mode Product Scan (25+ calls, 500+ raw products)

Run products/search with 3-5 modes matching user profile. **Paginate each mode 5 pages** to ensure 100 products per mode:

```bash
# For each mode, paginate 5 pages:
python3 scripts/apiclaw.py products --keyword "{keyword}" --mode {mode1} --page-size 20 --page 1
python3 scripts/apiclaw.py products --keyword "{keyword}" --mode {mode1} --page-size 20 --page 2
python3 scripts/apiclaw.py products --keyword "{keyword}" --mode {mode1} --page-size 20 --page 3
python3 scripts/apiclaw.py products --keyword "{keyword}" --mode {mode1} --page-size 20 --page 4
python3 scripts/apiclaw.py products --keyword "{keyword}" --mode {mode1} --page-size 20 --page 5
# Repeat for mode2, mode3, mode4, mode5
```

If user gave a category instead of keyword, use `--category` param.

**Workaround for reviewCount filter bug (API-56):** For modes that depend on `reviewCountMax` (high-demand-low-barrier, broad-catalog), the API filter is currently broken. Instead of relying on the filter, use a sorting workaround:
```bash
# Sort by reviewCount ascending + filter by sales — first page = lowest reviews with real sales
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --sales-min 300 --sort ratingCount --order asc --page-size 20
```
This returns "low review + high sales" products directly, without needing the broken reviewCountMax filter. More efficient than client-side filtering (no wasted API results).

Deduplicate results by ASIN across all modes.

### Step 2 — Market Context for Each Candidate Category (2+ calls)

For each unique category found in Step 1 results:

```bash
python3 scripts/apiclaw.py market --category "{categoryPath}" --topn 10
```

Also get category-level brand landscape:
```bash
python3 scripts/apiclaw.py brand-overview --keyword "{keyword}"
python3 scripts/apiclaw.py brand-detail --keyword "{keyword}"
```

Use sampleProducts from brand-detail to assess brand depth — if a brand has only 1 product in top 100, it is not deeply invested in this category (higher opportunity for new entrants).

### Step 3 — Price Opportunity Analysis (2 calls)

```bash
python3 scripts/apiclaw.py price-band-overview --keyword "{keyword}"
python3 scripts/apiclaw.py price-band-detail --keyword "{keyword}"
```

Use sampleOpportunityIndex to boost/penalize candidates by price positioning.

### Step 4 — Realtime Validation for Top 10 Candidates (10 calls)

```bash
python3 scripts/apiclaw.py product --asin {candidate1}
python3 scripts/apiclaw.py product --asin {candidate2}
# ... top 10 candidates
```

Cross-validate database data vs realtime. Flag significant discrepancies.

**DB + Realtime cross-reference principle:** Database data (products/search) provides broad quantitative metrics with ~T+1 delay. Realtime data (realtime/product) provides current qualitative content. Always compare both — discrepancies reveal promotions, listing changes, or data lag. Flag differences explicitly in the report (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

### Step 5 — Trend Check for Top 5 (1 call)

```bash
python3 scripts/apiclaw.py product-history --asins "{top1},{top2},{top3},{top4},{top5}" --start-date "{30d_ago}" --end-date "{today}"
```

Determine if each candidate is rising, stable, or declining.

**Category-level growth validation:** A single product's high growth rate (e.g. +900%) may be seasonal rebound, restock recovery, or promotion spike — not a market trend. To validate category-level growth:
- Check if the MAJORITY of products in the category show positive growth (not just 1-2 outliers)
- Cross-reference with market data: is the category's total SKU count and total sales volume growing?
- Flag seasonal patterns explicitly: "This growth coincides with [season], which may be temporary"
- Mark single-product growth signals as 💡 **Directional** / **方向参考**, not 📊 **Data-backed** / **数据验证**

### Step 6 — Consumer Insights for Top 3 (1-3 calls)

```bash
python3 scripts/apiclaw.py analyze --asin {top1}
python3 scripts/apiclaw.py analyze --asin {top2}
python3 scripts/apiclaw.py analyze --asin {top3}
```

Extract pain points and differentiation opportunities.

If reviews/analyze returns INSUFFICIENT_REVIEWS (common for new/emerging candidates with <50 reviews), fall back to topReviews from Step 4 realtime/product data:
- Extract pain points, buying factors, and sentiment from the topReviews text
- Use ratingBreakdown (star distribution) to gauge satisfaction patterns
- This ensures consumer insights are available even for low-review opportunity candidates

### Step 7 — Competitor Density Check (1+ calls)

Use the **specific niche keyword** of the top candidate, not the broad category keyword. For example, if the top candidate is dog grooming scissors, use "dog grooming scissors" not "pet supplies":

```bash
python3 scripts/apiclaw.py competitors --keyword "{top_candidate_niche_keyword}" --page-size 20
```

If competitor-lookup fails (broad keywords often return empty), narrow to the top candidate's subcategory or product type and retry.

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

**Confidence labels — every conclusion or recommendation must be tagged with one of:**
**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

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
