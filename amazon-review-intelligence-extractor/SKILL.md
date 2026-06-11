---
name: amazon-review-intelligence-extractor
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
metadata:
  version: "1.0.3"
  author: SerendipityOneInc
  homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
  openclaw:
    requires:
      env:
        - APICLAW_API_KEY
    primaryEnv: "APICLAW_API_KEY"
---

# Amazon Review Intelligence Extractor — 11 Dimensions, 1B+ Reviews

Pre-analyzed consumer insights. Pain points, buying factors, user profiles, differentiation gaps.

## Files
- **Script**: `{skill_base_dir}/scripts/apiclaw.py` — run `--help` for params
- **Reference**: `{skill_base_dir}/references/reference.md` (field names & response structure)

## Credential
Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys)

## Input (one of)
- **Single ASIN**: "Analyze reviews for B09V3KXJPB"
- **Multi-ASIN**: "Compare review pain points across these 5 competitor ASINs"
- **Category-wide**: keyword/category name → resolve via `categories` first (need ≥3-level deep path)

## API Pitfalls (see apiclaw skill for full list)
- `reviews/analysis` needs **50+ reviews**. Fallback chain when sample is insufficient:
  1. **Lightweight**: `realtime/product` ratingBreakdown — only star distribution, no themes
  2. **Full 11-dim insights**: see "Insufficient Data Fallback" section below — use the
     local toolkit (`reviews-raw` + `review-tag-prompt` + `review-reduce-prompt` +
     `review-aggregate`) to bypass `/reviews/analysis` entirely
- **labelType** is NOT an API request parameter — the API returns all 11 dimensions in one call. Filter by `labelType` client-side from the `consumerInsights` array.
- Category mode needs precise path (≥3 levels) — broad categories = diluted insights
- Field name is `reviewRate` (NOT the legacy `reviewPercentage` from API v1) for mention frequency
- ASIN-specific endpoints don't need `--category`; keyword-based ones do
- **Category auto-detection**: categoryPath is auto-detected from target ASIN. If `category_source` in output is `inferred_from_search`, confirm with user

## 11 Analysis Dimensions
`painPoints` · `issues` · `positives` · `improvements` · `buyingFactors` · `keywords` · `userProfiles` · `scenarios` · `usageTimes` · `usageLocations` · `behaviors`

## Unique Logic

### Analysis Modes
- **Category mode**: all reviews in category → market-level insights
- **ASIN mode**: specific products → competitive analysis
- Choose based on user intent. Category = broader, ASIN = deeper.

### Pain Point Impact Ranking
Rank differentiation opportunities by: **frequency × avg rating delta**
"Top pain point: durability — mentioned in 27/471 reviews (5.7%), avg rating 2.4 when mentioned"

| reviewRate | Frequency Level | Interpretation |
|------------|----------------|---------------|
| >10% | 🔴 Critical | Mentioned by 1 in 10 buyers — must address in product design 📊 |
| 5-10% | 🟡 Significant | Common complaint — differentiator if solved 📊 |
| 2-5% | 🟠 Notable | Worth mentioning in listing if you solve it 📊 |
| <2% | 🟢 Minor | Edge case — deprioritize unless easy fix 🔍 |

| avgRating when mentioned | Severity |
|--------------------------|----------|
| <2.5 | Severe — causes returns/1-star reviews 📊 |
| 2.5-3.5 | Moderate — disappoints but doesn't cause returns 🔍 |
| >3.5 | Mild — noticed but not deal-breaker 🔍 |

**Differentiation Priority** = High frequency + Low avgRating = Biggest opportunity 🔍. If top 3 pain points all have reviewRate >5% and avgRating <3.0, there is a clear product improvement opportunity 💡. If all pain points have reviewRate <2%, the category is well-served — differentiation through reviews is limited 🔍.

⚠️ **Small-sample caveat (N < 50)**: The reviewRate thresholds above assume ≥50 reviews. With smaller samples (e.g. fallback toolkit with 14 reviews), every single mention = 1/N which already crosses 5-10%. Rules to apply when `reviewCount < 50`:
- Demote single-mention pain points / positives from 📊 to 🔍 (directional, not data-backed)
- In the report, surface a "Sample-size advisory" banner above all percentage-based tables
- Prefer reporting `count` alongside `reviewRate` so readers can judge weight themselves
- Do NOT trigger "🔴 Critical / clear improvement opportunity" 💡 verdicts on counts of 1
- **Never attach a table-level or section-header 📊 label** when ANY row inside is single-mention (🔍-demoted). A header 📊 implies the entire table is data-backed, which contradicts the per-row demotion rule and smuggles 🔍 data back into the 📊 tier via visual grouping. Either:
  - (a) Omit the header-level confidence label entirely and let individual rows carry their own labels, OR
  - (b) If the header must carry a label, use the LOWEST confidence present in any row (🔍 if any row is 🔍; 📊 only if EVERY row qualifies as 📊 on its own — i.e. all counts ≥ 2 when N<50)

### Consumer Profile Synthesis
Combine `userProfiles` + `scenarios` + `usageTimes` + `usageLocations` → complete buyer persona.

### Listing Copy from Reviews
Quote actual customer words from `positives` — these are proven converting phrases. High-frequency positive elements (reviewRate >5%) should appear in title or first bullet 💡.

### Competitor Comparison
Align dimensions (pain points vs pain points) across products. If competitor review data unavailable, use brand-detail sampleProducts + note limitation.
- **Your pain point rate < competitor's**: Advantage — highlight in listing 💡
- **Your pain point rate > competitor's**: Risk — address in product iteration 💡
- **Both high on same pain point**: Category-wide issue — solving it is a strong differentiator 🔍

## Composite Command
```bash
python3 {skill_base_dir}/scripts/apiclaw.py review-deepdive --target-asin "<ASIN>" [--keyword "<kw>"] [--category "<path>"]
```
Optional: `--comp-asins "<asin1>,<asin2>"` for comparison.
Runs: reviews × 11 dimensions + competitors + realtime + market context + price/trend.
(`<placeholders>` are LITERAL — replace with actual values, no curly braces in commands.)

### Detecting when to fall back

After `review-deepdive` runs, programmatically inspect its JSON output for sparse
review aggregation. The composite continues past review failures, so success is NOT
proof of usable insights. Detection rule:

```python
import json
deepdive = json.load(open("deepdive.json"))
reviews_section = deepdive.get("reviews", {})
# review-deepdive currently makes one /reviews/analysis call per labelType (target_painPoints,
# target_positives, etc.). All-fail means switch to fallback.
all_failed = all(
    sub.get("success") is False
    or not (sub.get("data") or {}).get("consumerInsights")
    for sub in reviews_section.values()
    if isinstance(sub, dict)
)
target_review_count = (deepdive.get("target_realtime", {}) or {}).get("data", {}).get("ratingCount", 0)
# Fallback triggers if ANY of these are true:
needs_fallback = (
    all_failed
    or target_review_count < 50
    or any((sub.get("error") or {}).get("code") == "INSUFFICIENT_REVIEWS"
           for sub in reviews_section.values() if isinstance(sub, dict))
)
```

If `needs_fallback` is True, run the "Insufficient Data Fallback" workflow below.
**Important**: the fallback REPLACES ONLY the review-analysis piece. Keep using the
deepdive's other outputs (`target_realtime`, `competitors`, `market`, `brand_overview`,
`price_band_overview`, `product_history`) for the corresponding report sections.

## Insufficient Data Fallback

When `/reviews/analysis` cannot produce meaningful aggregation, fetch raw reviews live
from Amazon and use this skill's own LLM (you) to perform Map/Reduce in-context. No
external LLM service or API key is required.

**Working directory convention**: create a per-run temp dir to keep intermediate files
together. Recommended: `/tmp/review_<ASIN>_<TIMESTAMP>/` containing `raw.json`,
`tagged.json`, `clusters.json`, `insights.json`. Example:
```bash
WORK=/tmp/review_B0XXXXXXXX_$(date +%s) && mkdir -p $WORK
```

### Step 1 — Fetch raw reviews

```bash
python3 {skill_base_dir}/scripts/apiclaw.py reviews-raw \
    --asin <ASIN> [--marketplace US] [--max-pages 10] > $WORK/raw.json
# Cost: 1 credit/page, 10 reviews/page, hard cap 100 (10 pages).
# Stops automatically when nextCursor=null (small-volume ASINs may exhaust earlier).
# For cost control: --max-pages 5 = 50 reviews / 5 credits / ~30s.
```

Then save just the reviews array for downstream tooling:
```bash
python3 -c "import json,sys; d=json.load(open('$WORK/raw.json'))['data']['reviews']; json.dump(d,open('$WORK/reviews_array.json','w'),ensure_ascii=False)"
```

### Step 2 — Map (per-review tagging)

`review-tag-prompt` renders the prompt **but does NOT call any LLM** — YOU (this skill's
LLM) produce the JSON. The template is uniform per review, so render it ONCE to learn
the schema, then mass-produce tags for all reviews in a single in-context pass.

```bash
# Render the prompt for ONE review to learn the schema (do this once per skill run)
python3 {skill_base_dir}/scripts/apiclaw.py review-tag-prompt \
    --review "$(python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))[0]))' $WORK/reviews_array.json)" \
    [--product-title "..."] [--product-category "..."]
```

The schema you must produce per review (12 fields, all required, empty arrays for empties):
```json
{
  "sentiment": "positive|neutral|negative",
  "mentioned_scenarios": [], "mentioned_issues": [], "mentioned_positives": [],
  "mentioned_improvements": [], "mentioned_buying_factors": [],
  "mentioned_pain_points": [], "user_profiles": [],
  "mentioned_usage_times": [], "mentioned_usage_locations": [],
  "mentioned_behaviors": [], "keywords": []
}
```

After producing tags for all N reviews, save them as a JSON array preserving review order:
```bash
# Save your in-context output as the array (example structure)
cat > $WORK/tagged.json <<'EOF'
[ {tag obj for review[0]}, {tag obj for review[1]}, ... ]
EOF
```

### Step 3 — Reduce (semantic clustering per dimension)

First extract unique candidate phrases per dimension from `tagged.json`:

```python
import json
from collections import defaultdict
tagged = json.load(open(f"{WORK}/tagged.json"))
DIMS = ["mentioned_scenarios","mentioned_issues","mentioned_positives",
        "mentioned_improvements","mentioned_buying_factors","mentioned_pain_points",
        "user_profiles","mentioned_usage_times","mentioned_usage_locations",
        "mentioned_behaviors","keywords"]
candidates = {d: sorted({el.strip().lower() for t in tagged for el in (t.get(d) or [])}) for d in DIMS}
```

Then for EACH of the 11 dimensions, render the reduce prompt and YOU produce clusters:

```bash
python3 {skill_base_dir}/scripts/apiclaw.py review-reduce-prompt \
    --label-type positives \
    --candidates '["comfortable","comfy","very comfortable",...]'
# → YOU produce {"clusters": [{"canonical": "Comfortable Fit",
#                              "members": ["comfortable","comfy","very comfortable"]}]}
```

Assemble all 11 dimension cluster outputs into one `clusters.json`:
```json
{
  "mentioned_scenarios": [{"canonical": "...", "members": [...]}],
  "mentioned_issues":    [{"canonical": "...", "members": [...]}],
  ... (all 11 dims, even if empty: use [])
}
```

**Keywords dim chunking**: when `keywords` has >150 unique candidates, split into
chunks of ~150, render the reduce prompt per chunk, and merge clusters across chunks
by case-insensitive canonical name match. Other dims rarely exceed 100 candidates.

### Step 4 — Aggregate (no LLM, pure local)

```bash
python3 {skill_base_dir}/scripts/apiclaw.py review-aggregate \
    --reviews $WORK/raw.json \
    --tagged $WORK/tagged.json \
    --clusters $WORK/clusters.json > $WORK/insights.json
# Output structure matches /reviews/analysis:
#   { reviewCount, avgRating, sentimentDistribution, consumerInsights[], topKeywords[] }
# Each consumerInsight has: {element, labelType, count, reviewRate, avgRating}
```

Use the same Pain Point Impact Ranking and Differentiation Priority tables above —
**but apply the small-sample caveat** when `reviewCount < 50`.

### Quality flags to surface in the final report

When generating the report from a fallback run, the Data Provenance section MUST flag:

1. **Sample-size warning** — if `reviewCount < 50`, banner above all rate-based tables.
2. **Suspicious review patterns** — scan `raw.json` for clusters of:
   - Same date + ≥3 unverified reviews + similar themes (potential seeded reviews)
   - Same author across multiple ASINs (review farm signal)
   Report these as "🔍 Possible seeded reviews" in Data Provenance.
3. **Spider exhaustion** — if `pages < max_pages` and `capped == false`, note that
   Spider exhausted the visible review window before reaching the 100-cap.

### Competitor Comparison in fallback mode

The default fallback workflow only fetches reviews for the TARGET ASIN.
SKILL.md's "Competitor Comparison" rules (your-rate vs competitor-rate) require
competitor review data, which is NOT available by default in fallback. Two options:

- **Option A (default)**: in the report's Competitor Comparison section, note
  "Pain-rate comparison unavailable in fallback mode — competitor review aggregations
  not fetched". Use only structural comparison (rating, ratingCount, price).
- **Option B (extension)**: for each top-3 competitor ASIN from the deepdive's
  `competitors` output, run Steps 1-4 again per ASIN. Cost: ~10 credits per
  competitor + LLM time. Only do this when the user explicitly asks for sentiment
  comparison.

### Cost / latency benchmark

| Sample size | Fetch | LLM Map+Reduce | Aggregate | Total |
|-------------|-------|----------------|-----------|-------|
| 100 reviews | ~60s + 10 credits | model-dependent (suggest ≤20 concurrent) | <1s | ~90-120s |
| 50 reviews | ~30s + 5 credits | ~half | <1s | ~60s |
| 14 reviews (validated) | ~20s + 2 credits | inline single pass | <1s | ~30s |

**Quality vs `/reviews/analysis`**: comparable 11-dim coverage; finer sizing-direction
splits (small vs large vs inaccurate) than server-side aggregation; properly
distinguishes `painPoints` (problems experienced) from `positives` (problems solved).

## Output
Respond in user's language.

Sections: Review Snapshot → Top 10 Pain Points (with count & %) → Top 10 Positives → Buying Factors → Improvement Wishlist → Consumer Profile → Usage Patterns → Competitor Comparison → Listing Copy Suggestions → Differentiation Roadmap (impact-ranked) → Data Provenance → API Usage

Do NOT invent insights — only report what the API returns. Omit empty dimensions.

**Cross-validation rule** (mandatory): star distribution (`ratingBreakdown`) should match
sentiment distribution (from `reviews/analysis` OR fallback Map tags). Compute:
- 4-5★ % vs `positive` %
- 3★ % vs `neutral` %
- 1-2★ % vs `negative` %

If any band mismatches by >15 percentage points, **re-examine the Map tags before
publishing**. Common causes: LLM mis-classifying a 5★ "didn't love it but works" as
positive; non-English reviews mis-tagged. Document residual mismatch in Data Provenance.

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "painPoint 'durability' mentioned by 27% of reviewers 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "durability is the #1 differentiation opportunity 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "highlight durability in bullet point #1 💡")

Rules: Strategy recommendations and listing copy suggestions are NEVER 📊. User criteria override AI judgment.

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

## API Budget: ~20-30 credits
