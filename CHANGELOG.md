# Changelog

All notable changes to this project will be documented in this file.
Each entry notes which skill or the repo itself was affected.

## [1.2.1] — 2026-03-25

### Repo
- Fixed CI markdown link check failure (pull_request_template.md path)
- Added `README.zh-CN.md` — full Chinese translation with language switcher
- Updated repo description and README to match official website positioning
- Corrected framing: APIClaw is a general agent data infrastructure, Amazon is the current data source

## [1.2.0] — 2026-03-23

### Repo
- **Major restructure**: moved amazon-analysis to subdirectory, added general `apiclaw/` skill
- Added LICENSE (MIT), CONTRIBUTING.md, CODE_OF_CONDUCT.md
- Rewrote README.md with badges, Quick Start guide, API examples, and feature tables
- Added Issue Templates (bug report, feature request), PR template, CODEOWNERS
- Added CI workflow (CLI smoke test + markdown link check)
- Set repository description, homepage, and topics

### apiclaw v1.0.0
- Corrected API parameters, field names, and added field difference table
- Improved skill display names and descriptions

### amazon-analysis
- Quality improvements: version sync, naming consistency
- Removed ClawHub references, use git clone for installation

## [1.1.5] — 2026-03-20

### amazon-analysis v1.1.5
- Fixed potential API key exposure risk in example configurations
- Removed hardcoded endpoint URLs from skill documentation
- Rewrote all reference files with improved field descriptions and usage examples
- Improved SKILL.md descriptions for better agent intent matching
- Enforced mandatory API usage tracking in output
- Enforced mandatory Data Source block in Full Mode output
- Added mandatory pre-execution checklist for Full Mode
- Optimized name and description for search discoverability

## [1.1.4] — 2026-03-18

### amazon-analysis v1.1.4
- **Credits Tracking**: API responses now include `creditsConsumed` and `creditsRemaining`
- **Realtime Data Supplementation**: automatically calls `realtime/product` for top 3-5 ASINs in Full mode
- **Reviews/Analyze Endpoint**: new `analyze` command for AI-powered review analysis (11 dimensions)
- **New Scenario 4.6**: Category Consumer Insights
- **Breaking**: `review` → `rating` rename across fields, filters, and CLI args
- **Breaking**: `topReviews` removed from `realtime/product` (use `reviews/analyze`)
- 6 new market response fields for new product metrics
- Slimmed SKILL.md from 448 → 417 lines

### apiclaw v1.0.0
- Initial release of general skill — lightweight overview of all 6 API endpoints

## [1.1.2] — 2026-03-16

### amazon-analysis v1.1.2
- Improved credential handling security: require user confirmation before writing to config.json (#12)
- Use ClawHub standard metadata format for credential declaration (#13)
- Emphasize environment variable as preferred credential method

## [1.1.1] — 2026-03-16

### amazon-analysis v1.1.1
- **Security**: removed API key logging, added SECURITY.md
- **8 Documentation Fixes**: interface data differences, API call ordering, null fallbacks
- **New**: Listing Optimization Module (8.1 Analysis, 8.2 Copy Generation, 8.3 Diagnosis)
- **6 Mode Corrections**: beginner, long-tail, new-release, fbm-friendly, speculative, top-bsr
- **New CLI Parameters**: `--keyword-match-type`, `--bsr-min/max`, `--seller-count-min/max`, etc.

## [1.0.0] — 2026-03-13

### amazon-analysis v1.0.0
- Initial release with full Amazon seller analytics skill
- CLI tool (`apiclaw.py`) with 8 subcommands and 14 preset search modes
- Full API reference documentation covering all endpoints and response fields
- 7 scenario reference files: composite, evaluation, pricing, operations, expansion, listing, market monitoring
