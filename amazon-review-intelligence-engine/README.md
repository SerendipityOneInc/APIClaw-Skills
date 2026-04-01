# Amazon Review Intelligence Extractor — APIClaw Agent Skill

> Deep consumer insights from 1B+ pre-analyzed Amazon reviews. No NLP required.

## What This Skill Does

Extracts actionable consumer insights from Amazon product reviews. Give it an ASIN or a category, and it analyzes reviews across **11 dimensions**:

| Dimension | What It Reveals |
|-----------|----------------|
| Pain Points | What customers complain about most |
| Buying Factors | Why customers chose this product |
| Improvements | What customers wish was better |
| Positives | What customers love |
| Issues | Specific product problems |
| Scenarios | How/where customers use the product |
| Keywords | Trending terms in reviews |
| User Profiles | Who is buying (demographics, use cases) |
| Usage Times | When customers use the product |
| Usage Locations | Where customers use the product |
| Behaviors | Customer behavior patterns |

### Three Analysis Modes

- **Single ASIN**: Deep-dive into one product's reviews
- **Multi-ASIN Comparison**: Compare pain points and strengths across competitors
- **Category-wide**: Analyze consumer sentiment across an entire product category

### What Makes This Different

- **1B+ pre-analyzed reviews**: API returns structured insights instantly — no token-heavy NLP processing needed
- **11 API endpoints**: Not just reviews — cross-validates with brand data, pricing, competitor listings, and trends
- **95% token savings**: Structured output vs. feeding raw reviews to an LLM

## Install

```bash
npx skills add SerendipityOneInc/APIClaw-Skills
```

Select **Amazon Review Intelligence Extractor** when prompted.

## API Key Setup

1. Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys) — 1,000 free credits, no credit card
2. Set the environment variable:
   ```bash
   export APICLAW_API_KEY='hms_live_xxxxxx'
   ```

## Example Prompts

- *"Analyze reviews for ASIN B09V3KXJPB — what are the main pain points?"*
- *"Compare review sentiment across these 5 travel mug ASINs"*
- *"What do customers love and hate about yoga mats in general?"*
- *"分析这个产品的差评，找出改进方向"*

## What You Get

| Section | Description |
|---------|-------------|
| 📊 Review Overview | Total reviews, avg rating, sentiment distribution |
| 🔴 Top Pain Points | Ranked complaints with frequency and avg rating |
| 🟢 Top Positives | What customers value most |
| 💡 Buying Factors | Purchase decision drivers |
| 🛠️ Improvement Suggestions | What customers want improved |
| 👤 User Profiles | Who is buying and why |
| 🆚 Competitor Comparison | Side-by-side review sentiment (multi-ASIN mode) |
| 🎯 Differentiation Opportunities | Gaps you can exploit |

## API Endpoints Used

All 11 APIClaw endpoints:

| Endpoint | Purpose |
|----------|---------|
| `categories` | Category resolution |
| `markets/search` | Market context |
| `products/search` | Find top products to analyze |
| `products/competitor-lookup` | Discover competitors |
| `realtime/product` | Live product details + rating breakdown |
| `reviews/analyze` | Core — 11-dimension review analysis |
| `products/price-band-overview` | Price context |
| `products/price-band-detail` | Price band details |
| `products/brand-overview` | Brand landscape |
| `products/brand-detail` | Per-brand breakdown |
| `products/product-history` | Review trend over time |

## Credit Cost

~20-30 credits per analysis.

## Powered By

[APIClaw](https://apiclaw.io) — The data infrastructure built for agents. 200M+ Amazon products, 1B+ reviews, real-time signals.
