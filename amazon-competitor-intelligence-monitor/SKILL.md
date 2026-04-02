---
name: Amazon Competitor Intelligence Monitor
version: 1.1.0
description: >
  Deep competitor intelligence for Amazon sellers with continuous monitoring.
  Two modes: Full Scan (complete analysis, 28-35 credits) and Quick Check (lightweight monitoring, 5-10 credits).
  Full Scan: 11 endpoints, competitor matrix, brand ranking, pricing, reviews, battle strategy.
  Quick Check: realtime/product polling, baseline diff, tiered alerts.
  Use when user asks about: competitor analysis, competitive landscape, competitor tracking,
  competitor monitoring, competitive intelligence, competitor comparison, benchmark, track competitor,
  spy on competitors, 竞品分析, 竞品监控, 竞对追踪.
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
| `scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `references/reference.md` | Load for exact field names or response structure |
| `monitor-data/` | Runtime storage (auto-created): config.json, baseline.json, history/, alerts.json |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input

Required: keyword or ASIN(s). Optional: my_asin, competitor_asins, brand.
If only ASIN given → derive keyword via `product --asin` then ask user to confirm.
Brand queries MUST also include confirmed `--category`.

## API Pitfalls (CRITICAL)

1. **Category first**: MUST resolve and confirm categoryPath with user before any data collection
2. **All keyword-based endpoints MUST include `--category`**; ASIN-specific endpoints do NOT need it
3. **Brand + category**: a brand sells across categories — only analyze within locked subcategory
4. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`atLeastMonthlySales`, concentration=`sampleTop10BrandSalesRate`
5. **reviews/analyze**: needs 50+ reviews; fallback to ratingBreakdown from realtime/product

## Mode Selection

- **Full Scan** (~28-35 credits): First run, no baseline.json, explicit request, or weekly refresh
- **Quick Check** (~5-10 credits): Cron trigger, baseline exists, "check competitors"

## Full Scan Flow

1. Parse input → resolve & confirm categoryPath with user
2. `competitor-analysis --keyword X --category Y [--my-asin Z]` (composite, runs all 11 endpoints)
3. Analyze & score → save baseline to `monitor-data/` → offer Auto-Monitor

## Quick Check Flow

1. Load config.json + baseline.json from `monitor-data/` (missing → fall back to Full Scan)
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

| Dimension | Weight |
|-----------|--------|
| Sales Dominance | 25% — monthly sales, revenue, market share |
| Brand Strength | 20% — brand sales rate, SKU count, price range |
| Listing Quality | 20% — images, bullets, A+, title |
| Customer Satisfaction | 20% — rating, sentiment, pain points |
| Trend Momentum | 15% — BSR direction, sales growth, price stability |

## Auto-Monitor Prompt

After EVERY run, offer: "Set up automatic monitoring? I can generate a scheduled Quick Check." Provide platform-specific setup (OpenClaw `/cron`, ChatGPT Scheduled Tasks, Claude Projects).

## Output Spec

Full Scan sections: Battlefield Overview → Competitor Matrix → Brand Power Ranking → Price Map → 30-Day Trends → Review Battle → Listing Audit → Competitive Scores → Battle Strategy → Data Provenance → API Usage.

Confidence labels: 📊 Data-backed | 🔍 Inferred | 💡 Directional. Strategy is NEVER 📊. Anomalies (>200% growth) always 💡. User criteria override AI judgment.

## API Budget

Full Scan: ~28-35 credits (all 11 endpoints via composite). Quick Check: ~5-10 credits (realtime/product × N ASINs).
