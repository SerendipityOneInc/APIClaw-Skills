# APIClaw Advanced Scenarios

> Load this file when handling product evaluation, pricing, daily operations, expansion, or special analysis tasks.
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
python scripts/apiclaw.py categories --keyword "pet toys"

# Step 2: Market conditions
python scripts/apiclaw.py market --category "Pet Supplies,Dogs,Toys" --topn 10

# Step 3: Run 2-3 modes based on user profile
# Beginner → beginner + high-demand-low-barrier
python scripts/apiclaw.py products --keyword "pet toys" --mode beginner --page-size 20
python scripts/apiclaw.py products --keyword "pet toys" --mode high-demand-low-barrier --page-size 20

# Advanced → fast-movers + underserved
python scripts/apiclaw.py products --keyword "pet toys" --mode fast-movers --page-size 20
python scripts/apiclaw.py products --keyword "pet toys" --mode underserved --page-size 20

# Step 4: AI weighted scoring → Top 5 recommendation
```

**AI Weighted Scoring Dimensions**:

| Dimension | Weight | Data Source |
|------|------|---------|
| Demand Strength | 25% | salesMonthly |
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
| # | ASIN | Product | Price | Monthly Sales | Ratings | Comprehensive Score | Recommendation Reason |
|---|------|------|------|-------|-------|---------|---------|

## Action Recommendations
[Specific recommendations based on user profile]
```

---

## 3.4 Chinese Seller Case Study

> Trigger: "Are there Chinese sellers who succeeded" / "Chinese sellers cases" / "Chinese sellers"

```bash
python scripts/apiclaw.py competitors --keyword "wireless earbuds" --page-size 50
# → Filter results by sellerLocation field
```

**sellerLocation Filtering Logic**:
- Contains "CN" / "China" / Chinese city names: Shenzhen, Guangzhou, Hangzhou, Yiwu, Dongguan, Xiamen, Shanghai, Beijing, Ningbo, Fuzhou
- Sort by `salesMonthly`, find Top 5 Chinese sellers by sales volume

**Analysis Dimensions**:
- Chinese sellers count ratio (vs total sellers)
- Common traits of top Chinese sellers (price range, rating count, listing time)
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
| # | ASIN | Brand | Price | Monthly Sales | Rating | Ratings | Listing Date |
|---|------|------|------|-------|------|------|---------|

## Success Strategy Analysis
[Common traits analysis + Replicable strategies]

## Action Recommendations
[Specific recommendations based on Chinese seller cases]
```

---

## 4. Product Evaluation

> Core question: Can this product be pursued?

### 4.2 Review Insights

> Trigger: "consumer pain points" / "negative review analysis" / "review insights" / "pain points"

```bash
python scripts/apiclaw.py product --asin B09V3KXJPB
# → Analyze ratingBreakdown from realtime/product
# → Use reviews/analyze for structured consumer insights
```

**Key Information from ratingBreakdown + analyze**:

| Analysis Dimension | Focus Points |
|---------|-------|
| Negative review keywords | broke, defect, quality, returned, disappointed, cheap, flimsy, doesn't work |
| Positive review highlights | easy, great value, love, perfect, amazing, sturdy, well-made, exactly as described |
| Negative review ratio | 1-2 star ratio in ratingBreakdown (> 20% is high risk) |
| Improvement opportunities | Specific problems from analyze consumerInsights → Product differentiation direction |

**Output Template**

```markdown
# 💬 [ASIN] Review Insights

## Rating Distribution
| Star Rating | Percentage | Count |
|------|------|------|
| 5⭐ | X% | X |
| 4⭐ | X% | X |
| 3⭐ | X% | X |
| 2⭐ | X% | X |
| 1⭐ | X% | X |

## Positive Review Themes
[Extract top 3 positive themes from analyze consumerInsights]

## Negative Review Pain Points
[Extract top 3 negative themes from analyze consumerInsights → These are differentiation opportunities]

## Improvement Suggestions
[Product improvement directions based on pain points]
```

---

### 4.3 Multi-Product Comparison

> Trigger: "Which of these products is more worth pursuing" / "compare evaluation" / "compare products"

```bash
python scripts/apiclaw.py competitors --keyword "yoga mat" --page-size 20
# Or for specific ASINs, run product command for each
python scripts/apiclaw.py product --asin B09XXXXX
python scripts/apiclaw.py product --asin B08YYYYY
```

**Horizontal Comparison Dimensions**:

| Dimension | Field | Description |
|------|------|------|
| Price | price | Pricing comparison |
| Monthly Sales | salesMonthly | Demand validation |
| BSR | bsrRank | Ranking comparison |
| Rating | rating | Product quality |
| Rating Count | ratingCount | Competition barrier |
| Profit Margin | profitMargin | Profitability |
| Variant Count | variantCount | Product complexity |
| FBA Fee | fbaFee | Cost comparison |
| Seller Count | sellerCount | Competition intensity |
| Tags | isBestSeller / isAmazonChoice / isNewRelease | Market recognition |
| A+/Video | hasAPlus / hasVideo | Listing investment level |

---

### 4.4 Risk Assessment

> Trigger: "What are the risks" / "can I do this" / "risk assessment"

```bash
# Step 1: Product detail
python scripts/apiclaw.py product --asin B09XXXXX

# Step 2: Market context
python scripts/apiclaw.py market --category "category path" --topn 10

# Step 3: Competitive landscape
python scripts/apiclaw.py competitors --keyword "product keyword" --page-size 20
```

**Six-Dimensional Risk Assessment Matrix**:

| Risk Dimension | Data Source | 🟢 Low Risk | 🟡 Medium Risk | 🔴 High Risk |
|---------|---------|---------|---------|---------|
| Competition Intensity | topSalesRate | < 40% | 40-60% | > 60% |
| Rating Barrier | Top average ratingCount | < 200 | 200-1000 | > 1000 |
| Brand Barrier/Moat | topBrandSalesRate | < 30% | 30-50% | > 50% |
| Price War Risk | Top price variance | High variance (dispersed) | Medium | Low variance (price war) |
| Compliance Risk | categories category | Regular categories | Requires certification | High-risk categories |
| Seasonality | AI judgment (category name) | Year-round demand | Seasonal fluctuation | Strong seasonality |

**High-risk Category Compliance Alerts** (AI self-judgment):

| Category | Compliance Requirements |
|------|---------|
| Health/Supplements | FDA compliance |
| Children's Products | CPSC certification (CPSIA) |
| Electronics | FCC certification |
| Food | FDA registration |
| Cosmetics | FDA compliance |
| Laser Products | FDA/CDRH |
| Toys | ASTM F963 |

**Output Template**

```markdown
# ⚠️ [ASIN/Category] Risk Assessment Report

## Risk Matrix
| Risk Dimension | Risk Level | Description |
|---------|---------|------|
| Competition Intensity | 🟢/🟡/🔴 | ... |
| Rating Barrier | 🟢/🟡/🔴 | ... |
| Brand Barrier/Moat | 🟢/🟡/🔴 | ... |
| Price War Risk | 🟢/🟡/🔴 | ... |
| Compliance Risk | 🟢/🟡/🔴 | ... |
| Seasonality | 🟢/🟡/🔴 | ... |

## Overall Risk Level: 🟢/🟡/🔴
[Analysis and recommendations]
```

---

### 4.5 Sales Estimation

> Trigger: "How much monthly sales does this product have" / "sales forecast" / "estimate sales"

```bash
python scripts/apiclaw.py competitors --asin B09XXXXX
# → Get bsrRank and salesMonthly
```

**Three Estimation Methods**:

| Method | Formula/Logic | Accuracy |
|-----|---------|------|
| API Direct Return | `salesMonthly` field | ⭐⭐⭐⭐ Most accurate (BSR model estimation) |
| BSR Rough Estimate | Monthly sales ≈ 300,000 / BSR^0.65 | ⭐⭐ Rough (due to category differences) |
| Rating Reverse Calculation | Monthly sales ≈ ratingMonthlyNew / Rating rate(1-3%) | ⭐⭐ Reference only |

**Usage Priority**:
1. Prioritize `salesMonthly` direct return value
2. If null, use BSR rough estimate
3. Rating reverse calculation only for cross-validation

**Note**: Current API has no sales historical trends (14-month curves), only current snapshot, cannot predict growth/decline direction.

---

## 5. Pricing & Listing

> Core question: What price is appropriate? How to write listing?

### 5.1 Price Analysis

**Progress**
- [ ] Step 1/2: Category avg price (market) <- ~30s
- [ ] Step 2/2: Price band distribution (products, pageSize 50) <- ~30s

```bash
# Step 1: Category pricing
python scripts/apiclaw.py market --category "Electronics,Headphones" --topn 10

# Step 2: Top 50 price distribution
python scripts/apiclaw.py products --keyword "wireless earbuds" --page-size 50
# -> Analyze price bands: $0-20, $20-50, $50-100, $100+
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

### 5.2 Profit Estimation

```bash
python scripts/apiclaw.py competitors --keyword "wireless earbuds" --page-size 20
# -> Compare: price, fbaFee, profitMargin across competitors
```

**Key fields**: `price`, `fbaFee`, `profitMargin`, `fulfillment`

---

### 5.3 Listing Reference

**Progress**
- [ ] Step 1/1: Get top product listing (product) <- ~5s

```bash
python scripts/apiclaw.py product --asin B09XXXXX
# -> Analyze: features (Bullet Points), description, images, specifications
```

**Analysis dimensions**:
- Bullet Points count and structure
- Key selling points extraction
- Image count and types
- A+ content presence
- Variant strategy

---

## 6. Daily Operations

> Core question: What recent changes are there?
>
> **Limitation**: Snapshot data only, no historical comparison. Run periodically and compare manually for continuous monitoring.

### 6.1 Market Dynamics Monitoring

**Progress**
- [ ] Step 1/2: Market data (market) <- ~30s
- [ ] Step 2/2: Recent new products (products, listingAge filter) <- ~30s

```bash
# Step 1: Market overview
python scripts/apiclaw.py market --category "Pet Supplies,Dogs" --topn 10

# Step 2: New products in last 90 days
python scripts/apiclaw.py products --keyword "dog toys" --listing-age 90 --page-size 20
```

---

### 6.2 Competitor Dynamics

```bash
# Check competitor's latest products
python scripts/apiclaw.py competitors --brand "CompetitorBrand" --sort listingDate
```

---

### 6.3 Top Products Changes

```bash
# Current top products (replaces realtime/bestsellers)
python scripts/apiclaw.py products --category "Pet Supplies,Dogs,Toys" --page-size 20
```

---

### 6.4 Anomaly Alerts

**Progress**
- [ ] Step 1/3: Market metrics (market) <- ~30s
- [ ] Step 2/3: Current top products (products) <- ~30s
- [ ] Step 3/3: High-growth new products (products, growth filter) <- ~30s

```bash
# Step 1: Market indicators
python scripts/apiclaw.py market --category "Pet Supplies,Dogs,Toys" --topn 10

# Step 2: Current top products
python scripts/apiclaw.py products --category "Pet Supplies,Dogs,Toys" --page-size 20

# Step 3: High-growth new products (potential threats)
python scripts/apiclaw.py products --category "Pet Supplies,Dogs,Toys" --listing-age 90 --growth-min 0.2 --page-size 10
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

---

## 7. Expansion & Iteration

> Core question: What else can I sell?
>
> **Limitation**: No historical data comparison. "Trends" based on current snapshot growth rate fields.

### 7.1 Related Products Discovery

**Progress**
- [ ] Step 1/2: Get sibling categories (categories) <- ~2s
- [ ] Step 2/2: Evaluate each category (market x N) <- ~30s x N

```bash
# Step 1: Sibling categories
python scripts/apiclaw.py categories --parent "Pet Supplies,Dogs"

# Step 2: Evaluate each
python scripts/apiclaw.py market --category "Pet Supplies,Dogs,Feeding & Watering" --topn 10
```

---

### 7.2 New Category Evaluation

```bash
python scripts/apiclaw.py market --keyword "new category keyword" --topn 10
```

---

### 7.3 Trend Discovery

```bash
# Find fastest growing products
python scripts/apiclaw.py products --keyword "pet supplies" --growth-min 0.2 --listing-age 180 --page-size 20
```

---

### 7.4 Product Discontinuation Decision

**Progress**
- [ ] Step 1/2: Current product performance (competitors) <- ~30s
- [ ] Step 2/2: Market trend (market) <- ~30s

```bash
# Step 1: Product current performance
python scripts/apiclaw.py competitors --asin B09XXXXX

# Step 2: Category market trend
python scripts/apiclaw.py market --category "category path" --topn 10
```

**Discontinuation Signals**:

| Signal | Data Source | Trigger Condition |
|--------|-------------|-------------------|
| Sales decline | salesGrowthRate | Negative growth rate |
| Profit erosion | profitMargin | Margin < 10% |
| Competition intensifying | sellerCount | Sellers > 10 and increasing |
| BSR dropping | bsrGrowthRate | BSR rank continuously rising (worsening) |
| Market shrinking | sampleAvgMonthlySales | Category avg sales declining |

**Output Template**

```markdown
# Product Discontinuation Evaluation - [ASIN]

## Current Performance
| Metric | Value | Trend |
|--------|-------|-------|
| Monthly sales | X | up/down |
| BSR | #X | up/down |
| Profit margin | X% | up/down |
| Seller count | X | up/down |

## Discontinuation Signals
| Signal | Triggered? | Description |
|--------|-----------|-------------|

## Recommendation
**[Continue / Adjust / Discontinue]**
[Reasons and alternatives]
```

---

## Flow Guidance (Smart Transitions)

| Current Conclusion | Next Step | Load File |
|-------------------|-----------|-----------|
| Pricing done, ready to list | -> Daily monitoring | This file -> 6.x |
| Found market anomaly | -> Competitor analysis | SKILL.md -> competitors |
| Want to expand | -> Related products | This file -> 7.1 |
| Product underperforming | -> Evaluate discontinuation | This file -> 7.4 |
| Need to pivot category | -> Market validation | SKILL.md -> market |

---

*Scenarios adapted from apiclaw-skill-public v1.0 | Script-based execution*