# Amazon Product Expansion & Market Trends

> Discover trending Amazon products, expand product lines, find new niche opportunities, and make data-driven discontinuation decisions.
> Load when handling product expansion, trend discovery, or discontinuation decisions.
> For API parameters, see `reference.md`.
>
> ⚠️ **Always resolve categoryPath before running these queries.** Tag conclusions with 📊/🔍/💡 confidence labels.
>
> **Note**: Use `history` for ASIN-level historical trends. Use `brand-overview` for market scanning.

---

## 7.1 Related Products Discovery

```bash
# Step 1: Sibling categories
python3 scripts/apiclaw.py categories --parent "Pet Supplies,Dogs"

# Step 2: Evaluate each
python3 scripts/apiclaw.py market --category "Pet Supplies,Dogs,Feeding & Watering" --topn 10
```

---

## 7.2 New Category Evaluation

```bash
python3 scripts/apiclaw.py market --keyword "new category keyword" --topn 10
```

---

## 7.3 Trend Discovery

```bash
python3 scripts/apiclaw.py products --keyword "pet supplies" --growth-min 0.2 --listing-age 180 --page-size 20
```

---

## 7.4 Product Discontinuation Decision

```bash
# Step 1: Product current performance
python3 scripts/apiclaw.py competitors --asin B09XXXXX

# Step 2: Category market trend
python3 scripts/apiclaw.py market --category "category path" --topn 10
```

**Discontinuation Signals**:

⚠️ API provides current snapshot only. Growth rates (`salesGrowthRate`, `bsrGrowthRate`) reflect recent trends but are not historical time-series. Use them as directional indicators, not definitive proof of sustained decline.

| Signal | Data Source | Trigger Condition |
|--------|-------------|-------------------|
| Sales decline | `salesGrowthRate` | Negative growth rate (current snapshot) |
| High competition | `sellerCount` | Currently > 10 sellers |
| BSR worsening | `bsrGrowthRate` | Negative BSR growth (rank number increasing) |
| Weak market | `sampleAvgMonthlySales` | Category avg below viable threshold |

**Note:** `salesGrowthRate` and `bsrGrowthRate` come from `products`/`competitors` interface. `realtime/product` does NOT provide these fields. For stronger evidence, run this analysis periodically and compare snapshots.

**Output Template**

```markdown
# Product Discontinuation Evaluation - [ASIN]

## Current Performance
| Metric | Value | Trend |
|--------|-------|-------|

## Discontinuation Signals
| Signal | Triggered? | Description |
|--------|-----------|-------------|

## Recommendation
**[Continue / Adjust / Discontinue]**
[Reasons and alternatives]
```

---

## 7.5 Market Scanning with Brand & Price Analysis (New Endpoints)

```bash
# Brand landscape — who dominates this category
python3 scripts/apiclaw.py brand-overview --keyword "pet toys"

# Price band scan — where are the gaps
python3 scripts/apiclaw.py price-band-overview --keyword "pet toys"

# Historical validation for specific expansion candidates
python3 scripts/apiclaw.py history --asin B09XXXXX --period 90d
```

**Expansion evaluation**: Combine `brand-overview` (low concentration = easier entry) with `price-band-overview` (high opportunity index bands) to identify the best entry points.

---

## Flow Guidance (Smart Transitions)

| Current Conclusion | Next Step | Load File |
|-------------------|-----------|-----------|
| Pricing done, ready to list | → Daily monitoring | `scenarios-ops.md` |
| Found market anomaly | → Competitor analysis | SKILL.md → competitors |
| Want to expand | → Related products | This file → 7.1 |
| Product underperforming | → Evaluate discontinuation | This file → 7.4 |
| Need to pivot category | → Market validation | SKILL.md → market |
