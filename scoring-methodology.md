# APIClaw Skills — Scoring Methodology Reference

> This document defines the evaluation scoring framework used across all APIClaw Hero Skills.
> Based on market research of 5 major Amazon seller tools + industry best practices.
> All skills that produce scores/ratings MUST reference this methodology.

## Industry Research Summary

### Tools Analyzed

| Tool | Score Name | Scale | Dimensions | Weights Public? |
|------|-----------|-------|-----------|----------------|
| Jungle Scout | Opportunity Score | 1-10 | Demand, Competition, Listing Quality | ❌ Proprietary |
| Helium 10 | Success Score / Power Score | 1-100 | Market maturity, Price, Revenue, Reviews | ❌ Proprietary |
| AMZScout | Niche Score + Saturation Score | 1-10 | Profit margin, Demand, Competition, Niche history | ❌ Not disclosed |
| SmartScout | Custom framework | — | Revenue, Seller count, Amazon share, BSR, Margins | ❌ Not disclosed |
| Viral Launch | Niche Health Score | — | Demand, Competition, Trends | ❌ Not disclosed |

**Key Finding**: No major tool publicly discloses their exact scoring weights. All use proprietary algorithms.

### Industry Consensus on Dimensions

Despite undisclosed weights, all tools converge on the same core dimensions:

| Dimension | Mentioned By | Industry Consensus |
|-----------|-------------|-------------------|
| **Demand / Market Size** | All 5 tools | Must have ≥300 units/mo, market value $5M+ |
| **Competition** | All 5 tools | Review count (<200 for low), Brand concentration, Seller count |
| **Profit Margin** | JS, AMZScout, SmartScout | Target ≥25-30% net margin after all fees |
| **Trends / Seasonality** | Helium 10, Viral Launch | Rising BSR trend, non-seasonal preferred |
| **Listing Quality** | JS, AMZScout | LQS >70, images, A+ content, keyword coverage |
| **Price Range** | AMZScout, SmartScout | Sweet spot $15-50 for beginners |
| **New Entrant Space** | SmartScout, AMZScout | New SKU rate, low review barriers |
| **Consumer Pain Points** | — (unique to us via reviews/analyze API) | Our differentiation — none of them have 1B+ pre-analyzed reviews |

### Industry Benchmark Thresholds

| Metric | Good | Medium | Warning | Sources |
|--------|------|--------|---------|---------|
| Monthly sales/product | >300 units | 100-300 | <100 | JS, AMZScout, SmartScout |
| Monthly market value | >$10M | $5-10M | <$5M | General consensus |
| Top 10 review count | <200 avg | 200-1000 | >1000 | AMZScout, SmartScout |
| Brand concentration CR10 | <40% | 40-60% | >60% | SmartScout |
| New SKU rate | >15% | 5-15% | <5% | SmartScout |
| Profit margin (net) | >30% | 15-30% | <15% | JS, AMZScout, SmartScout |
| FBA rate | >50% | 30-50% | <30% | General |
| Avg rating | >4.3 | 4.0-4.3 | <4.0 | General |
| Price sweet spot | $15-50 | $10-15 or $50-100 | <$10 or >$100 | AMZScout |

---

## APIClaw Scoring Framework

### Design Rationale

Based on the industry research above, our framework:
1. **Covers all 5 consensus dimensions** + 2 unique ones (Price Opportunity via price-band API, Consumer Pain Points via reviews/analyze API)
2. **Uses 1-100 scale** (consistent with Helium 10, more granular than JS's 1-10)
3. **Weights justified by failure mode analysis** — what causes most new seller failures?

### Weight Justification

| Dimension | Weight | Rationale |
|-----------|--------|-----------|
| **Competition** | 25% | #1 cause of new seller failure. All 5 tools list it as primary factor. Higher weight = more conservative recommendations. |
| **Market Size** | 15% | Must verify sufficient demand exists. All tools require ≥300 units/mo. Smaller weight than competition because small markets can be profitable if competition is low. |
| **Consumer Pain Points** | 15% | Our unique advantage (1B+ pre-analyzed reviews). No other tool scores this dimension with real data. Pain points = differentiation opportunity. |
| **Price Opportunity** | 15% | Our unique advantage (price-band API with opportunityIndex). Tells you exactly which price range has demand but low competition. |
| **Market Trend** | 10% | Rising/stable/declining market. Helium 10 and Viral Launch emphasize this. Lower weight because trends can reverse. |
| **New Entrant Space** | 10% | New SKU rate + low review barriers. SmartScout and AMZScout use this. Indicates if the market is open to newcomers. |
| **Profit Potential** | 10% | Must be ≥25-30% margin. All tools check this. Lower weight because margins can be optimized after entry, unlike competition which is structural. |
| **Total** | **100%** | |

### Scoring Tiers

| Score Range | Signal | Meaning | Action |
|-------------|--------|---------|--------|
| 70-100 | ✅ GO | Strong opportunity across most dimensions | Proceed to product development |
| 40-69 | ⚠️ CAUTION | Mixed signals, some dimensions weak | Needs clear differentiation strategy before proceeding |
| 0-39 | 🔴 AVOID | Too competitive, too small, or declining | Look for other categories |

These tiers are more conservative than Jungle Scout's (where 7/10 = "good") because:
- Our score considers more dimensions (7 vs 3)
- A score of 70/100 = performing well on most dimensions, roughly equivalent to JS's 7/10
- We'd rather have false negatives (miss some opportunities) than false positives (recommend bad markets)

---

## Application to Skills

| Skill | Uses Scoring? | Which Dimensions? |
|-------|--------------|-------------------|
| Market Entry Analyzer | ✅ Full 7-dimension | All 7 |
| Opportunity Discoverer | ✅ Composite score (1-100) | All 7, weighted |
| Competitor War Room | Partial (competitive strength) | Competition + Trend |
| Review Intelligence Engine | Partial (pain point score) | Consumer Pain Points only |
| Pricing Command Center | Partial (pricing signal) | Price Opportunity + Profit |
| Listing Audit Pro | ✅ Different framework (8-dimension) | Listing-specific criteria |
| Daily Market Radar | Alert thresholds only | Trend + Competition changes |

---

## Changelog

- 2026-03-28: Initial version based on research of Jungle Scout, Helium 10, AMZScout, SmartScout, Viral Launch
