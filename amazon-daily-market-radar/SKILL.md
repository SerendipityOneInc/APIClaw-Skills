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
| `{skill_base_dir}/scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `{skill_base_dir}/references/reference.md` | Load for exact field names or response structure |
| `{skill_base_dir}/data/` | Runtime: watchlist.json, last-run.json (auto-created) |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input (First Run)

Collect in ONE message: ✅ my_asins (1-10) | 💡 competitor_asins (up to 20) | 📌 alert_preferences. Optional: keyword, category. Category is auto-detected from first tracked ASIN if not provided.

## API Pitfalls (CRITICAL)

1. **Category auto-detection**: categoryPath is auto-detected from tracked ASINs. If `category_source` in output is `inferred_from_search`, confirm with user
2. **All keyword-based endpoints MUST include `--category`**; ASIN-specific endpoints do NOT
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`monthlySalesFloor`, concentration=`sampleTop10BrandSalesRate`
4. **reviews/analysis**: needs 50+ reviews
5. **Aggregation without categoryPath**: severely distorted data

## Execution

1. `daily-radar --asins "asin1,asin2,..." [--keyword X] [--category Y]` (composite, auto-detects category from ASINs)
3. Compare against `{skill_base_dir}/data/last-run.json` for change detection (first run = baseline only, no alerts)
4. Generate alert-prioritized briefing → save snapshot to `{skill_base_dir}/data/last-run.json`

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

### Change Interpretation Guide
| Metric | Normal Range | Action Trigger | Likely Cause |
|--------|-------------|----------------|-------------|
| Price change | ±3% | >5% sustained 3+ days | Repricing strategy or promotion 🔍 |
| BSR shift | ±15% daily | >30% sustained or >50% single day | Stockout, promotion, or algorithm change 🔍 |
| Rating drop | ±0.1 | >0.2 in 7 days | Product quality issue or review attack 🔍 |
| Review velocity | ±20% | >50% spike | Vine program, review manipulation, or viral moment 🔍 |
| New entrant in Top 20 | 0-1/week | 3+ in one week | Market shift or seasonal demand 🔍 |

### Action Recommendations by Alert Level
- **🔴 RED**: Require immediate response — check inventory, match price if needed, investigate quality issues 💡
- **🟡 YELLOW**: Monitor for 3-5 days before acting — may be temporary fluctuation 💡
- **🟢 GREEN**: Opportunity window — act within 1-2 weeks before competitors notice 💡

## Output Spec

First run: "Baseline Established" — KPI Dashboard (current snapshot) only, no alerts.

Subsequent runs: Alert Summary → RED Alerts → YELLOW Alerts → GREEN Opportunities → KPI Dashboard (today vs yesterday) → Competitor Movement → Market Shifts → Action Items → Data Provenance → API Usage.

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "CR10 = 54.8% 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "brand concentration is moderate 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "consider entering $10-15 band 💡")

Rules: Strategy recommendations are NEVER 📊. Anomalies (>200% growth) are always 💡. User criteria override AI judgment.

Sample bias: "Based on Top [N] by sales volume; niche/new products may be underrepresented."

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

## API Budget: ~15-30 credits

Realtime×ASINs(5-15) + History(1-2) + Market/Brand(3) + Products(1) + Price(2) + Categories(1) + Reviews(1-3).
