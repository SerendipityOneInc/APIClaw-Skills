---
name: Amazon Market Entry Analyzer
version: 1.0.0
description: >
  One-click market viability assessment for Amazon sellers.
  Analyzes market size, competition intensity, brand landscape, pricing structure,
  and consumer pain points to deliver a GO/CAUTION/AVOID recommendation.
  Uses all 11 APIClaw API endpoints with cross-validation for data-backed decisions.
  Use when user asks about: market entry, can I sell, should I enter, market viability,
  is this niche worth it, category analysis, market opportunity, market assessment,
  niche evaluation, product category research.
  Requires APICLAW_API_KEY.
author: SerendipityOneInc
homepage: https://github.com/SerendipityOneInc/APIClaw-Skills
metadata: {"openclaw": {"requires": {"env": ["APICLAW_API_KEY"]}, "primaryEnv": "APICLAW_API_KEY"}}
---

# APIClaw — Amazon Market Entry Analyzer

> One input. Complete market viability assessment. GO / CAUTION / AVOID.
>
> **Language rule**: Always respond in the user's language. Chinese input → Chinese output.
> All API calls go through `scripts/apiclaw.py`.

## Credentials

- Required: `APICLAW_API_KEY`
- Scope: used only for `https://api.apiclaw.io`
- Setup: Guide user to set the environment variable:
  ```bash
  export APICLAW_API_KEY='hms_live_xxxxxx'
  ```
- Get a free key at [apiclaw.io/api-keys](https://apiclaw.io/api-keys) (1,000 free credits on signup, no credit card required)
- Fallback: The script also checks `config.json` in the skill root directory if the env var is not set.
- **Do NOT write keys to disk files.** Always recommend the environment variable approach.
- New keys may need 3-5 seconds to activate — if first call returns 403, wait 3 seconds and retry (max 2 retries).

## File Map

| File | When to Load |
|------|-------------|
| `SKILL.md` (this file) | Always — execution flow + evaluation criteria |
| `scripts/apiclaw.py` | **Execute** for all API calls (do NOT read into context) |
| `references/reference.md` | Need exact field names or response structure |

## Execution Flow

### Step 0 — Parse Input

Extract from user message:
- **keyword** (required): product keyword or niche (e.g. "yoga mat", "wireless earbuds")
- **category** (optional): Amazon category path
- **marketplace** (optional): default US

If only a vague idea given (e.g. "pet products"), ask one clarifying question to narrow scope.

**Input Collection:** If required inputs are missing, ask the user in ONE message:
"To produce a reliable analysis, I need:
 ✅ Required: keyword or categoryPath
 💡 Recommended (significantly improves accuracy): marketplace
 📌 Optional: (none)"

Do NOT proceed until all required inputs are collected.

### Step 0.5 — Category Resolution (mandatory, do not skip)

Before any data collection, lock down the exact product category:

1. **Query categories endpoint** — try the user's keyword first:
   ```bash
   python3 scripts/apiclaw.py categories --keyword "{keyword}"
   ```
2. **If empty or too broad** — split/broaden the keyword and retry (e.g. "yoga mat" → "yoga", then drill into subcategories). Try up to 3 variations.
3. **If still no match** — use realtime/product on a known ASIN to extract categoryPath from its bestsellersRank field.
4. **Validate the categoryPath** — ensure it matches the user's intended product type, not a tangentially related category.

Once a precise categoryPath is confirmed, use it as the primary filter for **ALL** subsequent API calls:
- `markets/search` → use `--category "{categoryPath}"`
- `products/search` → add `--category "{categoryPath}"` alongside keyword
- `brand-overview` → add `--category "{categoryPath}"` alongside keyword
- `brand-detail` → add `--category "{categoryPath}"` alongside keyword
- `price-band-overview` → add `--category "{categoryPath}"` alongside keyword
- `price-band-detail` → add `--category "{categoryPath}"` alongside keyword
- `competitors` → add `--category "{categoryPath}"` alongside keyword

**⚠️ CRITICAL: EVERY endpoint that accepts --category MUST include it.** Without category filtering, keyword-only queries will return cross-category contamination (e.g. "liquid foundation" returns foundation brushes/sponges alongside actual liquid foundation products). This corrupts brand concentration, price structure, and all derived metrics.

Record in the final report's Data Provenance section: the final categoryPath used, how it was resolved, and how many results were filtered out.

### Pre-Execution Checklist

Before proceeding to data collection, verify:
- ✓ `APICLAW_API_KEY` is set and valid
- ✓ categoryPath is locked (from Step 0.5)
- ✓ All required inputs collected (from Step 0)
If any check fails, stop and resolve before continuing.

### Step 1 — Category Discovery + Market Landscape (4 calls)

```bash
# 1a. Find the right category path
python3 scripts/apiclaw.py categories --keyword "{keyword}"
```

Use the most relevant categoryPath from results. Then run simultaneously:

```bash
# 1b. Market aggregate metrics (use categoryPath from 1a)
python3 scripts/apiclaw.py market --category "{categoryPath}" --topn 10

# 1b. Brand landscape overview (MUST include --category to filter out non-target products)
python3 scripts/apiclaw.py brand-overview --keyword "{keyword}" --category "{categoryPath}"

# 1c. Brand detailed ranking (MUST include --category to filter out non-target products)
python3 scripts/apiclaw.py brand-detail --keyword "{keyword}" --category "{categoryPath}"
```

Extract: market size (totalSkuCount, sampleAvgMonthlySales, sampleAvgMonthlyRevenue), competition (topSalesRate, sampleTop10BrandSalesRate (from brand-overview), topBrandSalesRate (from markets/search), topSellerSalesRate), brand count, new SKU rate, FBA rate. Use sampleProducts from brand-detail to analyze each brand's product matrix (SKU spread, price range, BSR distribution). Cross-validate with Step 3 products data.

### Step 2 — Price Structure (2 calls, same keyword)

```bash
# 2a. Price band summary (include --category for precision)
python3 scripts/apiclaw.py price-band-overview --keyword "{keyword}" --category "{categoryPath}"

# 2b. Price band breakdown
python3 scripts/apiclaw.py price-band-detail --keyword "{keyword}" --category "{categoryPath}"
```

Extract: hottest price band, best opportunity band (highest sampleOpportunityIndex), median price, per-band SKU count / sales share / brand concentration / avg rating.

### Step 3 — Product Supply (paginated, min 100 records)

```bash
# 3a. Page 1-5 to get 100 products (MUST include --category to ensure on-category results)
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20 --page 1
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20 --page 2
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20 --page 3
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20 --page 4
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --page-size 20 --page 5
```

Extract: product distribution (price, rating, sales, listing age, fulfillment), Top 5 by sales.

### Step 4 — Top Competitor Deep-Dive (7+ calls)

```bash
# 4a. Competitor list (include --category)
python3 scripts/apiclaw.py competitors --keyword "{keyword}" --category "{categoryPath}" --page-size 20

# 4b. Brand-specific products for top brand from Step 1 (include --category)
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --include-brands "{topBrand}"

# 4c. Realtime detail for Top 5 competitors (5 calls)
python3 scripts/apiclaw.py product --asin {top1_asin}
python3 scripts/apiclaw.py product --asin {top2_asin}
python3 scripts/apiclaw.py product --asin {top3_asin}
python3 scripts/apiclaw.py product --asin {top4_asin}
python3 scripts/apiclaw.py product --asin {top5_asin}
```

Cross-validate realtime data (price, rating, BSR) against Step 3 database data. Note discrepancies.

**DB + Realtime cross-reference principle:** Database data (products/search) provides broad quantitative metrics with ~T+1 delay. Realtime data (realtime/product) provides current qualitative content. Always compare both — discrepancies reveal promotions, listing changes, or data lag. Flag differences explicitly in the report (e.g. "DB price: $21.58, Realtime: $14.43 — likely active promotion").

### Step 5 — Trend Analysis (3 calls)

```bash
# 5a. 30-day history for Top 3 competitors — detect rising/falling market
python3 scripts/apiclaw.py product-history --asins "{top1},{top2},{top3}" --start-date "{30d_ago}" --end-date "{today}"
```

Extract: price trend (rising/stable/falling), BSR trend, sales trend. Determine if market is growing or saturating.

**Quantify trends, don't just label them.** Instead of "price stable" or "BSR rising", calculate and report:
- Price change rate: (latest - earliest) / earliest × 100%
- BSR volatility: (max - min) / average × 100%
- Sales trend direction: regression slope over the period
Use these numbers to support trend labels.

### Step 6 — Consumer Insights (1-3 calls)

```bash
# 6a. Review analysis — pain points + buying factors
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type painPoints,buyingFactors,improvements
```

If category mode fails, fall back to top 3 ASINs:
```bash
python3 scripts/apiclaw.py analyze --asins "{asin1},{asin2},{asin3}"
```

If ASIN mode also fails, fall back to topReviews from Step 4c realtime/product data:
- Extract pain points, buying factors, and sentiment from the topReviews text of Top 5 competitors
- Use ratingBreakdown (star distribution) to gauge overall satisfaction
- This provides directional consumer insights even when reviews/analyze is unavailable

**Always report pain points with proportion.** Do NOT say "Top pain point: durability issues". Instead: "Top pain point: durability issues — mentioned in 27/471 reviews (5.7%), avg rating 2.4 when mentioned." Raw count + total sample + percentage = credibility.

### Step 7 — Price Drill-Down (optional, 1 call)

If best opportunity band identified in Step 2, drill into that price range:
```bash
python3 scripts/apiclaw.py products --keyword "{keyword}" --category "{categoryPath}" --price-min {band_min} --price-max {band_max} --page-size 20
```

### Step 8 — Cross-Validate & Score

Cross-validate data across all 11 data sources. When data conflicts, note the discrepancy.

## Scoring Framework

### Market Viability Score (1-100)

> Methodology based on industry research of Jungle Scout, Helium 10, AMZScout, SmartScout, Viral Launch.
> See `../scoring-methodology.md` for detailed rationale and industry benchmarks.

| Dimension | Weight | Source Endpoints | Good | Medium | Warning |
|-----------|--------|-----------------|------|--------|---------|
| Market Size | 15% | markets/search | >$10M/mo | $5-10M | <$5M |
| Market Trend | 10% | product-history (BSR/sales trend) | Rising | Stable | Declining |
| Competition | 25% | markets + brand-overview + brand-detail + realtime | CR10<40% | 40-60% | >60% |
| Price Opportunity | 15% | price-band-overview + detail | sampleOpportunityIndex>1.0 | 0.5-1.0 | <0.5 |
| New Entrant Space | 10% | markets (newSkuRate) + brand-detail | >15% | 5-15% | <5% |
| Consumer Pain Points | 15% | reviews/analyze | Clear gaps | Some gaps | No gaps |
| Profit Potential | 10% | products (profitMargin, fbaFee) + realtime (buyboxWinner) | >30% margin | 15-30% | <15% |

**Scoring transparency:** In the Scoring Breakdown table, add a "Basis" column explaining WHY each dimension received its score. Example: "Competition: 45/100 — CR10=49.3% falls in 'Medium' range (40-60%), plus 106K review barrier on #1 competitor."

### Final Recommendation

| Score | Signal | Meaning |
|-------|--------|---------|
| 70-100 | ✅ **GO** | Strong opportunity, proceed with product development |
| 40-69 | ⚠️ **CAUTION** | Possible but risky, needs differentiation strategy |
| 0-39 | 🔴 **AVOID** | Too competitive or too small, look elsewhere |

**Output confidence context with every recommendation:**
- State the recommendation with its confidence label (📊/🔍/💡)
- Include: "Based on [X] data points from [Y] endpoints, sample of [Z] products"
- For scores: append "(Confidence: High/Medium/Low — [brief reason])"
- Acknowledge specific data gaps that may affect the conclusion
- End with: "Recommended next step: [specific validation action] before committing resources."

## Output Format

**Every report must begin with this disclaimer:**

> ⚠️ **Important**: This analysis is based on APIClaw API data as of [date]. Sales figures are lower-bound estimates. Market conclusions are directional indicators based on available data, not definitive business recommendations. Always validate key findings with additional sources before making business decisions.

**Confidence labels — every conclusion or recommendation must be tagged with one of:**
**Confidence labels — tag every conclusion with one of:**
- 📊 **Data-backed** / **数据验证** — Supported by API data with cross-validation
- 🔍 **Inferred** / **合理推断** — Reasonable inference, not directly measured
- 💡 **Directional** / **方向参考** — Hypothesis only, verify before acting

Use the label in the user's language: English output → "📊 Data-backed", Chinese output → "📊 数据验证".

**Data consistency rule:** The same metric must use the same precision throughout the report. Do NOT use "10K+" in one table and "47,000" in another for the same product. Pick one level of precision and apply it consistently across all sections.

**Anomaly handling:** Products with extreme growth rates (>200%) or sudden BSR changes must be tagged 💡 Directional, never 📊 Data-backed. Do NOT claim "proves innovation works" or "confirms market opportunity" based on a single product's spike. State: "Product X showed [metric], which MAY indicate [hypothesis]. Further validation needed."

Report sections (all required):
1. **📊 Executive Summary** — Score (1-100), GO/CAUTION/AVOID, one-paragraph verdict
2. **📈 Market Overview** — Market value, SKU count, avg sales/price, new product rate
3. **📉 Market Trend** — 30-day BSR/price/sales trend for Top 3, market direction (rising/stable/declining)
4. **🏷️ Brand Landscape** — Brand count, CR10, Top 5 brands table, entry difficulty
5. **💰 Price Structure** — Hottest/opportunity bands, 5-band table, recommended entry price
6. **🏆 Top 5 Competitors** — Side-by-side comparison (with realtime data), strengths/weaknesses
7. **💬 Consumer Insights** — Top 5 pain points, buying factors, differentiation opportunities
8. **📋 Scoring Breakdown** — 7-dimension table with scores and key data points
9. **🎯 Entry Strategy** — Target price, differentiation angle, expected sales, risks

**Actionable specificity:** If user provided COGS/cost data, calculate and present: break-even units, estimated monthly profit at target price, and timeline to recover initial investment. If COGS not provided, prompt: "Provide your product cost (COGS) for detailed profit simulation."

**Scope acknowledgment:** End every strategy/recommendation section with: "This analysis covers [list dimensions covered]. Dimensions not covered by this data include: advertising costs (CPC/ACoS), search keyword competition, supply chain logistics, and regulatory compliance. Consider supplementing with additional tools before final decisions."
10. **📋 Data Provenance** — Query conditions (keyword, locked categoryPath, marketplace, timestamp), sample coverage (total returned vs post-filter valid vs analyzed), data freshness (DB ~T+1 vs realtime), DB-vs-Realtime discrepancies found, known limitations of this specific analysis

**Sample bias disclosure:** Clearly state in the report body (not just Data Provenance): "This analysis is based on Top [N] products by sales volume, which skews toward established products. New or niche products may be underrepresented."
11. **📊 API Usage & Sample Quality** — Per-endpoint call count with success/fail, total credits consumed, effective sample size after deduplication and category filtering

## ⚠️ Important Notes

- Monthly sales are **lower bound estimates** — actual may be higher
- Database data has ~T+1 delay
- Concentration metrics depend on topN parameter
- reviews/analyze needs 50+ reviews; fall back to top ASINs if category mode fails
- Always paginate products/search to get 100+ records for reliable analysis
- **Never show empty data rows** — omit categories/ASINs with no data entirely
- **Sales estimation fallback**: When `atLeastMonthlySales` is null, estimate using: Monthly Sales ≈ 300,000 / BSR^0.65. Tag as 🔍 **Inferred** / **合理推断** in the report.
- **Never expose internal errors to users** — silently fall back to alternative data sources if an API call fails
- **FORBIDDEN in Data Provenance**: HTTP status codes (422, 500, 403), endpoint failure details, "fallback", "degraded", "retry", internal implementation details. The user should see clean data sourcing, not debugging logs.
