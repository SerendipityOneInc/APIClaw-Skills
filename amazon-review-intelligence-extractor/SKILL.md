---
name: Amazon Review Intelligence Extractor — Consumer Insights from 1B+ Reviews
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

# Amazon Review Intelligence Extractor — 11 Dimensions, 1B+ Reviews

Pre-analyzed consumer insights. Pain points, buying factors, user profiles, differentiation gaps.

## Files
- **Script**: `{skill_base_dir}/scripts/apiclaw.py` (execute, don't read) — run `--help` for params
- **Reference**: `{skill_base_dir}/references/reference.md` (field names & response structure)

## Credential
Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys)

## Input (one of)
- **Single ASIN**: "Analyze reviews for B09V3KXJPB"
- **Multi-ASIN**: "Compare review pain points across these 5 competitor ASINs"
- **Category-wide**: keyword/category name → resolve via `categories` first (need ≥3-level deep path)

## API Pitfalls (see apiclaw skill for full list)
- `reviews/analysis` needs **50+ reviews** — fallback to `realtime/product` ratingBreakdown
- **labelType** is NOT an API request parameter — the API returns all 11 dimensions in one call. Filter by `labelType` client-side from the `consumerInsights` array.
- Category mode needs precise path (≥3 levels) — broad categories = diluted insights
- Field name is `reviewRate` (not `reviewRate`) for mention frequency
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
python3 {skill_base_dir}/scripts/apiclaw.py review-deepdive --target-asin "{asin}" [--keyword "{kw}"] [--category "{path}"]
```
Optional: `--comp-asins "{asin1},{asin2}"` for comparison.
Runs: reviews × 11 dimensions + competitors + realtime + market context + price/trend.

## Output
Respond in user's language.

Sections: Review Snapshot → Top 10 Pain Points (with count & %) → Top 10 Positives → Buying Factors → Improvement Wishlist → Consumer Profile → Usage Patterns → Competitor Comparison → Listing Copy Suggestions → Differentiation Roadmap (impact-ranked) → Data Provenance → API Usage

Do NOT invent insights — only report what the API returns. Omit empty dimensions.
Cross-validate: star distribution (ratingBreakdown) should match sentiment (reviews/analysis).

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "painPoint 'durability' mentioned by 27% of reviewers 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "durability is the #1 differentiation opportunity 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "highlight durability in bullet point #1 💡")

Rules: Strategy recommendations and listing copy suggestions are NEVER 📊. User criteria override AI judgment.

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
