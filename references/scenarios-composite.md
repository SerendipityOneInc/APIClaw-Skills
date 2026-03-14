# APIClaw Scenarios — Composite & Case Study

> Load when handling comprehensive product recommendations or Chinese seller case studies.
> For API parameters, see `reference.md`.

---

## 2.10 Composite Product Recommendation (Comprehensive Decision Recommendations)

> Trigger: "help me choose" / "comprehensive recommendations" / "what should I sell" / "most suitable for me"

**First collect user information (if not provided, proactively ask):**

| Element | Example |
|------|------|
| Target category | "Pet supplies" |
| Budget range | < $10K / $10-50K / > $50K |
| Experience level | Beginner / Experienced / Expert |
| Preferences | Small & light items / High-ticket items / Fast turnover |

**Workflow**

```bash
# Step 1: Confirm category
python3 scripts/apiclaw.py categories --keyword "pet toys"

# Step 2: Market conditions
python3 scripts/apiclaw.py market --category "Pet Supplies,Dogs,Toys" --topn 10

# Step 3: Run 2-3 modes based on user profile
# Beginner → beginner + high-demand-low-barrier
python3 scripts/apiclaw.py products --keyword "pet toys" --mode beginner --page-size 20
python3 scripts/apiclaw.py products --keyword "pet toys" --mode high-demand-low-barrier --page-size 20

# Step 4: AI weighted scoring → Top 5 recommendation
```

**AI Weighted Scoring Dimensions**:

| Dimension | Weight | Data Source |
|------|------|---------|
| Demand Strength | 25% | atLeastMonthlySales |
| Competition Difficulty | 25% | ratingCount + sellerCount |
| Profit Margin | 20% | price × profitMargin |
| Differentiation Opportunity | 15% | rating < 4.3 or ratingCount < 200 |
| User Match | 15% | Budget/Experience/Preferences |

**Output Template**

```markdown
# 🎯 [Category] Comprehensive Product Selection Recommendations

## User Profile
| Item | Value |
|----|-----|
| Budget | ... |
| Experience | ... |
| Preferences | ... |

## Top 5 Recommended Products
| # | ASIN | Product | Price | Monthly Sales | Reviews | Comprehensive Score | Recommendation Reason |
|---|------|------|------|-------|-------|---------|---------|

## Action Recommendations
[Specific recommendations based on user profile]
```

---

## 3.4 Chinese Seller Case Study

> Trigger: "Are there Chinese sellers who succeeded" / "Chinese sellers cases" / "Chinese sellers"

```bash
python3 scripts/apiclaw.py competitors --keyword "wireless earbuds" --page-size 50
# → Filter results by sellerLocation field
```

**sellerLocation Filtering Logic**:
- Contains "CN" / "China" / Chinese city names: Shenzhen, Guangzhou, Hangzhou, Yiwu, Dongguan, Xiamen, Shanghai, Beijing, Ningbo, Fuzhou
- Sort by `atLeastMonthlySales`, find Top 5 Chinese sellers by sales volume

**Analysis Dimensions**:
- Chinese sellers count ratio (vs total sellers)
- Common traits of top Chinese sellers (price range, review count, listing time)
- Listing strategies of successful Chinese sellers (can use `product --asin XXX` for details)
- Replicable strategy points

**Output Template**

```markdown
# 🇨🇳 [Category] Chinese Seller Case Analysis

## Chinese Seller Overview
| Metric | Value |
|-----|------|
| Chinese Seller Count | X / Total Y (Z% ratio) |
| Top Chinese Seller Average Monthly Sales | X units |
| Top Chinese Seller Average Price | $X |

## Top 5 Chinese Seller Products
| # | ASIN | Brand | Price | Monthly Sales | Rating | Reviews | Listing Date |
|---|------|------|------|-------|------|------|---------|

## Success Strategy Analysis
[Common traits analysis + Replicable strategies]

## Action Recommendations
[Specific recommendations based on Chinese seller cases]
```
