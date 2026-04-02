---
name: Amazon Blue Ocean Product Finder — Untapped Product Discovery
version: 1.0.0
description: >
  Discover untapped, high-demand, low-competition products on Amazon.
  Scans using emerging, underserved, and high-demand-low-barrier modes to find
  blue ocean opportunities. Validates top candidates with all 11 APIClaw endpoints.
  Supports three entry modes: specific market, broad direction, or full-site scan.
  Use when user asks about: blue ocean, find products to sell, untapped niche,
  low competition products, what should I sell, product discovery, hidden gems,
  high demand low competition, find me opportunities, 蓝海产品, 找蓝海.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Blue Ocean Product Finder

> Find untapped products. High demand, low competition, real data. Respond in user's language.

## Files

| File | Purpose |
|------|---------|
| `scripts/apiclaw.py` | **Execute** for all API calls (run `--help` for params) |
| `references/reference.md` | Load for exact field names or response structure |

## Credential

Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys).

## Input & Entry Modes

| Entry Mode | User Says | Action |
|------------|-----------|--------|
| **Specific Market** | "瑜伽垫蓝海" | Resolve category first |
| **Broad Direction** | "家居类蓝海" | Resolve category, expect multiple matches → ask user to pick |
| **Full-Site Scan** | "找蓝海" | Skip category, scan directly |

Optional: price range, FBA/FBM preference. Do NOT ask about budget, supply chain, or experience (no API filters).

## API Pitfalls (CRITICAL)

1. **Category first**: keyword search is broad → MUST lock categoryPath via categories endpoint (except Full-Site Scan)
2. **Brand + category**: Brand queries MUST include `--category`
3. **Use API fields directly**: revenue=`sampleAvgMonthlyRevenue` (NEVER price×sales), sales=`atLeastMonthlySales` (lower bound), opportunity=`sampleOpportunityIndex`
4. **reviews/analyze**: needs 50+ reviews; category mode first, ASIN fallback only if all category calls fail
5. **Aggregation without categoryPath**: severely distorted data
6. **Per-product Price Opportunity**: call `price-band-overview` per unique category of TOP 20 — do NOT reuse one global value
7. **Trend data**: ≥5 points → normal score; 1-4 → cap at 60 + 💡; 0 → fixed 50 + 💡

## Execution

Use `opportunity-scan` composite command with `--modes "emerging,underserved,high-demand-low-barrier"`. Add `--keyword`, `--category`, user filters as applicable. Scans up to 300 products (deduplicated), runs market/brand/price/realtime/history/reviews automatically.

Mode built-in params (combine with user filters, stricter value wins):
- `emerging`: monthlySalesMax=600, growthMin=10%, age≤180d
- `underserved`: monthlySalesMin=300, ratingMax=3.7, age≤180d
- `high-demand-low-barrier`: monthlySalesMin=300, ratingsMax=50, age≤180d

## Blue Ocean Score (1-100)

| Dimension | Weight | Source |
|-----------|--------|--------|
| Demand Signal | 27.5% | `atLeastMonthlySales`: 300-1K→60, 1K-5K→80, 5K-10K→90, >10K→100 |
| Competition Gap | 27.5% | `ratingCount` (realtime): <10→100, 10-30→90, 30-50→80, 50-100→70, >500→0 |
| Price Opportunity | 15% | `sampleOpportunityIndex`: >1.0→100, 0.5-1.0→linear, <0.5→0 |
| Trend Momentum | 15% | product-history BSR/sales direction |
| Profit Margin | 15% | `profitMargin` or fallback: (price-fbaFee)/price, then 1-(0.15+6/price) |

Tiers: 🔥 S(80-100) | ✅ A(60-79) | ⚠️ B(40-59) | ❌ C(0-39)

**NOT blue ocean if**: ratingCount>500 AND CR10>60%; atLeastMonthlySales<50; hottest price band with CR3>50%.

## Output Spec

Sections: Scan Overview → TOP 10 Table → TOP 3 Detailed Analysis (why blue ocean, brand landscape, price positioning, pain points, trend, entry strategy) → Risk Alerts → Scoring Breakdown (TOP 3) → Next Steps → Data Provenance → API Usage.

Confidence labels: 📊 Data-backed | 🔍 Inferred | 💡 Directional. Strategy is NEVER 📊. User criteria override AI judgment.

## API Budget: ~60-80 credits

Products scan(15) + Realtime×20(20) + Brand/Price per category(10-20) + History×5(5) + Reviews(0-3) + Market(1-3) + Categories(1-3).
