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

### Step 1 — Target Identification (1-2 calls)

If keyword given, find top products first:
```bash
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20
```

If category given, also get category context:
```bash
python3 scripts/apiclaw.py categories --keyword "{keyword}"
```

### Step 2 — Full Review Analysis (3-16 calls, core)

**⚠️ labelType only accepts ONE value per call — do NOT comma-separate multiple types.**

**Priority 1 — ASIN mode (try this first):**

For primary ASIN — get ALL 11 dimensions. The target ASIN must have ratingCount ≥ 50 (check from Step 1 data). **Use individual label-type calls:**
```bash
python3 scripts/apiclaw.py analyze --asin {target} --label-type painPoints
python3 scripts/apiclaw.py analyze --asin {target} --label-type positives
python3 scripts/apiclaw.py analyze --asin {target} --label-type buyingFactors
python3 scripts/apiclaw.py analyze --asin {target} --label-type improvements
python3 scripts/apiclaw.py analyze --asin {target} --label-type userProfiles
python3 scripts/apiclaw.py analyze --asin {target} --label-type scenarios
python3 scripts/apiclaw.py analyze --asin {target} --label-type issues
python3 scripts/apiclaw.py analyze --asin {target} --label-type keywords
python3 scripts/apiclaw.py analyze --asin {target} --label-type usageTimes
python3 scripts/apiclaw.py analyze --asin {target} --label-type usageLocations
python3 scripts/apiclaw.py analyze --asin {target} --label-type behaviors
```

Alternatively, call without `--label-type` to get all dimensions in one call (if supported). If it returns no data, fall back to individual calls above.

For competitor ASINs (up to 5) — each must have ratingCount ≥ 50:
```bash
python3 scripts/apiclaw.py analyze --asin {comp1}
python3 scripts/apiclaw.py analyze --asin {comp2}
# ... up to 5 competitors
```

**Priority 2 — Category mode fallback (ONLY if ASIN mode fails):**
```bash
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type painPoints
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type buyingFactors
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type improvements
```

**Priority 3 — Realtime topReviews (ONLY if both ASIN AND category modes fail):**
- Extract pain points, buying factors, and sentiment from the topReviews text from Step 3 realtime/product data
- Use ratingBreakdown (star distribution) to gauge overall satisfaction
- Tag all insights as 💡 Directional — this is the weakest data source

**⚠️ FORBIDDEN: Skipping directly to Priority 3 without attempting Priority 1 and 2. Every report MUST show which priority level was used and why higher priorities failed (if applicable).**

**Always report pain points with proportion.** Do NOT say "Top pain point: durability issues". Instead: "Top pain point: durability issues — mentioned in 27/471 reviews (5.7%), avg rating 2.4 when mentioned." Raw count + total sample + percentage = credibility.

**Important: Analyze each brand/competitor independently.** Do NOT combine multiple ASINs from different brands in a single analyze call. Each brand must be analyzed separately to enable accurate cross-brand comparison of pain points, buying factors, and user profiles. Mixing ASINs produces averaged insights that cannot be attributed to any specific brand.

**If a user-provided competitor ASIN returns INSUFFICIENT_REVIEWS or null data (product doesn't exist):** Auto-select replacement competitors from Step 1 product search results — pick the top 1-2 ASINs that are in the same subcategory but different brand from the target. Re-run analyze + realtime for the replacements. Do not produce a one-sided report without competitor comparison.

### Step 3 — Realtime Product Detail (1-6 calls)

```bash
python3 scripts/apiclaw.py product --asin {target}
python3 scripts/apiclaw.py product --asin {comp1}
# ... for each ASIN being compared
```

Extract: ratingBreakdown (star distribution), topReviews (raw review text), features (current bullets).
**DB + Realtime cross-reference principle:** Database data (products/search) provides broad quantitative metrics with ~T+1 delay. Realtime data (realtime/product) provides current qualitative content. Always compare both — discrepancies reveal promotions, listing changes, or data lag. Flag differences explicitly in the report (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

Cross-validate: AI-analyzed sentiment vs actual star distribution. Specifically: compare positive_sentiment% from reviews/analyze against (4+5 star)% from ratingBreakdown. If the gap exceeds 15%, flag a discrepancy and note possible causes (review manipulation, rating inflation, or sample window difference between 6-month analyze vs all-time ratingBreakdown).

### Step 4 — Market & Competitive Context (4 calls)

```bash
python3 scripts/apiclaw.py market --category "{categoryPath}" --topn 10
python3 scripts/apiclaw.py brand-overview --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py brand-detail --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py competitors --keyword "{keyword}" --category "{categoryPath}" --page-size 20
```

Context: how does this product's review profile compare to category averages? Use sampleProducts from brand-detail to find other products from the same brand for expanded review comparison.

### Step 5 — Price & Trend Context (3 calls)

```bash
python3 scripts/apiclaw.py price-band-overview --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py price-band-detail --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py product-history --asins "{target},{comp1},{comp2}" --start-date "{30d_ago}" --end-date "{today}"
```

**⚠️ Fallback for empty history data:** If product-history returns empty data (count=0) for some ASINs:
1. **Try different ASINs** — newer products or variant ASINs may not have history coverage. Pick ASINs with the oldest `listingDate` from earlier steps.
2. **Try up to 3 rounds** of different ASIN combinations before giving up.
3. If ALL ASINs return empty, use BSR snapshots from DB data + realtime data to infer directional trends. Tag as 🔍 Inferred.
4. **Never report "no trend data available" without trying at least 5 different ASINs.**

Correlate: do price changes affect review sentiment? Is rating trending up or down?

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

**Confidence labels — every conclusion or recommendation must be tagged with one of:**
**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

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

- reviews/analyze needs 50+ reviews for meaningful analysis; use topReviews from realtime as fallback
- **Never show empty data rows** — omit dimensions with no data
- **Never expose internal errors to users** — silently fall back to alternative data
- InsightItem field: `reviewRate` (not `reviewPercentage`) for mention frequency
- Quote actual customer words in Listing Copy Suggestions — these are proven converting phrases
- When comparing competitors, align dimensions (pain points vs pain points) for clear comparison
- Star distribution from ratingBreakdown should cross-validate sentiment from reviews/analyze
- **FORBIDDEN in output**: "fallback", "degraded", "API error", "500", "failed", "insufficient reviews", "interface limitation", "pending recovery". The user must never see any hint of internal API issues.
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
