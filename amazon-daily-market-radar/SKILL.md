---
name: Amazon Daily Market Radar — Automated Monitoring & Alerts
version: 1.0.0
description: >
  Automated daily market monitoring and alert system for Amazon sellers.
  Tracks price changes, new competitors, BSR movements, review spikes,
  stock-out signals, and market shifts. Designed for unattended agent automation.
  Uses all 11 APIClaw API endpoints with cross-validation.
  Use when user asks about: daily monitoring, market alerts, track competitors,
  price monitoring, BSR tracking, market changes, daily briefing, market watch,
  competitor alerts, review monitoring, stock alerts, market dashboard,
  daily report, market updates, what changed today.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Daily Market Radar

> Set it. Forget it. Get alerted when it matters. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `references/reference.md` | Load for exact field names or response structure |
| `data/` | Runtime: watchlist.json, last-run.json (auto-created) |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input (First Run)

Collect in ONE message: ✅ my_asins (1-10) + keyword | 💡 competitor_asins (up to 20) | 📌 alert_preferences.

## API Pitfalls (CRITICAL)

1. **Category first**: MUST resolve categoryPath via `categories --keyword` before any data collection
2. **All keyword-based endpoints MUST include `--category`**; ASIN-specific endpoints do NOT
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`monthlySalesFloor`, concentration=`sampleTop10BrandSalesRate`
4. **reviews/analysis**: needs 50+ reviews
5. **Aggregation without categoryPath**: severely distorted data

## Execution

1. Resolve & lock categoryPath
2. `daily-radar --asins "asin1,asin2,..." --keyword X --category Y` (composite, runs all endpoints)
3. Compare against `data/last-run.json` for change detection (first run = baseline only, no alerts)
4. Generate alert-prioritized briefing → save snapshot to `data/last-run.json`

## Alert Rules

| Level | Triggers |
|-------|----------|
| 🔴 RED | Price drop >10% by competitor; BSR crash >50% (yours); 1-star spike (3+ in 24h) |
| 🟡 YELLOW | New competitor in Top 20; competitor price change 5-10%; BSR change 20-50%; brand share shift >2% |
| 🟢 GREEN | Competitor stock-out; your review velocity up; price band opportunity shift |

## Change Detection Logic

- Price change >5% → 🔴
- BSR move >20% → 🟡
- New ASINs in top 20 (vs last run) → 🟡

Growth signal validation:
- 📊 Sustained: 7+ days consistent direction
- 🔍 Possible signal: 2-3 days of change
- 💡 Single-day spike: could be promotion/restock

## Output Spec

First run: "Baseline Established" — KPI Dashboard (current snapshot) only, no alerts.

Subsequent runs: Alert Summary → RED Alerts → YELLOW Alerts → GREEN Opportunities → KPI Dashboard (today vs yesterday) → Competitor Movement → Market Shifts → Action Items → Data Provenance → API Usage.

Confidence labels: 📊 Data-backed | 🔍 Inferred | 💡 Directional. Strategy is NEVER 📊. Anomalies (>200% growth) always 💡. User criteria override AI judgment.

Sample bias: "Based on Top [N] by sales volume; niche/new products may be underrepresented."

## API Budget: ~15-30 credits

Realtime×ASINs(5-15) + History(1-2) + Market/Brand(3) + Products(1) + Price(2) + Categories(1) + Reviews(1-3).
