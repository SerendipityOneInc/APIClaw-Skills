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

### Step 1 — Audit Target (1 call)

```bash
python3 scripts/apiclaw.py product --asin {my_asin}
```

If realtime/product returns null fields (common for variant/child ASINs), use `products/search --keyword "{keyword}"` to find the parentAsin, then re-fetch with the parent ASIN.

Extract everything: title, features (bullets), images, description, rating, ratingBreakdown, BSR, BuyBox, categories, variants. This is the listing being audited.

### Step 2 — Category Leaders for Benchmark (3 calls)

```bash
python3 scripts/apiclaw.py categories --keyword "{keyword}"
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20
python3 scripts/apiclaw.py competitors --keyword "{keyword}" --category "{categoryPath}" --page-size 20
```

If competitors endpoint returns empty results, rely on products/search results as the leader pool.

Filter results by categoryPath to exclude irrelevant products (keyword "yoga mat" may return incense or flip-flops). Only benchmark against products in the same subcategory.

If categories returns empty for the specific keyword, try a broader keyword (e.g. "yoga" instead of "yoga mat") or use categoryPath from the target product's realtime data.

Identify Top 5 by sales as benchmark. **Deduplicate by parentAsin** — if multiple results share the same parent (e.g. color variants of the same product), keep only the highest-selling variant. The goal is 5 distinct products from different brands/product lines, not 5 variants of the same listing. These are the "gold standard" listings to compare against.

### Step 3 — Benchmark Realtime (5 calls)

```bash
python3 scripts/apiclaw.py product --asin {leader1}
python3 scripts/apiclaw.py product --asin {leader2}
python3 scripts/apiclaw.py product --asin {leader3}
python3 scripts/apiclaw.py product --asin {leader4}
python3 scripts/apiclaw.py product --asin {leader5}
```

For each: title structure, bullet approach, image count, A+ presence. Build benchmark averages.

**DB + Realtime cross-reference principle:** Database data (products/search) provides broad quantitative metrics with ~T+1 delay. Realtime data (realtime/product) provides current qualitative content. Always compare both — discrepancies reveal promotions, listing changes, or data lag. Flag differences explicitly in the report (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

### Step 4 — Market Context (3 calls)

```bash
python3 scripts/apiclaw.py market --category "{categoryPath}" --topn 10
python3 scripts/apiclaw.py brand-overview --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py brand-detail --keyword "{keyword}" --category "{categoryPath}"
```

Use sampleProducts from brand-detail to see how top brands structure their listings.

### Step 5 — Price Context (2 calls)

```bash
python3 scripts/apiclaw.py price-band-overview --keyword "{keyword}" --category "{categoryPath}"
python3 scripts/apiclaw.py price-band-detail --keyword "{keyword}" --category "{categoryPath}"
```

### Step 6 — Review Intelligence (2-5 calls)

**⚠️ labelType only accepts ONE value per call — do NOT comma-separate multiple types.**

**Priority 1 — ASIN mode (try this first):**
```bash
# my_asin and top_leader must each have ratingCount ≥ 50
python3 scripts/apiclaw.py analyze --asin {my_asin}
python3 scripts/apiclaw.py analyze --asin {top_leader}
```
⚠️ Each ASIN must have ratingCount ≥ 50. If an ASIN has <50 reviews, pick a different leader with more reviews.

**Priority 2 — Category mode fallback (ONLY if ASIN mode fails):**
```bash
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type painPoints
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type buyingFactors
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type improvements
```

**Priority 3 — Realtime topReviews (ONLY if both ASIN AND category modes fail):**
- Extract keywords, pain points, and sentiment from the topReviews text from Step 1/3 realtime data
- Tag all insights as 💡 Directional — this is the weakest data source

**⚠️ FORBIDDEN: Skipping directly to Priority 3 without attempting Priority 1 and 2.**

Extract keywords customers use in reviews → compare with title/bullet keywords.

### Step 7 — Trend Context (1 call)

```bash
python3 scripts/apiclaw.py product-history --asins "{my_asin},{leader1},{leader2}" --start-date "{30d_ago}" --end-date "{today}"
```

**⚠️ Fallback for empty history data:** If product-history returns empty data (count=0) for some ASINs:
1. **Try different ASINs** — newer products or variant ASINs may not have history coverage. Pick ASINs with the oldest `listingDate` from earlier steps.
2. **Try up to 3 rounds** of different ASIN combinations before giving up.
3. If ALL ASINs return empty, use BSR snapshots from DB data + realtime data to infer directional trends. Tag as 🔍 Inferred.
4. **Never report "no trend data available" without trying at least 5 different ASINs.**

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

**Confidence labels — every conclusion or recommendation must be tagged with one of:**
**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

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

- **Never show empty data rows** — omit dimensions with no data
- **Never expose internal errors** — silently fall back to alternative data
- **FORBIDDEN in output**: "fallback", "degraded", "API error", "500", "failed", "insufficient reviews"
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
- For bulk audit (agencies), run Steps 1-8 per ASIN but share Steps 2-5 market data across ASINs
- Keyword gap analysis compares against Top 5 leader titles + bullets, not just one competitor
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- Suggested rewrites should incorporate high-frequency positive review language from Step 6
