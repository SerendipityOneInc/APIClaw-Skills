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
- **Script**: `scripts/apiclaw.py` (execute, don't read) — run `--help` for params
- **Reference**: `references/reference.md` (field names & response structure)

## Credential
Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys)

## Input (one of)
- **Single ASIN**: "分析 B09V3KXJPB 的评论"
- **Multi-ASIN**: "对比这 5 个竞品的评论痛点"
- **Category-wide**: keyword/category name → resolve via `categories` first (need ≥3-level deep path)

## API Pitfalls (see apiclaw skill for full list)
- `reviews/analyze` needs **50+ reviews** — fallback to `realtime/product` ratingBreakdown
- **labelType: one per call** — do NOT comma-separate. Make separate calls.
- Category mode needs precise path (≥3 levels) — broad categories = diluted insights
- Field name is `reviewRate` (not `reviewPercentage`) for mention frequency
- ASIN-specific endpoints don't need `--category`; keyword-based ones do

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

### Consumer Profile Synthesis
Combine `userProfiles` + `scenarios` + `usageTimes` + `usageLocations` → complete buyer persona.

### Listing Copy from Reviews
Quote actual customer words from `positives` — these are proven converting phrases.

### Competitor Comparison
Align dimensions (pain points vs pain points) across products. If competitor review data unavailable, use brand-detail sampleProducts + note limitation.

## Composite Command
```bash
python3 scripts/apiclaw.py review-deepdive --target-asin "{asin}" --keyword "{kw}" --category "{path}"
```
Optional: `--comp-asins "{asin1},{asin2}"` for comparison.
Runs: reviews × 11 dimensions + competitors + realtime + market context + price/trend.

## Output
Respond in user's language. Tag every conclusion: 📊 Data-backed / 🔍 Inferred / 💡 Directional.

Sections: Review Snapshot → Top 10 Pain Points (with count & %) → Top 10 Positives → Buying Factors → Improvement Wishlist → Consumer Profile → Usage Patterns → Competitor Comparison → Listing Copy Suggestions → Differentiation Roadmap (impact-ranked) → Data Provenance → API Usage

Do NOT invent insights — only report what the API returns. Omit empty dimensions.
Cross-validate: star distribution (ratingBreakdown) should match sentiment (reviews/analyze).

## API Budget: ~20-30 credits
