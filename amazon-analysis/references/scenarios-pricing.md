# Amazon Pricing Strategy & Profit Estimation

> Develop competitive Amazon pricing strategies, estimate FBA/FBM profit margins, calculate fees, and benchmark against competitor prices.
> Load when handling pricing strategy, profit estimation, or listing reference tasks.
> For API parameters, see `reference.md`.
>
> ⚠️ **Always resolve categoryPath before running these queries.** Tag conclusions with 📊/🔍/💡 confidence labels.

---

## 5.1 Price Analysis

```bash
# Step 1: Category pricing
python3 scripts/apiclaw.py market --category "Electronics,Headphones" --topn 10

# Step 2: Top 50 price distribution
python3 scripts/apiclaw.py products --keyword "wireless earbuds" --page-size 50
# → Analyze price bands: $0-20, $20-50, $50-100, $100+
```

**Output Template**

```markdown
# Price Analysis - [Category]

## Market Average
- Sample avg price: $XX
- Sample avg gross margin: XX%

## Price Band Distribution (Top 50)
| Price Range | Count | % | Avg Monthly Sales | Recommendation |
|-------------|-------|---|-------------------|----------------|

## Pricing Strategy
[Data-driven pricing recommendations]
```

---

## 5.2 Profit Estimation

```bash
python3 scripts/apiclaw.py competitors --keyword "wireless earbuds" --page-size 20
# → Compare: price, fbaFee across competitors
```

**Key fields**: `price`, `fbaFee`, removed, `fulfillment`

---

## 5.3 Listing Reference

```bash
python3 scripts/apiclaw.py product --asin B09XXXXX
# → Analyze: features (Bullet Points), description, images, specifications
```

**Analysis dimensions**:
- Bullet Points count and structure
- Key selling points extraction
- Image count and types
- A+ content presence
- Variant strategy

---

## 5.4 Price Band Analysis (New Endpoints)

```bash
# Step 1: Overview — which price bands have opportunity
python3 scripts/apiclaw.py price-band-overview --keyword "yoga mat"

# Step 2: Drill into a promising band
python3 scripts/apiclaw.py price-band-detail --keyword "yoga mat" --price-min 20 --price-max 40

# Step 3: Historical price trends for key ASINs
python3 scripts/apiclaw.py history --asin B09XXXXX --period 90d
```

**Key metrics**: `sampleOpportunityIndex` > 1.0 = underserved band, Sales/Competition Ratio = Avg Monthly Sales / Avg Review Count (higher = easier entry).
