---
name: Amazon Market Trend Scanner — Daily Category Radar
version: 1.0.0
description: >
  Scan Amazon category landscapes to discover trending subcategories,
  emerging niches, and market shifts. Complements Daily Market Radar
  (defensive monitoring) with offensive trend discovery for product
  selection and market entry timing. Tracks demand surges, brand
  consolidation, new entrant waves, price band migration, and margin
  changes across all subcategories under a parent category.
  Use when user asks about: market trends, category trends, trending
  categories, what's hot, emerging categories, trend scanner,
  category trends, market trends, which categories are growing.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Market Trend Scanner

> Find rising categories before everyone else. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `references/reference.md` | Load for exact field names or response structure |
| `scan-data/` | Runtime: watchlist.json, baseline.json, alerts.json, history/ (auto-created) |

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
6. Save baseline → `scan-data/baseline.json`, config → `scan-data/watchlist.json`
7. Output full trend report (see Output Spec)
8. Offer Auto-Monitor setup

## Mode 2: Quick Check (scheduled)

1. Read `scan-data/watchlist.json` + `scan-data/baseline.json`
2. `market --category "{path}"` per watched category
3. Compare vs baseline using signal rules below
4. 🔴 alerts → notify user; else silent log
5. Save snapshot to `scan-data/history/{timestamp}.json`, update baseline

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

## Auto-Monitor

After each Full Scan, ask user to enable scheduled monitoring. If yes, generate cron config with: category list, alert thresholds, schedule. Supports OpenClaw /cron, ChatGPT Scheduled Tasks, Claude Projects. Quick Check only notifies on 🔴 alerts.

## Output Spec

Full Scan: Trend Dashboard (all subcategories) → 🔥 Hot Categories TOP 5 → 🆕 New Entrants Scan → ⚠️ Risk Alerts → Subcategory Detail (per hot category) → Next Steps → Data Provenance → API Usage.

Confidence labels: 📊 Data-backed | 🔍 Inferred | 💡 Directional. Sample bias note required.

## API Budget

Full Scan: ~40-60 credits (~2-3 per subcategory × 20). Quick Check: ~20-30 credits (market only).
