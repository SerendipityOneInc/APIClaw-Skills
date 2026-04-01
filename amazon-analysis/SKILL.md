---
name: Amazon Analysis — Full-Spectrum Research & Seller Intelligence
version: 1.1.4
description: >
  Amazon seller data analysis tool. Features: market research, product selection, competitor analysis, ASIN evaluation, pricing reference, category research.
  Uses scripts/apiclaw.py to call APIClaw API, requires APICLAW_API_KEY.
---

# APIClaw — Amazon Seller Data Analysis

> AI-powered Amazon product research. From market discovery to daily operations.
>
> **Language rule**: Always respond in the user's language. If the user asks in Chinese, reply in Chinese. If in English, reply in English. The language of this skill document does not affect output language.
> All API calls go through `scripts/apiclaw.py` — one script, 5 endpoints, built-in error handling.

## Credentials

- Required: `APICLAW_API_KEY`
- Scope: used only for `https://api.apiclaw.io`
- Storage: `config.json` in the skill directory (same folder as SKILL.md)

### API Key Configuration Mechanism

**Config file location:** `config.json` in the skill root directory, next to `SKILL.md`.

```
apiclaw-analysis-skill/
├── config.json          ← API Key stored here
├── SKILL.md
├── scripts/
│   └── apiclaw.py
└── references/
```
**Config file format:**
```json
{
  "api_key": "hms_live_xxxxxx"
}
```

### Initial Setup (AI Operation Guide)

When user first uses or provides new Key, AI should execute:

```python
import os, json
# config.json is stored in the skill root directory (parent of scripts/)
skill_dir = os.path.dirname(os.path.abspath(__file__))  # when running from scripts/
skill_dir = os.path.dirname(skill_dir)  # go up to skill root
config_path = os.path.join(skill_dir, "config.json")
with open(config_path, "w") as f:
    json.dump({"api_key": "hms_live_user_provided_key"}, f, indent=2)
print(f"API Key saved to {config_path}")
```


### Get API Key

**New users please first obtain API Key:**

1. Visit [APIClaw Console](https://apiclaw.io/en/api-keys) to register account
2. Create API Key, copy it (format: `hms_live_xxxxxx`)
3. Tell the AI your Key in conversation, AI will automatically save it to config file

**New Key first use note:** Newly configured API Key may need 3-5 seconds to fully activate in backend. If first call returns 403 error, AI should wait 3 seconds then retry, max 2 retries.

## File map

| File | When to use |
|------|-------------|
| `SKILL.md` (this file) | Start here — covers 80% of tasks |
| `scripts/apiclaw.py` | **Execute** for all API calls (do not read into context) |
| `references/reference.md` | Load when you need exact field names or filter details |
| `references/scenarios.md` | Load for pricing, daily operations, or expansion scenarios (5.x/6.x/7.x) |

### Reference File Usage Guide (Important)

**Must load reference files in these scenarios**:

| Scenario | Load File | Reason |
|----------|-----------|---------|
| Need to confirm field names | `reference.md` | Avoid field name errors (e.g. ratingCount vs ratingMonthlyNew)|
| Need filter parameter details | `reference.md` | Get complete Min/Max parameter list |
| Pricing strategy analysis | `scenarios.md` | Contains pricing SOP and reference framework |
| Daily operations analysis | `scenarios.md` | Contains monitoring and alert logic |
| Product expansion analysis | `scenarios.md` | Contains related recommendation logic |

**Don't guess field names**: If uncertain about an interface's return fields, load `reference.md` first to check.

---

## Execution Standards

**Prioritize script execution for API calls.** The script includes built-in:
- Parameter format conversion (e.g. topN automatically converted to string)
- Retry logic (429/timeout auto-retry)
- Standardized error messages
- `_query` metadata injection (for query condition traceability)

**macOS note**: macOS doesn't have `python` command by default, use `python3`. Replace `python` in example commands with `python3`.

**Fallback plan:** If script execution fails and can't be quickly fixed, can use curl to call API directly as temporary solution, but note "this time using curl direct call" in output.

---

## Script usage

All commands output JSON. Progress messages go to stderr.

### categories — Category tree lookup

```bash
python scripts/apiclaw.py categories --keyword "pet supplies"
python scripts/apiclaw.py categories --parent "Pet Supplies"
python scripts/apiclaw.py categories                          # root categories
```

Common fields: `categoryName` (not `name`), `categoryPath`, `productCount`, `hasChildren`

### market — Market-level aggregate data

```bash
python scripts/apiclaw.py market --category "Pet Supplies,Dogs" --topn 10
python scripts/apiclaw.py market --keyword "treadmill"
```

Key output fields: `sampleAvgMonthlySales`, `sampleAvgPrice`, `topSalesRate` (concentration), `topBrandSalesRate`, `sampleNewSkuRate`, `sampleFbaRate`, `sampleBrandCount`, `sampleNewSkuAvgPrice` (new product avg price), `sampleNewSkuAvgMonthlySaleCnt` (new product avg sales), `sampleNewSkuAvgRatingAmt` (new product avg rating), `sampleNewSkuAvgRatingCnt` (new product avg rating count), `sampleNewSkuCount` (new product count), `sampleNewSkuRate` (new product rate)

### products — Product selection with filters

```bash
# Use a preset mode (14 built-in modes)
python scripts/apiclaw.py products --keyword "yoga mat" --mode beginner
python scripts/apiclaw.py products --keyword "pet toys" --mode high-demand-low-barrier

# Or use explicit filters
python scripts/apiclaw.py products --keyword "yoga mat" --sales-min 300 --ratings-max 50
python scripts/apiclaw.py products --keyword "yoga mat" --growth-min 0.1 --listing-age 180

# Combine mode + overrides (overrides win)
python scripts/apiclaw.py products --keyword "yoga mat" --mode beginner --price-max 30
```

Available modes: `fast-movers`, `emerging`, `single-variant`, `high-demand-low-barrier`, `long-tail`, `underserved`, `new-release`, `fbm-friendly`, `low-price`, `broad-catalog`, `selective-catalog`, `speculative`, `beginner`, `top-bsr`

### competitors — Competitor lookup

```bash
python scripts/apiclaw.py competitors --keyword "wireless earbuds"
python scripts/apiclaw.py competitors --brand "Anker"
python scripts/apiclaw.py competitors --asin B09V3KXJPB
```

**products/competitors shared fields (easily confused)**:

| ❌ Common Error | ✅ Correct Field | Description |
|------------|------------|------|
| `reviewMonthlyNew` | `ratingMonthlyNew` | Monthly new ratings (renamed) |
| `bsr` | `bsrRank` | BSR ranking |
| `monthlySales` | `salesMonthly` | Monthly sales |

Common fields: `salesMonthly`, `bsrRank`, `ratingCount`, `rating`, `salesGrowthRate`, `listingDate`, `price`, `brand`, `categories`

> Complete field list see `reference.md` → Shared Product Object

### product — Single ASIN real-time detail

```bash
python scripts/apiclaw.py product --asin B09V3KXJPB
python scripts/apiclaw.py product --asin B09V3KXJPB --marketplace JP
```

Returns: title, brand, rating, ratingBreakdown, features (bullets), specifications, variants, bestsellersRank, buyboxWinner

### report — Full market analysis (composite)

```bash
python scripts/apiclaw.py report --keyword "pet supplies"
```

Runs automatically: categories → market → products (top 50) → realtime detail (top 1). Returns combined JSON.

### opportunity — Product opportunity discovery (composite)

```bash
python scripts/apiclaw.py opportunity --keyword "pet supplies"
python scripts/apiclaw.py opportunity --keyword "pet supplies" --mode fast-movers
```

Runs: categories → market → products (filtered) → realtime detail (top 3). Returns combined JSON.

---

## Return Data Structure

**Important**: The `.data` field returned by all interfaces is an **array**, not an object. When parsing, use `.data[0]` to get the first record.

```bash
# Correct ✅
jq '.data[0].topSalesRate'

# Error ❌ - will report "Cannot index array with string"
jq '.data.topSalesRate'
```

**Batch processing example**:
```bash
# Iterate through all records
jq '.data[] | {name: .categoryName, sales: .sampleAvgMonthlySales}'

# Take first 5
jq '.data[:5] | .[] | .title'
```

---

## Intent routing

| User says | Run this | Extra file? |
|-----------|----------|-------------|
| "which category has opportunity" | `market` (+ `categories` to confirm path) | No |
| "help me check B09XXX" / "analyze ASIN" | `product --asin XXX` | No |
| "Chinese sellers cases" | `competitors --keyword XXX --page-size 50` | `scenarios.md` → 3.4 |
| **Product Evaluation** | | |
| "pain points" / "negative reviews" | `product --asin XXX` | `scenarios.md` → 4.2 |
| "compare products" | `competitors` or multiple `product` | `scenarios.md` → 4.3 |
| "risk assessment" / "can I do this" / "risk" | `product` + `market` + `competitors` | `scenarios.md` → 4.4 |
| "monthly sales" / "sales estimate" | `competitors --asin XXX` | `scenarios.md` → 4.5 |
| "help me with product selection" / "find products" | `products --mode XXX` (see mode table below) | No |
| "comprehensive recommendations" / "help me choose" / "what should I sell" | `products` (multi-mode) + `market` | `scenarios.md` → 2.10 |

**Product selection mode mapping (14 types)**:

| User Intent | Mode | Filter Conditions |
|----------|------|----------|
| "underserved market" / "has pain points" / "can improve" | `--mode underserved` | Monthly sales≥300, rating≤3.7, within 6 months |
| "high demand low barrier" / "easy to do" / "easy entry" | `--mode high-demand-low-barrier` | Monthly sales≥300, ratings≤50, within 6 months |
| "beginner friendly" / "suitable for new sellers" / "entry level" | `--mode beginner` | Monthly sales≥300, $15-60, FBA |
| "fast turnover" / "good sellers" / "hot selling" | `--mode fast-movers` | Monthly sales≥300, growth≥10% |
| "emerging products" / "rising period" | `--mode emerging` | Monthly sales≤600, growth≥10%, within 6 months |
| "small but beautiful rising single products" / "single variant" | `--mode single-variant` | Growth≥20%, variants=1, within 6 months |
| "long tail products" / "niche" / "segmented" | `--mode long-tail` | BSR 10K-50K, ≤$30, exclusive sellers |
| "new products" / "just launched" / "new release" | `--mode new-release` | Monthly sales≤500, New Release tag |
| "low price products" / "cheap" | `--mode low-price` | ≤$10 |
| "top sellers" / "best sellers" / "top seller" | `--mode top-bsr` | BSR≤1000 |
| "self-fulfillment friendly" / "FBM" | `--mode fbm-friendly` | Monthly sales≥300, FBM |
| "broad catalog mode" / "cast wide net" | `--mode broad-catalog` | BSR growth≥99%, ratings≤10, within 90 days |
| "selective catalog" | `--mode selective-catalog` | BSR growth≥99%, within 90 days |
| "speculative" / "piggyback selling opportunities" | `--mode speculative` | Monthly sales≥600, sellers≥3 |
| "complete report" / "full report" | `report --keyword XXX` | No |
| "product opportunity" / "opportunity" | `opportunity --keyword XXX` | No |
| **Pricing & Listing** | | |
| "how much to price" / "pricing strategy" | `market` + `products` | `scenarios.md` → 5.1 |
| "profit estimation" / "profit margin" | `competitors` | `scenarios.md` → 5.2 |
| "how to write listing" / "listing reference" | `product --asin XXX` | `scenarios.md` → 5.3 |
| **Daily Operations** | | |
| "recent changes" / "market changes" | `market` + `products` | `scenarios.md` → 6.1 |
| "what are competitors doing recently" / "competitor updates" | `competitors --brand XXX` | `scenarios.md` → 6.2 |
| "anomaly alerts" / "alerts" | `market` + `products` | `scenarios.md` → 6.4 |
| **Expansion** | | |
| "what else can I sell" / "related products" | `categories` + `market` | `scenarios.md` → 7.1 |
| "trends" | `products --growth-min 0.2` | `scenarios.md` → 7.3 |
| "should I delist" / "discontinue" | `competitors --asin XXX` + `market` | `scenarios.md` → 7.4 |
| **Reference** | | |
| Need exact filters or field names | — | Load `reference.md` |

---

## Quick evaluation criteria

### Market viability (from `market` output)

| Metric | Good | Medium | Warning |
|--------|------|--------|---------|
| Market value (avgRevenue × skuCount) | > $10M | $5–10M | < $5M |
| Concentration (topSalesRate, topN=10) | < 40% | 40–60% | > 60% |
| New SKU rate (sampleNewSkuRate) | > 15% | 5–15% | < 5% |
| FBA rate (sampleFbaRate) | > 50% | 30–50% | < 30% |
| Brand count (sampleBrandCount) | > 50 | 20–50 | < 20 |

### Product potential (from `product` output)

| Metric | High | Medium | Low |
|--------|------|--------|-----|
| BSR | Top 1000 | 1000–5000 | > 5000 |
| Rating count | < 200 | 200–1000 | > 1000 |
| Rating | > 4.3 | 4.0–4.3 | < 4.0 |
| Negative reviews (1-2 star %) | < 10% | 10–20% | > 20% |

### Sales estimation fallback

When `salesMonthly` is null: **Monthly sales ≈ 300,000 / BSR^0.65**

---

## Output Standards (Mandatory)

**Must include data source block after every analysis completion**, otherwise output is considered incomplete:

```markdown
---
**Data Source & Conditions**
| Item | Value |
|----|-----|
| Data Source | APIClaw API |
| Interface | [List interfaces used this time, e.g. categories, markets/search, products/search] |
| Category | [Queried category path] |
| Time Range | [dateRange, e.g. 30d] |
| Sampling Method | [sampleType, e.g. by_sale_100] |
| Top N | [topN value, e.g. 10] |
| Sort | [sortBy + sortOrder, e.g. monthlySales desc] |
| Filter Conditions | [Specific parameter values, e.g. monthlySalesMin: 300, ratingCountMax: 50] |

**Data Notes**
- Monthly sales are **estimated values** based on BSR + sampling model, not official Amazon data
- Database interface data has ~T+1 delay, realtime/product is current real-time data
- Concentration metrics calculated based on Top N sample, different topN values will yield different results
```

**Rules**:
1. Must include this block after every analysis
2. Filter conditions should be specific to parameter values (e.g. `monthlySalesMin: 300, ratingCountMax: 50`)
3. If multiple interfaces used, list each one
4. If data has limitations (e.g. missing historical trends), proactively explain

---

## Limitations

### What this skill cannot do

- Keyword research / reverse ASIN / ABA data
- Traffic source analysis
- Historical sales trends (14-month curves)
- Historical price / BSR charts
- Raw individual review text (topReviews removed from realtime/product; use reviews/analyze for structured insights)

### API Data Coverage Boundaries

| Scenario | Coverage | Suggestion |
|----------|----------|------------|
| Market data: Popular keywords | ✅ Usually has data | Use `--keyword` query directly |
| Market data: Niche/long-tail keywords | ⚠️ May have no data | Use category path `--category` query instead |
| Product data: Active ASIN | ✅ Has data | - |
| Product data: Delisted/variant ASIN | ❌ No data | Try parent ASIN or realtime interface |
| Real-time data: US site | ✅ Full support | - |
| Real-time data: Non-US sites | ⚠️ Some fields missing | Core fields available, sales estimation may be empty |

---

## reviews/analyze Fallback Rules

**⚠️ labelType only accepts ONE value per call — do NOT comma-separate multiple types.**

When using `reviews/analyze` for consumer insights (pain points, buying factors, improvements, etc.), follow this priority chain:

**Priority 1 — Category mode (ALWAYS try this first, 3 calls):**
```bash
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type painPoints
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type buyingFactors
python3 scripts/apiclaw.py analyze --category "{categoryPath}" --label-type improvements
```
Category mode analyzes ALL reviews in the category (can be 100K+ reviews). This is the richest data source.

**Priority 2 — ASIN mode (ONLY if ALL 3 category calls fail):**
```bash
# Pick Top 3 ASINs with ratingCount > 50
python3 scripts/apiclaw.py analyze --asin {asin1}
python3 scripts/apiclaw.py analyze --asin {asin2}
python3 scripts/apiclaw.py analyze --asin {asin3}
```
⚠️ ASIN mode requires the selected ASINs to have ≥50 reviews EACH. Check ratingCount before selecting. If an ASIN has <50 reviews, pick a different one.

**Priority 3 — Realtime topReviews (ONLY if both category AND ASIN modes fail):**
- Extract pain points, buying factors, and sentiment from the topReviews text from realtime/product data
- Use ratingBreakdown (star distribution) to gauge overall satisfaction
- Tag all insights as 💡 Directional — this is the weakest data source

**⚠️ FORBIDDEN: Skipping directly to Priority 3 without attempting Priority 1 and 2.**

## product-history Fallback Rules

**⚠️ Fallback for empty history data:** If product-history returns empty data (count=0) for some ASINs:
1. **Try different ASINs** — newer products or variant ASINs may not have history coverage. Pick ASINs with the oldest `listingDate` from earlier steps.
2. **Try up to 3 rounds** of different ASIN combinations before giving up.
3. If ALL ASINs return empty, use BSR snapshots from DB data + realtime data to infer directional trends. Tag as 🔍 Inferred.
4. **Never report "no trend data available" without trying at least 5 different ASINs.**

---

## Data Field Usage (MANDATORY)
**Always use API-provided fields directly. Do NOT calculate metrics when the API already provides them:**
- Revenue → use `sampleAvgMonthlyRevenue`, **NEVER** calculate as avgPrice × totalSales
- Opportunity → use `sampleOpportunityIndex`, **NEVER** invent your own formula
- Concentration → use `sampleTop10BrandSalesRate` or `topBrandSalesRate` directly

## User Decision Standards (MANDATORY)
**If the user specifies decision criteria, STRICTLY evaluate against data. Do NOT override with your own judgment.**

## Error Handling & Self-Check

HTTP errors (401/402/403/404/429) are handled by the script automatically, returning structured JSON with `error.message` and `error.action` that AI can read and act on.

When encountering issues, run self-check:

```bash
python scripts/apiclaw.py check
```

Tests 4 of 5 endpoints (skips `realtime/product` which requires a valid ASIN), reports availability.

**Other common issues**:

| Error | Cause | Solution |
|-----|------|------|
| `command not found: python` | macOS has no python command | Use `python3` |
| `Cannot index array with string` | `.data` is array | Use `.data[0].fieldName` |
| Returns empty `data: []` | Keyword no match | Use `categories` to confirm category exists first |
| `salesMonthly: null` | Some products lack sales data | BSR estimate: Monthly sales ≈ 300,000 / BSR^0.65 |
| `realtime/product` slow | Real-time scraping | Normal 5-30s, be patient |