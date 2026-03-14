# APIClaw Scenarios — Daily Operations

> Load when handling market monitoring, competitor tracking, or anomaly detection.
> For API parameters, see `reference.md`.
>
> **Limitation**: Snapshot data only, no historical comparison. Run periodically and compare manually for continuous monitoring.

---

## 6.1 Market Dynamics Monitoring

```bash
# Step 1: Market overview
python3 scripts/apiclaw.py market --category "Pet Supplies,Dogs" --topn 10

# Step 2: New products in last 90 days
python3 scripts/apiclaw.py products --keyword "dog toys" --listing-age 90 --page-size 20
```

---

## 6.2 Competitor Dynamics

```bash
python3 scripts/apiclaw.py competitors --brand "CompetitorBrand" --sort listingDate
```

---

## 6.3 Top Products Changes

```bash
python3 scripts/apiclaw.py products --category "Pet Supplies,Dogs,Toys" --page-size 20
```

---

## 6.4 Anomaly Alerts

```bash
# Step 1: Market indicators
python3 scripts/apiclaw.py market --category "Pet Supplies,Dogs,Toys" --topn 10

# Step 2: Current top products
python3 scripts/apiclaw.py products --category "Pet Supplies,Dogs,Toys" --page-size 20

# Step 3: High-growth new products (potential threats)
python3 scripts/apiclaw.py products --category "Pet Supplies,Dogs,Toys" --listing-age 90 --growth-min 0.2 --page-size 10
```

**Alert Signal Detection**:

| Alert Type | Detection Method | Trigger Condition |
|------------|-----------------|-------------------|
| New blockbuster invasion | Step 3 results | New product (<90 days) already in Top 20 |
| Price war risk | Step 2 price distribution | Multiple top products with similar low prices |
| Concentration change | Step 1 topSalesRate | Sudden increase in concentration |
| New SKU rate anomaly | Step 1 sampleNewSkuRate | Sudden spike (flood) or drop (market freeze) |

**Output Template**

```markdown
# Anomaly Alert Report - [Category]

## Alert Signals
| Signal | Level | Description |
|--------|-------|-------------|

## Detailed Analysis
[Each alert signal with specific data]

## Recommended Actions
[Response strategy for each alert]
```
