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
- Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/api-keys) (1,000 free credits on signup, no credit card required)
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

### Step 1 — Competitor Discovery (2 calls)

```bash
# 1a. Find competitors by keyword (top 20 by sales)
python3 scripts/apiclaw.py competitors --keyword "{keyword}" --category "{categoryPath}" --page-size 20

# 1b. Also search products for broader coverage
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20
```

If competitors endpoint returns empty results, rely on products/search sorted by sales as the primary competitor discovery source.

Merge and deduplicate. Identify Top 10 competitors by sales. If user provided specific ASINs, include those. Always include user's own ASIN as reference point.

### Step 2 — Market Context (4 calls, same keyword)

```bash
# 2a. Category discovery
python3 scripts/apiclaw.py categories --keyword "{keyword}"

# 2b. Market metrics
python3 scripts/apiclaw.py market --category "{categoryPath}" --topn 10

# 2c. Brand overview
python3 scripts/apiclaw.py brand-overview --keyword "{keyword}" --category "{categoryPath}"

# 2d. Brand detail — see where each competitor brand ranks (includes sampleProducts)
python3 scripts/apiclaw.py brand-detail --keyword "{keyword}" --category "{categoryPath}"
```

Use sampleProducts from brand-detail to get each competitor brand's full product lineup within this category. This reveals their product strategy (single SKU vs multi-SKU, price spread, variant approach).

**Category validation:** Cross-check sampleProducts' categoryPath against the target product category. Exclude brands whose products are primarily in unrelated categories (e.g. a flip-flop brand appearing for "yoga mat" keyword due to title keyword stuffing).

### Step 3 — Price Landscape (2 calls)

```bash
python3 scripts/apiclaw.py price-band-overview --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py price-band-detail --keyword "{keyword}" --category "{categoryPath}"
```

Map each competitor's price to a band. Identify who is in the hottest band vs opportunity band.

### Step 4 — Deep Realtime Analysis for Top 10 (10 calls)

```bash
python3 scripts/apiclaw.py product --asin {comp1}
python3 scripts/apiclaw.py product --asin {comp2}
# ... through {comp10}
```

Use the **parentAsin** field from products/search results (if available) instead of the variant ASIN for realtime lookups — variant ASINs often return null data.

For each: extract title strategy, bullet point approach, image count/quality, A+ status, BSR, BuyBox price, rating breakdown, top reviews.

Cross-validate realtime price/rating/BSR against Step 1 database data. Note discrepancies.

**DB + Realtime cross-reference principle:** Database data (products/search) provides broad quantitative metrics with ~T+1 delay. Realtime data (realtime/product) provides current qualitative content. Always compare both — discrepancies reveal promotions, listing changes, or data lag. Flag differences explicitly in the report (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

### Step 5 — Historical Trend Comparison (1 call)

```bash
python3 scripts/apiclaw.py product-history --asins "{comp1},{comp2},...,{comp10}" --start-date "{30d_ago}" --end-date "{today}"
```

**⚠️ Fallback for empty history data:** If product-history returns empty data (count=0) for some ASINs:
1. **Try different ASINs** — newer products or variant ASINs may not have history coverage. Pick ASINs with the oldest `listingDate` from earlier steps.
2. **Try up to 3 rounds** of different ASIN combinations before giving up.
3. If ALL ASINs return empty, use BSR snapshots from DB data + realtime data to infer directional trends. Tag as 🔍 Inferred.
4. **Never report "no trend data available" without trying at least 5 different ASINs.**

For each competitor: price trend, BSR trend, sales trend. Who is rising? Who is falling?

**Quantify trends, don't just label them.** Instead of "price stable" or "BSR rising", calculate and report:
- Price change rate: (latest - earliest) / earliest × 100%
- BSR volatility: (max - min) / average × 100%
- Sales trend direction: regression slope over the period
Use these numbers to support trend labels.

### Step 6 — Review Intelligence (5-8 calls)

**⚠️ labelType only accepts ONE value per call — do NOT comma-separate multiple types.**

**Priority 1 — ASIN mode (try this first):**
```bash
# Analyze top 5 competitors individually — each ASIN must have ratingCount ≥ 50
python3 scripts/apiclaw.py analyze --asin {comp1}
python3 scripts/apiclaw.py analyze --asin {comp2}
python3 scripts/apiclaw.py analyze --asin {comp3}
python3 scripts/apiclaw.py analyze --asin {comp4}
python3 scripts/apiclaw.py analyze --asin {comp5}
```
⚠️ Each ASIN must have ratingCount ≥ 50 (check from Step 1/4 data). If an ASIN has <50 reviews, pick a different competitor with more reviews.

**Priority 2 — Category mode fallback (ONLY if ASIN mode fails for most competitors):**
```bash
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type painPoints
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type buyingFactors
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type improvements
```

**Priority 3 — Realtime topReviews (ONLY if both ASIN AND category modes fail):**
- Extract pain points, buying factors, and sentiment from the topReviews text from Step 4 realtime/product data
- Tag all insights as 💡 Directional — this is the weakest data source

**⚠️ FORBIDDEN: Skipping directly to Priority 3 without attempting Priority 1 and 2.**

**Always report pain points with proportion.** Do NOT say "Top pain point: durability issues". Instead: "Top pain point: durability issues — mentioned in 27/471 reviews (5.7%), avg rating 2.4 when mentioned." Raw count + total sample + percentage = credibility.

**Analyze each competitor independently.** Do NOT combine multiple competitor ASINs in a single analyze call. Each competitor must be analyzed separately so pain points, buying factors, and user profiles can be compared side-by-side. Mixed-ASIN analysis produces averaged insights that hide competitive differences.

### Step 7 — Brand Drill-Down (2 calls)

For the top competitor brand from Step 2 (cross-validate sampleProducts from Step 2d):
```bash
# Cross-validate brand product list from sampleProducts with direct search
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --include-brands "{topCompBrand}" --page-size 20

# And for user's brand (if provided)
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --include-brands "{userBrand}" --page-size 20
```

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

**Confidence labels — every conclusion or recommendation must be tagged with one of:**
**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

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

- Cross-validate database vs realtime data. When prices differ, note "Database: $X, Realtime: $Y (likely promotion)" 
- **Never show empty data rows** — omit competitors/dimensions with no data entirely
- **Never expose internal errors to users** — silently fall back to alternative data sources
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
- If user provides their own ASIN, always include it in comparisons as the reference point
- reviews/analyze needs 50+ reviews; for low-review competitors, use topReviews from realtime
- Brand drill-down keyword must match original search keyword (condition consistency)
