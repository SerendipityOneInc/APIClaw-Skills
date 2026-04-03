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
- **Script**: `scripts/apiclaw.py` (execute, don't read) — run `--help` for params
- **Reference**: `references/reference.md` (field names & response structure)

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
- Sales = `atLeastMonthlySales` (lower bound)
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

## Output
Respond in user's language. Tag every conclusion: 📊 Data-backed / 🔍 Inferred / 💡 Directional.

**Per ASIN**: Price Signal (RAISE/HOLD/LOWER) → Current Position in Category → Price Band Heatmap (with Sales/Competition Ratio) → Competitor Price Map (top 10 in leaf category) → 30-Day Trend → Profit Simulation (3 scenarios) → BuyBox Analysis → Recommended Price.

**Batch summary** (if multiple ASINs): Overview table (ASIN | Product | Category | Current Price | Signal | Recommended) → Per-ASIN detail.

End with: Data Provenance → API Usage. Begin with disclaimer. Flag DB vs Realtime discrepancies as likely promotions.

## API Budget
- Single ASIN: ~20-25 credits
- Batch N ASINs (same category): ~20-25 + 1 per additional ASIN
- Batch N ASINs (different categories): ~20-25 per unique category
