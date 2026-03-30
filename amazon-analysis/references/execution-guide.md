# Execution Guide — Complete Protocols

This document contains detailed execution standards for Full-mode analysis.
Load when performing comprehensive product selection, market analysis, or competitor comparison.

---

## Execution Mode

| Task Type | Mode | Behavior |
|-----------|------|----------|
| Single ASIN lookup, simple data query | **Quick** | Execute command, return key data. Skip evaluation criteria and output standard block. |
| Market analysis, product selection, competitor comparison, risk assessment | **Full** | Complete flow: command → analysis → evaluation criteria → output standard block. |

**Quick mode trigger:** User asks for a single specific data point ("B09XXX monthly sales?", "how many brands in cat litter?") — no decision analysis needed.

**Credit-conscious scanning:** For opportunity discovery with limited credits, use 2 modes × 1 page (instead of 5 modes × 5 pages) + brand-overview + price-band-overview ≈ ~10 credits. Label output: "Quick Scan — reduced sample, directional only."

---

## Pre-Execution Checklist (MANDATORY for Full Mode)

Before running any Full-mode product selection or market analysis, **complete this checklist**:

- [ ] **Step 1 — Mode Selection:** Check the Product Selection Mode Mapping table in SKILL.md. If ANY of the 14 preset modes matches the user's intent, **USE IT** (`--mode xxx`). Do NOT manually piece together filters when a preset mode exists.
- [ ] **Step 2 — Realtime Supplement:** Plan to call `product --asin` for the top 3-5 ASINs from results.
- [ ] **Step 3 — Review Analysis:** Plan to call `analyze --asins` for top ASINs to get consumer insights (especially painPoints, improvements, buyingFactors).
- [ ] **Step 4 — Output Blocks:** Prepare to include Disclaimer, Confidence Labels, Data Provenance, and API Usage.

---

## parentAsin Handling

If `realtime/product` returns null fields (common for variant/child ASINs), use `products/search --keyword "{asin}"` to find the parentAsin, then re-fetch with the parent ASIN. Do not report null data — always attempt parent resolution first.

---

## Leader/Benchmark Deduplication

When selecting Top 5 products for benchmarking or comparison, deduplicate by parentAsin — if multiple results share the same parent (color/size variants), keep only the highest-selling variant. The goal is 5 distinct products, not 5 variants of the same listing.

---

## Competitors Fallback

If competitors endpoint returns empty results (common with broad keywords), rely on `products/search` sorted by sales as the competitor discovery source. Do not expose the issue to users.

---

## Review Analysis Protocols

### Independent Brand Analysis
When comparing multiple brands, analyze each brand's ASIN separately — do NOT combine ASINs from different brands in a single `analyze` call. Mixed-ASIN analysis produces averaged insights that hide competitive differences and cannot be attributed to specific brands.

### Fallback for Insufficient Reviews
If `analyze` returns insufficient data (requires 50+ reviews), silently fall back to `realtime/product` topReviews + ratingBreakdown data. Extract pain points, buying factors, and sentiment from the raw review text. Never expose API errors to users.

### Review Fallback Chain
`realtime/product` provides topReviews (raw text) + ratingBreakdown (star distribution). When reviews/analyze is unavailable (insufficient reviews), use these as the consumer insight source. Cross-validate: compare positive_sentiment% from analyze against (4+5 star)% from ratingBreakdown — if gap > 15%, flag potential discrepancy.

---

## Realtime Data Supplementation

When `products` or `competitors` returns ASINs in Full-mode analysis, call `product --asin` for the top 3-5 most relevant ASINs to get current real-time data. For bulk lookups (>3 ASINs), confirm with the user before proceeding.

**When to supplement**: Product selection / competitor analysis → top 3 by sales. Risk assessment → target + top 2 competitors. Multi-product comparison → all compared ASINs (max 5). Skip for: single ASIN lookup, market overview, listing analysis.

**Data conflict rule**: `products`/`competitors` = ~T+1 delay; `realtime/product` = live. Use realtime for price/BSR/rating; use products/competitors for sales/margin/fees. Note significant differences: "⚡ Price updated: $29.99 → $24.99 (likely promotion)"

---

## Category Resolution — Detailed Flow

1. Query categories endpoint with the user's keyword
2. If empty or too broad, split/broaden keyword and retry (up to 3 variations)
3. If still no match, use realtime/product on a known ASIN to extract categoryPath
4. Validate categoryPath matches the user's intended product type

**Data-driven category selection:** When the user provides a broad interest (e.g. "home products") instead of a specific niche, do NOT pick categories from general knowledge. Use `market` endpoint to scan subcategories, then rank by composite score: newSkuRate > 10%, topBrandSalesRate < 60%, sampleFbaRate > 50%, sampleAvgPrice $10-$50. Select Top 3-5 subcategories for deeper analysis.

---

## Growth Signal Validation

- A single product's high growth rate (e.g. +900%) may be seasonal rebound, restock recovery, or promotion spike — NOT necessarily a market trend
- To validate: check if the MAJORITY of products in the category show positive growth, not just 1-2 outliers
- Flag seasonal patterns explicitly: "This growth coincides with [season], which may be temporary"
- Mark single-product growth signals as 💡 **Directional** / **方向参考**, not 📊 **Data-backed** / **数据验证**

---

## Alert Signal Tiers (for monitoring scenarios)

- 📊 **Sustained trend** — multiple data points over 7+ days showing consistent direction
- 🔍 **Possible signal** — 2-3 days of change, needs more observation
- 💡 **Single-day spike** — could be promotion, restock, or data lag; do not treat as confirmed trend

---

## Sales Estimation Fallback

When `atLeastMonthlySales` is null: **Monthly sales ≈ 300,000 / BSR^0.65**

---

## Output Standards — Full Specification

**Data consistency rule:** The same metric must use the same precision throughout the report. Do NOT use "10K+" in one table and "47,000" in another for the same product. Pick one level of precision and apply it consistently across all sections.

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."

**Anomaly handling:** Products with extreme growth rates (>200%) or sudden BSR changes must be tagged 💡 Directional, never 📊 Data-backed. Do NOT claim "proves innovation works" or "confirms market opportunity" based on a single product's spike. State: "Product X showed [metric], which MAY indicate [hypothesis]. Further validation needed."

### Disclaimer (every Full-mode report)

> ⚠️ **Important**: This analysis is based on APIClaw API data as of [date]. Sales figures are lower-bound estimates. Market conclusions are directional indicators based on available data, not definitive business recommendations. Always validate key findings with additional sources before making business decisions.

### Confidence Labels (every conclusion must be tagged)

**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

### Data Provenance Block (Full Mode Only)

```markdown
---
📋 **Data Provenance**
| Item | Value |
|------|-------|
| Query Keyword | [keyword used] |
| Locked CategoryPath | [resolved category] |
| Category Resolution | [how many attempts, final path] |
| Marketplace | [US/etc] |
| Timestamp | [date] |
| Sample Size | [total returned / post-filter valid / analyzed] |
| Data Freshness | DB data ~T+1, realtime = live |
| Endpoints Used | [list with call count] |
| Credits Consumed | [total] |
| Known Limitations | [list any gaps] |
```

**Rules**:
1. Every Full-mode analysis MUST end with this block
2. Filter conditions MUST list specific parameter values
3. If multiple interfaces used, list each one
4. If data has limitations, proactively explain
5. ⚠️ **Self-check:** scan your response — if you don't see `📋 **Data Provenance**`, ADD IT before replying

### API Usage Summary (All Modes — MANDATORY)

```markdown
📊 **API Usage**
| Interface | Calls |
|-----------|-------|
| categories | 1 |
| markets/search | 1 |
| products/search | 2 |
| realtime/product | 3 |
| reviews/analyze | 1 |
| **Total** | **8** |
| **Credits consumed** | **8** |
| **Credits remaining** | **492** |
```

**Tracking rules:**
1. Count each `apiclaw.py` execution as 1 call to the corresponding interface
2. Sum `_credits.consumed` from every API response for total consumed
3. Use `_credits.remaining` from the **last** API response as remaining balance
4. If `_credits` fields are null, show "N/A"
5. ⚠️ **Self-check before sending:** scan your response — if you don't see `📊 **API Usage**` at the bottom, ADD IT before replying

---

## Interface Data Differences

The interfaces return **different fields**. Do NOT assume they share the same structure.

| Data | `market` | `products`/`competitors` | `realtime/product` | `reviews/analyze` | `price-band` | `brand` | `product-history` |
|------|----------|--------------------------|--------------------|--------------------|-------------|---------|-------------------|
| Monthly Sales | `sampleAvgMonthlySales` | `atLeastMonthlySales` | ❌ | ❌ | per-band avg | per-brand | historical |
| Revenue | `sampleAvgMonthlyRevenue` | `salesRevenue` | ❌ | ❌ | ❌ | ❌ | ❌ |
| Price | `sampleAvgPrice` | `price` | `buyboxWinner.price` | ❌ | band range | ❌ | historical |
| BSR | `sampleAvgBsr` | `bsrRank` (integer) | `bestsellersRank` (array) | ❌ | ❌ | ❌ | historical |
| Rating | `sampleAvgRating` | `rating` | `rating` | `avgRating` | ❌ | ❌ | historical |
| Review Count | `sampleAvgReviewCount` | `ratingCount` | `ratingCount` | `totalReviews` | ❌ | ❌ | ❌ |
| Sentiment | ❌ | ❌ | ❌ | `sentimentDistribution` | ❌ | ❌ | ❌ |
| Consumer Insights | ❌ | ❌ | ❌ | `consumerInsights` (11 dims) | ❌ | ❌ | ❌ |
| Brand Share | ❌ | ❌ | ❌ | ❌ | ❌ | `sampleTop10BrandSalesRate` | ❌ |
| Opportunity Index | ❌ | ❌ | ❌ | ❌ | `sampleOpportunityIndex` | ❌ | ❌ |
| Seller | ❌ | `buyboxSeller` (string) | `buyboxWinner` (object) | ❌ | ❌ | ❌ | ❌ |
| Profit Margin | ❌ | `profitMargin` | ❌ | ❌ | ❌ | ❌ | ❌ |
| Features/Bullets | ❌ | ❌ | `features` | ❌ | ❌ | ❌ | ❌ |

**Usage rule:**
- `products`/`competitors` → sales, pricing, competition
- `realtime/product` → review details, listing content, seller info
- `market` → category-level aggregates
- `reviews/analyze` → AI-powered review insights (all reviews, not just topReviews)
- `price-band-*` → price segment analysis and opportunity
- `brand-*` → brand landscape and concentration
- `product-history` → historical trends
- For reports: combine quantitative + qualitative + consumer insights + market structure

## Common Field Name Mistakes

- `reviewCount` → use `ratingCount`
- `bsr` → use `bsrRank` (products/competitors) or `bestsellersRank` (realtime, array)
- `monthlySales` → use `atLeastMonthlySales`
- realtime price → `buyboxWinner.price`
- realtime has NO `profitMargin`
- See `reference.md` → Shared Product Object for complete field list

## Data Structure Reminder

All interfaces return `.data` as an **array**. Use `.data[0]` to get the first record, NOT `.data.fieldName`.

---

## Error Handling

Errors are handled by the script with structured JSON output. **Never expose error details to users.**
Self-check: `python3 scripts/apiclaw.py check`

| Error | Fix |
|-------|-----|
| `Cannot index array with string` | Use `.data[0].fieldName` (`.data` is array) |
| Empty `data: []` | Use `categories` to confirm category exists |
| `atLeastMonthlySales: null` | BSR estimate: 300,000 / BSR^0.65 |

**FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.

---

## API Coverage Boundaries

| Scenario | Coverage | Suggestion |
|----------|----------|------------|
| Market data: Popular keywords | ✅ Has data | Use `--keyword` directly |
| Market data: Niche/long-tail keywords | ⚠️ May be empty | Use `--category` instead |
| Product data: Active ASIN | ✅ Has data | — |
| Product data: Delisted/variant ASIN | ❌ No data | Try parent ASIN or realtime |
| Real-time data: US site | ✅ Full support | — |
| Real-time data: Non-US sites | ⚠️ Partial | Core fields OK, sales may be null |
