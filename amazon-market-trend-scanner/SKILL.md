---
name: amazon-market-trend-scanner
description: >
  Amazon category trend scanner. Scans Amazon category landscapes to discover
  trending subcategories, emerging niches, and market shifts. Tracks demand
  surges, brand consolidation, new entrant waves, price band migration, and
  margin changes across all subcategories under a parent category.
  Use when user asks about: market trends, category trends, trending
  categories, what's hot, emerging categories, trend scanner,
  which categories are growing, where the market is heading.
  Requires APICLAW_API_KEY.
metadata:
  version: "1.0.2"
  author: SerendipityOneInc
  homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
  openclaw: {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}
---

# APIClaw — Market Trend Scanner

> Find rising categories before everyone else. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `{skill_base_dir}/scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `{skill_base_dir}/references/reference.md` | Load for exact field names or response structure |
| `{skill_base_dir}/scan-data/` | Runtime: watchlist.json, baseline.json, alerts.json, history/ (auto-created) |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input

Tell the user: "Give me one or more categories to monitor (e.g. 'Pet Supplies > Dogs'). I'll scan all subcategories and find trending directions. Single or batch supported."

Required: 1+ category paths or keywords. Optional: scan depth, metric preferences.

## API Pitfalls (CRITICAL)

1. **Category first**: resolve categoryPath via `categories --keyword` before anything
2. **All keyword endpoints MUST include `--category`**; omitting it distorts aggregation
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue`, sales=`monthlySalesFloor`
4. **Key metrics per subcategory**: sampleAvgMonthlySales, sampleNewSkuRate, topBrandSalesRate, sampleAvgPrice, sampleAPlusRate, totalSkuCount, sampleFbaRate

## Mode 1: Full Scan

1. `categories --keyword "{keyword}"` → resolve category path
2. `market --category "{path}" --page-size 20` → collect all subcategory market data (paginate)
3. Record 7 key metrics per subcategory (see Pitfalls #4)
4. `products --keyword "{sub}" --category "{path}" --mode emerging --page-size 20` per hot subcategory
5. `products --keyword "{sub}" --category "{path}" --mode new-release --page-size 20` per hot subcategory
6. Save baseline → `{skill_base_dir}/scan-data/baseline.json`, config → `{skill_base_dir}/scan-data/watchlist.json`
7. Output full trend report (see Output Spec)
8. Offer Auto-Monitor setup

## Mode 2: Quick Check (scheduled)

1. Read `{skill_base_dir}/scan-data/watchlist.json` + `{skill_base_dir}/scan-data/baseline.json`
2. `market --category "{path}"` per watched category
3. Compare vs baseline using signal rules below
4. 🔴 alerts → notify user; else silent log
5. Save snapshot to `{skill_base_dir}/scan-data/history/{timestamp}.json`, update baseline

## Trend Signals

| Signal | Condition | Level |
|--------|-----------|-------|
| Demand surge | sampleAvgMonthlySales >20% vs baseline | 🔴 |
| Red ocean warning | topBrandSalesRate >70% AND rising | 🔴 |
| New entrant wave | sampleNewSkuRate up >5 percentage points | 🟡 |
| Brand loosening | topBrandSalesRate down >3 percentage points | 🟡 |
| Price band shift | sampleAvgPrice change >10% | 🟡 |
| Margin change | sampleAPlusRate change >5 percentage points | 🟡 |
| Minor movement | None of the above triggered | 🟢 Silent log |

### Trend Interpretation & Action Guide
| Signal Combination | Market Phase | Recommended Action |
|--------------------|-------------|-------------------|
| Demand surge + New entrant wave | 🚀 Growth phase | Enter quickly, first-mover advantage matters 💡 |
| Demand surge + Brand loosening | 🎯 Opportunity window | Best timing — demand up, incumbents losing grip 💡 |
| Demand surge + Red ocean warning | ⚠️ Late stage growth | High demand but leaders consolidating — need strong differentiation 💡 |
| Red ocean warning + No demand surge | 🔒 Mature/locked | Avoid — established players dominate with flat demand 💡 |
| Brand loosening + Price band shift down | 💰 Price war | Wait — margins compressing, enter after shakeout 💡 |
| New entrant wave + Margin change | 🔄 Disruption | Category being redefined — study new entrants' strategies 🔍 |

### Subcategory Ranking Criteria
Rank subcategories by composite attractiveness (apply market-entry scoring logic):
- **Demand**: sampleAvgMonthlySales — higher = more attractive 📊
- **Competition**: topBrandSalesRate — lower = more open 📊
- **Entry barrier**: sampleAvgRatingCount — lower = easier entry 📊
- **Activity**: sampleNewSkuRate — higher = more dynamic 📊
- **Margin signal**: sampleAvgPrice — higher generally = better margins 🔍

## Auto-Monitor

After each Full Scan, ask user to enable scheduled monitoring. If yes, generate cron config with: category list, alert thresholds, schedule. Supports OpenClaw /cron, ChatGPT Scheduled Tasks, Claude Projects. Quick Check only notifies on 🔴 alerts.

## Output Spec

Full Scan: Trend Dashboard (all subcategories) → 🔥 Hot Categories TOP 5 → 🆕 New Entrants Scan → ⚠️ Risk Alerts → Subcategory Detail (per hot category) → Next Steps → Data Provenance → API Usage.

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "CR10 = 54.8% 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "brand concentration is moderate 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "consider entering $10-15 band 💡")

Rules: Strategy recommendations are NEVER 📊. Anomalies (>200% growth) are always 💡. Sample bias note required. User criteria override AI judgment.

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

Full Scan: ~40-60 credits (~2-3 per subcategory × 20). Quick Check: ~20-30 credits (market only).
