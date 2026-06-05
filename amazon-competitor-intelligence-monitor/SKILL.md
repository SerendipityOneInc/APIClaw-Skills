---
name: amazon-competitor-intelligence-monitor
version: 1.1.3
description: >
  Deep competitor intelligence for Amazon sellers with continuous monitoring.
  Two modes: Full Scan (complete analysis, 28-35 credits) and Quick Check (lightweight monitoring, 5-10 credits).
  Full Scan: 11 endpoints, competitor matrix, brand ranking, pricing, reviews, battle strategy.
  Quick Check: realtime/product polling, baseline diff, tiered alerts.
  Use when user asks about: competitor analysis, competitive landscape, competitor tracking,
  competitor monitoring, competitive intelligence, competitor comparison, benchmark, track competitor,
  spy on competitors, competitor analysis, competitor monitoring, competitor tracking.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Competitor Intelligence Monitor

> Know your enemy. Two modes: Full Scan + Quick Check. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `{skill_base_dir}/scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `{skill_base_dir}/references/reference.md` | Load for exact field names or response structure |
| `{skill_base_dir}/monitor-data/` | Runtime storage (auto-created): config.json, baseline.json, history/, alerts.json |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input

Required: keyword or ASIN(s). Optional: my_asin, competitor_asins, brand.
If only ASIN given → derive keyword via `product --asin` then ask user to confirm.
Brand queries MUST also include confirmed `--category`.

## API Pitfalls (CRITICAL)

1. **Category auto-detection**: categoryPath is auto-detected from keyword, ASIN, or top search result. If `category_source` in output is `inferred_from_search`, MUST confirm with user before trusting results
2. **All keyword-based endpoints MUST include `--category`**; ASIN-specific endpoints do NOT need it
3. **Brand + category**: a brand sells across categories — only analyze within locked subcategory
4. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`monthlySalesFloor`, concentration=`sampleTop10BrandSalesRate`
5. **reviews/analysis**: needs 50+ reviews. Fallback chain when sample is insufficient:
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
      - **Scope**: fallback replaces ONLY the `/reviews/analysis` aggregation. This skill's primary workflow outputs (competitor metrics, brand ranking, pricing, etc.) remain valid — do not re-run them.

## Mode Selection

- **Full Scan** (~28-35 credits): First run, no baseline.json, explicit request, or weekly refresh
- **Quick Check** (~5-10 credits): Cron trigger, baseline exists, "check competitors"

## Full Scan Flow

1. `competitor-analysis --keyword X [--category Y] [--my-asin Z]` (composite, auto-detects category)
2. If `category_source` is `inferred_from_search`, confirm with user before presenting results
3. Analyze & score → save baseline to `{skill_base_dir}/monitor-data/` → offer Auto-Monitor

## Quick Check Flow

1. Load config.json + baseline.json from `{skill_base_dir}/monitor-data/` (missing → fall back to Full Scan)
2. Poll `product --asin {asin}` for each tracked ASIN
3. Diff against baseline with tiered alerts → update baseline → offer Auto-Monitor

## Alert Tiers

| 🔴 Critical | 🟡 Watch | 🟢 Opportunity |
|-------------|----------|----------------|
| Price change > threshold | FBA↔FBM switch | Competitor stock-out |
| BSR crash > threshold | Rating change | Bullet/image changes |
| Buy Box owner changed | Abnormal review growth | Variant added/removed |
| | Title modified | |

## Competitive Score (per competitor, 1-100)

| Dimension | Weight | 80-100 (Strong) | 50-79 (Moderate) | 0-49 (Weak) |
|-----------|--------|-----------------|-------------------|-------------|
| Sales Dominance | 25% | Top 3 in category, >5K units/mo 📊 | Top 20, 1K-5K units/mo 📊 | Below Top 20, <1K units/mo 📊 |
| Brand Strength | 20% | Brand in CR10, 5+ SKUs, wide price range 📊 | Known brand, 2-4 SKUs 📊 | Unknown brand, single SKU 📊 |
| Listing Quality | 20% | 7+ images, 5 bullets, A+, optimized title 📊 | 5-6 images, basic bullets 📊 | <5 images, weak bullets, no A+ 📊 |
| Customer Satisfaction | 20% | Rating ≥4.5, <3% 1-star, positive sentiment 📊 | 4.0-4.4, 3-8% 1-star 📊 | <4.0 or >8% 1-star 📊 |
| Trend Momentum | 15% | BSR improving 30d, sales growth >10% 🔍 | BSR stable, flat sales 🔍 | BSR declining, sales drop 🔍 |

### Competitive Threat Level
| Total Score | Threat | Interpretation |
|-------------|--------|---------------|
| 80-100 | 🔴 Dominant | Hard to compete head-on; find differentiation or avoid price band 💡 |
| 50-79 | 🟡 Competitive | Beatable with better listing, pricing, or reviews 💡 |
| 0-49 | 🟢 Vulnerable | Weak competitor; opportunity to capture share 💡 |

### Market Structure Analysis
- **CR10 > 70%**: Concentrated market — new entrants need strong differentiation or niche positioning 🔍
- **CR10 40-70%**: Moderately competitive — room for well-positioned products 🔍
- **CR10 < 40%**: Fragmented — opportunity for brand building 🔍
- **Top brand share > 25%**: Category leader dominance — avoid direct competition in their price band 💡
- **New SKU rate > 15%**: Active market with frequent new entrants 📊
- **New SKU rate < 5%**: Mature/stagnant market, high barriers 🔍

## Auto-Monitor Prompt

After EVERY run, offer: "Set up automatic monitoring? I can generate a scheduled Quick Check." Provide platform-specific setup (OpenClaw `/cron`, ChatGPT Scheduled Tasks, Claude Projects).

## Output Spec

Full Scan sections: Battlefield Overview → Competitor Matrix → Brand Power Ranking → Price Map → 30-Day Trends → Review Battle → Listing Audit → Competitive Scores → Battle Strategy → Data Provenance → API Usage.

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

## API Budget

Full Scan: ~28-35 credits (all 11 endpoints via composite). Quick Check: ~5-10 credits (realtime/product × N ASINs).
