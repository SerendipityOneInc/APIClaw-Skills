---
name: Dynamic Pricing Intelligence Agent
version: 1.1.0
description: >
  Data-driven pricing strategy engine for Amazon sellers.
  Give me your ASIN(s) — I auto-detect the leaf category, analyze pricing landscape,
  and deliver RAISE/HOLD/LOWER signals with profit simulation.
  Supports single ASIN or batch (multiple ASINs, auto-grouped by category).
  Uses APIClaw API endpoints with cross-validation.
  Use when user asks about: pricing strategy, how much to price, optimal price,
  price optimization, competitor pricing, price war, BuyBox strategy,
  profit margin, pricing analysis, should I raise price, should I lower price,
  price comparison, price positioning, repricing, pricing strategy, should I raise or lower price.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# Dynamic Pricing Intelligence Agent — RAISE / HOLD / LOWER

Give me your ASIN(s). I'll tell you whether to raise, hold, or lower — with data.

## Files
- **Script**: `{skill_base_dir}/scripts/apiclaw.py` — run `--help` for params
- **Reference**: `{skill_base_dir}/references/reference.md` (field names & response structure)

## Credential
Required: `APICLAW_API_KEY`. Get free key at [apiclaw.io/api-keys](https://apiclaw.io/en/api-keys)

## Input
- **Required**: one or more ASINs (your products). No keyword needed — category is auto-detected.
- **Optional**: competitor_asins

On first interaction, tell user: "Give me your ASIN(s). I support single or batch analysis — I'll auto-detect each product's category and analyze the pricing landscape for you."

## Auto Category Detection (CRITICAL — replaces manual keyword input)

1. For each ASIN: `product --asin {asin}` → extract `bestsellersRank` array
2. The **last entry** in `bestsellersRank` = leaf (most specific) category
3. Use leaf category name → `categories --keyword "{leaf_category_name}"` → get `categoryPath`
4. If categories returns empty, try the second-to-last BSR entry, or ask user
5. **Batch mode**: group ASINs by leaf category → share market data within same category (saves credits)

## API Pitfalls
- Revenue = `sampleAvgMonthlyRevenue` directly. **NEVER** calculate price×sales.
- Sales = `monthlySalesFloor` (lower bound)
- Price in realtime: `buyboxWinner.price`, NOT top-level `price`
- **All keyword-based endpoints MUST include `--category`** once categoryPath is locked
- FBA fees from products/search are estimates — verify with Amazon FBA calculator
- Aggregation endpoints without categoryPath produce severely distorted data

## Pricing Signal Logic

| Signal | Condition |
|--------|-----------|
| **RAISE** | Price below opportunity band AND rating ≥ category avg AND BSR stable/rising |
| **HOLD** | Price in optimal band AND BSR stable AND no competitor price war |
| **LOWER** | Price above hottest band AND BSR declining OR competitor undercut detected |

### New Seller Price Band Selection
Don't pick highest-sales band. Calculate per band:
**Sales/Competition Ratio = Avg Monthly Sales ÷ Avg Review Count**
Highest ratio = best entry point (strong demand + low review barriers).

### Profit Simulation
3 scenarios: Conservative (current price), Moderate (±$1-2), Aggressive (±$3-5).
Per scenario: Revenue = Price × Est. Sales − FBA Fee − Referral Fee (15%) − COGS = Net Profit & Margin.

### Profit Margin Interpretation
| Net Margin | Signal | Interpretation |
|------------|--------|---------------|
| >30% | 🟢 Healthy | Strong margin, room for ad spend and promotions 📊 |
| 15-30% | 🟡 Acceptable | Viable but monitor costs closely 🔍 |
| 5-15% | 🟠 Thin | One price war or cost increase away from loss 🔍 |
| <5% | 🔴 Unsustainable | Must raise price, cut costs, or exit 💡 |

### Price Position Analysis
- **Price < opportunity band min**: Underpriced — likely leaving money on the table if rating ≥ category avg 🔍
- **Price in opportunity band**: Optimal zone — hold unless competitors shift 🔍
- **Price in hottest band**: Maximum volume zone — high competition, margin pressure likely 🔍
- **Price > hottest band max**: Premium positioning — only viable with strong brand/reviews 🔍
- **DB price ≠ Realtime price** (>5% diff): Likely running a promotion or coupon — flag as temporary 📊

## Output
Respond in user's language.

**Per ASIN**: Price Signal (RAISE/HOLD/LOWER) → Current Position in Category → Price Band Heatmap (with Sales/Competition Ratio) → Competitor Price Map (top 10 in leaf category) → 30-Day Trend → Profit Simulation (3 scenarios) → BuyBox Analysis → Recommended Price.

**Batch summary** (if multiple ASINs): Overview table (ASIN | Product | Category | Current Price | Signal | Recommended) → Per-ASIN detail.

End with: Data Provenance → API Usage. Flag DB vs Realtime discrepancies as likely promotions.

### Language (required)

Output language MUST match the user's input language. If the user asks in Chinese, the entire report is in Chinese. If in English, output in English. Exception: API field names (e.g. `monthlySalesFloor`, `categoryPath`), endpoint names, technical terms (e.g. ASIN, BSR, CR10, FBA, credits) remain in English.

### Disclaimer (required, at the top of every report)

> Data is based on APIClaw API sampling as of [date]. Monthly sales (`monthlySalesFloor`) are lower-bound estimates. This analysis is for reference only and should not be the sole basis for business decisions. Validate with additional sources before acting.

### Confidence Labels (required, tag EVERY conclusion)

- 📊 **Data-backed** — direct API data (e.g. "current price $12.99 📊")
- 🔍 **Inferred** — logical reasoning from data (e.g. "price is below opportunity band 🔍")
- 💡 **Directional** — suggestions, predictions, strategy (e.g. "consider raising to $14.99 💡")

Rules: Strategy recommendations and price signals (RAISE/HOLD/LOWER) are NEVER 📊. User criteria override AI judgment.

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
- Single ASIN: ~20-25 credits
- Batch N ASINs (same category): ~20-25 + 1 per additional ASIN
- Batch N ASINs (different categories): ~20-25 per unique category
