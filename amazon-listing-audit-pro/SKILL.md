---
name: amazon-listing-audit-pro
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
metadata:
  version: "1.0.3"
  author: SerendipityOneInc
  homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
  openclaw: {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}
---

# APIClaw — Amazon Listing Audit Pro

> 8-dimension health check. Benchmark against leaders. Fix what matters most. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `{skill_base_dir}/scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `{skill_base_dir}/references/reference.md` | Load for exact field names or response structure |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input

Required: my_asin. Optional: keyword, category. Category is auto-detected from ASIN via `realtime/product` if not provided. If `category_source` is `inferred_from_search`, confirm with user before proceeding.

## API Pitfalls (CRITICAL)

1. **Category auto-detection**: categoryPath is auto-detected from ASIN. If `category_source` in output is `inferred_from_search`, confirm with user
2. **All keyword-based endpoints MUST include `--category`**; ASIN-specific endpoints do NOT
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`monthlySalesFloor`, opportunity=`sampleOpportunityIndex`
4. **reviews/analysis**: needs 50+ reviews; ASIN mode first, category fallback. Fallback chain when both fail:
   1. **Lightweight**: `realtime/product` ratingBreakdown — only star distribution, no themes
   2. **Full 11-dim insights** — bypass `/reviews/analysis` entirely:
      a. `apiclaw.py reviews-raw --asin X` → fetch up to 100 raw reviews (10 credits, ~60s)
      b. For each review: render Map prompt via `apiclaw.py review-tag-prompt --review '<json>'`
         and have your own LLM produce JSON tags (sentiment + 11 dimensions)
      c. Collect candidate phrases per dimension; for each dimension render
         Reduce prompt via `apiclaw.py review-reduce-prompt --label-type X --candidates '[...]'`
         and have your LLM produce semantic clusters
      d. `apiclaw.py review-aggregate --reviews R --tagged T --clusters C`
         → consumerInsights output compatible with `/reviews/analysis`
   3. **Fallback caveats** (apply to the 4-step chain above — lessons from end-to-end validation):
      - **Working dir**: `WORK=/tmp/review_<ASIN>_$(date +%s) && mkdir -p $WORK`
      - **Step b CLI behavior**: `review-tag-prompt` RENDERS the prompt only; YOUR LLM produces the JSON. Render once to learn the schema, then produce tags for all N reviews in one in-context pass (don't call the CLI N times).
      - **Step c candidate extraction** (Python one-liner):
        `candidates = {d: sorted({el.strip().lower() for t in tagged for el in (t.get(d) or [])}) for d in DIMS}`
      - **Small-sample rule (reviewCount<50)**: demote single-mention items 📊→🔍; NEVER attach table-level or section-header 📊 when any row inside is 🔍; suppress "🔴 Critical" verdicts on count=1
      - **Scope**: fallback replaces ONLY the `/reviews/analysis` aggregation. This skill's primary workflow outputs (8-dimension audit scores, title/bullet/A+ checks, category-leader benchmarks) remain valid — do not re-run them.
5. **Sales null fallback**: Monthly sales ≈ 300,000 / BSR^0.65, tag 🔍

## Execution

1. `listing-audit --my-asin X [--keyword Y] [--category Z]` (composite, auto-detects category from ASIN)
3. Score 8 dimensions → generate report with improvements

## 8 Scoring Dimensions

| Dimension | Weight | 90-100 | 60-89 | 30-59 | 0-29 |
|-----------|--------|--------|-------|-------|------|
| Title | 15% | 150+ chars, top 3 KW, brand first | 100-150, 2 KW | <100 or stuffed | Missing key terms |
| Bullets | 15% | 5+, benefit-led, KW each | 5, features only | 3-4, generic | <3 bullets |
| Images | 15% | 7+, infographic+lifestyle | 5-6, decent | 3-4, basic | 1-2 images |
| A+ Content | 10% | Rich A+, comparison, brand story | Basic A+ | No A+ w/ description | Nothing |
| Reviews | 15% | 1000+, 4.5+, <5% 1-star | 200-1K, 4.0-4.5 | 50-200, 3.5-4.0 | <50 or <3.5 |
| Keywords | 10% | Top 5 competitor KW covered | 3-4 covered | 1-2 covered | None matched |
| Category Fit | 10% | Optimal category, top 1% BSR | Top 5% | Suboptimal | Wrong category |
| Pricing | 10% | In opportunity band, margin >25% | Hottest band | Outside top bands | Overpriced/<10% margin |

Score each 0-100, calculate weighted total. Include "Basis" column explaining each score.

## Output Spec

Sections: Overall Score (X/100, A-F grade) → 8-Dimension Scorecard → Title Audit (analysis + suggested rewrite) → Bullets Audit (vs leaders, missing points, rewrites) → Image Audit → Review Health → Keyword Gap Analysis (vs Top 5 leader titles/bullets) → vs Category Leaders (side-by-side Top 3) → Priority Fix List (lowest scores first) → Data Provenance → API Usage.

Suggested rewrites should incorporate high-frequency positive review language.

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "CR10 = 54.8% 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "brand concentration is moderate 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "consider entering $10-15 band 💡")

Rules: Strategy recommendations are NEVER 📊. User criteria override AI judgment.

**Aggregate-label rule (applies to ALL report output, not just fallback)**: NEVER attach 📊 to ANY element that aggregates or groups underlying content when ANY piece of that content is 🔍 or 💡. "Aggregate/grouping elements" include:
- Section headers at EVERY level (`#`, `##`, `###`, `####`) — including top-level summary sections like "Overall Score", "Verdict", "Executive Summary"
- Summary/score lines anywhere in the report (e.g. `## Overall Score — 27/100 · Grade F 📊` is WRONG if any Basis row inside is 🔍)
- Table **column** headers in comparison tables (e.g. `**Target ASIN** 📊` as a column label is WRONG if any cell in that column contains 🔍)
- Table row headers or row-aggregation labels (when the row aggregates multiple cells of mixed confidence)
- Any other visual grouping label — bullet-list group titles, callout box titles, etc.

A group-level 📊 implies the whole block/column/row is data-backed, which smuggles inferred/directional content into the 📊 tier via visual grouping. Either (a) **omit the group-level label entirely** (preferred when content mixes tiers), or (b) use the LOWEST confidence present inside (🔍 if any underlying content is 🔍; 💡 if any is 💡). This is a universal output-quality rule — it applies regardless of which fallback path (if any) was triggered.

**Emoji reservation rule (closely related)**: The three confidence symbols `📊 🔍 💡` are RESERVED for confidence labeling. NEVER use them as decorative prefixes on section headers, table headers, or any aggregate element — even when you also include a correct confidence suffix on the same line. Example:
- ❌ WRONG: `## 📊 Overall Score — 27/100 · Grade F 🔍` (the leading 📊 reads as a data-backed claim even though the trailing 🔍 is correct)
- ✅ RIGHT: `## Overall Score — 27/100 · Grade F 🔍` (no decorative emoji, just the proper confidence suffix)
- ✅ RIGHT: `## 🎯 Overall Score — 27/100 · Grade F 🔍` (use non-reserved decorative icons like 🎯 🧭 📋 📝 📂 🏁 🚨 🏆 🔔 when a visual prefix is desired)

Decorative emoji ≠ confidence label — but from a reader's perspective, a leading `📊/🔍/💡` is indistinguishable from a confidence claim. Reserve these three symbols EXCLUSIVELY for confidence annotation to avoid ambiguity.

Bulk audit: share market data across ASINs, run audit per ASIN.

### Data Provenance (required)

Include a table at the end of every report:

| Data | Endpoint | Key Params | Notes |
|------|----------|------------|-------|
| (e.g. Market Overview) | `markets/search` | categoryPath, topN=10 | 📊 Top N sampling, sales are lower-bound |
| ... | ... | ... | ... |

Extract endpoint and params from `_query` in JSON output. Add notes: sampling method, T+1 delay, realtime vs DB, minimum review threshold, etc.

### API Usage (required)

| Endpoint | Calls | Credits |
|----------|-------|---------|
| (each endpoint used) | N | N |
| **Total** | **N** | **N** |

Extract from `meta.creditsConsumed` per response. End with `Credits remaining: N`.

## API Budget: ~20-25 credits

Audit target(1) + Categories/Products/Competitors(3) + Realtime×5(5) + Market/Brand(3) + Price(2) + Reviews(2) + History(1) + Buffer(3-8).
