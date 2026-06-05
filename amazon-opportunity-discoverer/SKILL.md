---
name: amazon-opportunity-discoverer
version: 1.0.3
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

# Amazon Opportunity Discoverer — Niche Scanner & Scoring

Tell me your budget and experience. I find opportunities, score them, and rank.

## Files
- **Script**: `{skill_base_dir}/scripts/apiclaw.py` — run `--help` for params
- **Reference**: `{skill_base_dir}/references/reference.md` (field names & response structure)

## Credential
Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys)

## Input
- **Required**: keyword or category + budget (Low/Med/High) + experience (Beginner/Intermediate/Advanced)
- **Recommended**: risk tolerance (Conservative/Moderate/Aggressive)
- **Optional**: fulfillment preference (FBA/FBM), specific filter criteria

## API Pitfalls (see apiclaw skill for full list)
- categoryPath is auto-resolved via `categories`, with fallback to top search result. If `category_source` is `inferred_from_search`, confirm with user — keyword-only queries contaminate results
- All keyword-based endpoints MUST include `--category` when locked
- Revenue = `sampleAvgMonthlyRevenue` directly. Sales = `monthlySalesFloor` (lower bound)
- `reviews/analysis` needs 50+ reviews. Fallback chain when sample is insufficient:
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
     - **Scope**: fallback replaces ONLY the `/reviews/analysis` aggregation. This skill's primary workflow outputs (opportunity scoring, mode-based selection, ranked candidate list) remain valid — do not re-run them.
- Deduplicate ASINs across modes — same product appears in multiple scans
- Each mode has **built-in filters that STACK** with user filters (e.g. beginner: $15-60, sales≥300)

## Unique Logic

### Profile → Strategy Mapping
| Profile | Primary Modes | Price | Max Reviews |
|---------|--------------|-------|-------------|
| Beginner + Conservative | beginner, long-tail, fbm-friendly | $15-60 | <50 |
| Beginner + Moderate | beginner, emerging, low-price | $10-50 | <100 |
| Intermediate + Moderate | fast-movers, underserved, single-variant | $15-80 | <200 |
| Intermediate + Aggressive | high-demand-low-barrier, speculative | $10-100 | <500 |
| Advanced + Aggressive | fast-movers, speculative, top-bsr | any | any |

### User Criteria → Filter Params
Always translate: "300+ monthly sales" → `--sales-min 300`, "reviews <100" → `--ratings-max 100`, "$15-35" → `--price-min 15 --price-max 35`. If user has specific criteria, use custom filters (Approach B/C), NOT default modes.

### Data-Driven Category Selection (no specific category given)
Scan with `market --keyword "{broad}" --topn 10`, rank subcategories by: newSkuRate>10%, topBrandSalesRate<60%, fbaRate>50%, avgPrice $10-50, avgMonthlySales>200. Pick top 3-5.

### Opportunity Score (per candidate, 1-100)
| Dimension | Weight | Good | Medium | Warning |
|-----------|--------|------|--------|---------|
| Demand Signal | 20% | sales>300, rev>$5K | 100-300 | <100 |
| Competition Gap | 20% | reviews<200, CR10<40% | 200-1K, 40-60% | >1K, >60% |
| Price Opportunity | 15% | in best opp band, opp>1.0 | 0.5-1.0 | <0.5 |
| Trend Momentum | 15% | BSR rising | stable | declining |
| Profit Margin | 15% | >30% | 15-30% | <15% |
| Differentiation | 10% | clear pain points | some gaps | none |
| Profile Fit | 5% | matches user profile | partial | mismatch |

### Tiers
| Score | Tier | Label |
|-------|------|-------|
| 80-100 | S | 🔥 Hot — act fast |
| 60-79 | A | ✅ Strong — worth pursuing |
| 40-59 | B | ⚠️ Moderate — needs differentiation |
| 0-39 | C | ❌ Weak — skip |

**Quick-Scan Mode** (~10 credits): 2 modes × 1 page, skip realtime/trend. Label as "directional only."

## Composite Command
```bash
python3 {skill_base_dir}/scripts/apiclaw.py opportunity-scan --keyword "{kw}" --category "{path}" --modes "beginner,emerging,underserved"
```
Or with custom filters: `--sales-min 300 --ratings-max 100 --price-min 15 --price-max 35`

## Output
Respond in user's language.

Sections: Scan Summary → Top 10 Opportunities Table → Detailed Analysis (Top 3) → Category Heatmap → Risk Alerts → Next Steps (S: buy sample, A: deep-dive, B: watch) → Data Provenance → API Usage

If user provides COGS, calculate profit. User criteria override: ANY fail → CAUTION/AVOID.

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "CR10 = 54.8% 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "brand concentration is moderate 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "consider entering $10-15 band 💡")

Rules: Strategy recommendations are NEVER 📊. Anomalies (>200% growth) are always 💡. User criteria override AI judgment.

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

## API Budget: ~50-60 credits
