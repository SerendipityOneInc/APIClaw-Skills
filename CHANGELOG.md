# Changelog

All notable changes to this project will be documented in this file.

## [1.2.0] — 2026-04-03

### Breaking Changes — API V2 Field Renames
- `atLeastMonthlySales` → `monthlySalesFloor`, `atLeastMonthlyRevenue` → `monthlyRevenueFloor`
- `bsrRank` → `bsr`, `subBsrRank` → `subBsr`
- `ratingConversionRate` → `ratingToSalesRate`, `ratingMonthlyNew` → `monthlyRatingCount`
- `buyboxSeller` → `buyBoxSellerName`, `sellerLocation` → `buyBoxSellerCountryCode`
- `sampleEbcSkuRate` → `sampleAPlusRate`, `sampleAvgPackageDimensions` → `sampleAvgPackageVolume`
- `totalReviews` → `reviewCount`, `reviewPercentage` → `reviewRate`, `verifiedRatio` → `verifiedRate`
- Endpoint: `products/competitor-lookup` → `products/competitors`
- Endpoint: `reviews/analyze` → `reviews/analysis`
- Endpoint: `products/product-history` → `products/history`
- Removed: `profitMargin`, `sampleAvgGrossMargin`
- `pageSize` max: 20 → 100

### Bug Fixes
- Fixed argparse prefix matching: `--page` silently overriding `--page-size`. Added `allow_abbrev=False`.

### Skill Updates
- **Renamed**: Dynamic Pricing Intelligence Agent → Amazon Pricing Command Center — RAISE/HOLD/LOWER Signals
- **Renamed**: Market Radar → Amazon Market Trend Scanner — Daily Category Radar
- **Removed**: amazon-blue-ocean-finder
- **Disabled**: beginner mode (excludeKeywords not working)
- Removed cost/COGS/profit from pricing skill
- Added OpenAPI spec reference to all SKILL.md
- Unified all reference.md to complete 11-endpoint version
- 13 selection modes (was 14)

## [1.1.4] — 2026-04-01

### amazon-analysis v1.1.4
- Major SKILL.md rewrite: improved intent routing, workflow structure, and agent instructions
- Added `references/execution-guide.md` — step-by-step execution playbook for agents
- Updated `references/reference.md` with 11 endpoints (was 6), new field descriptions
- Enhanced scenarios files with additional guidance
- Rewrote `scripts/apiclaw.py` with improved error handling

### apiclaw v1.1.0
- Expanded from 6 to 11 API endpoints: added price-band overview/detail, brand overview/detail, product history
- Rewrote SKILL.md with complete endpoint documentation
- Updated `references/openapi-reference.md` with full field reference for all 11 endpoints

### 7 New Hero Skills v1.0.0
- **amazon-competitor-war-room** — Real-time competitive monitoring and response strategy
- **amazon-daily-market-radar** — Daily market pulse check and anomaly detection
- **amazon-listing-audit-pro** — Comprehensive listing quality audit and optimization
- **amazon-market-entry-analyzer** — Market viability assessment for new category entry
- **amazon-opportunity-discoverer** — Underserved niche and opportunity identification
- **amazon-pricing-command-center** — Dynamic pricing strategy and margin optimization
- **amazon-review-intelligence-engine** — Deep review sentiment analysis and insight extraction

### Repo
- Added `scoring-methodology.md` — unified quality scoring framework for all skills

## [1.1.3] — 2026-03-20

### amazon-analysis
- Fixed potential API key exposure risk in example configurations
- Removed hardcoded endpoint URLs from skill documentation
- Rewrote all reference files with improved field descriptions and usage examples
- Improved SKILL.md descriptions for better agent intent matching
- Enforced mandatory API usage tracking in output
- Enforced mandatory Data Source block in Full Mode output
- Added mandatory pre-execution checklist for Full Mode
- Optimized name and description for search discoverability

## [1.1.2] — 2026-03-18

### amazon-analysis
- **Credits Tracking**: API responses now include `creditsConsumed` and `creditsRemaining`
- **Realtime Data Supplementation**: automatically calls `realtime/product` for top 3-5 ASINs in Full mode
- **Reviews/Analyze Endpoint**: new `analyze` command for AI-powered review analysis (11 dimensions)
- **New Scenario 4.6**: Category Consumer Insights
- **Breaking**: `review` → `rating` rename across fields, filters, and CLI args
- **Breaking**: `topReviews` removed from `realtime/product` (use `reviews/analysis`)
- 6 new market response fields for new product metrics
- Slimmed SKILL.md from 448 → 417 lines

### apiclaw v1.0.0
- Initial release of general skill — platform overview, 6 API endpoints

## [1.1.1] — 2026-03-16

### amazon-analysis
- Improved credential handling security: require user confirmation before writing to config.json
- Use ClawHub standard metadata format for credential declaration
- Emphasize environment variable as preferred credential method

## [1.1.0] — 2026-03-16

### amazon-analysis
- **Security**: removed API key logging, added SECURITY.md
- **8 Documentation Fixes**: interface data differences, API call ordering, null fallbacks
- **New**: Listing Optimization Module (8.1 Analysis, 8.2 Copy Generation, 8.3 Diagnosis)
- **6 Mode Corrections**: beginner, long-tail, new-release, fbm-friendly, speculative, top-bsr
- **New CLI Parameters**: `--keyword-match-type`, `--bsr-min/max`, `--seller-count-min/max`, etc.

## [1.0.0] — 2026-03-13

### amazon-analysis
- Initial release with full Amazon seller analytics skill
- CLI tool (`apiclaw.py`) with 8 subcommands and 14 preset search modes
- Full API reference documentation
- 7 scenario reference files

---

### Repo Maintenance (not versioned)

**2026-03-25**
- Fixed CI markdown link check failure
- Added `README.zh-CN.md` with language switcher
- Updated repo description to match official website positioning

**2026-03-23**
- Restructured repo: added general `apiclaw/` skill, moved amazon-analysis to subdirectory
- Added LICENSE (MIT), CONTRIBUTING.md, CODE_OF_CONDUCT.md, Issue Templates, PR template
- Added CI workflow (CLI smoke test + markdown link check)
- Rewrote README.md with badges, Quick Start, API examples
