# Changelog

All notable changes to this project will be documented in this file.
Each entry notes which skill or the repo itself was affected.

## 2026-03-23

### Repo
- Added LICENSE (MIT), CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md
- Rewrote README.md with badges, Quick Start guide, API examples, and feature tables
- Added Issue Templates (bug report, feature request), PR template, CODEOWNERS
- Added basic CI workflow (CLI smoke test)
- Added config.example.json for API key configuration reference
- Fixed version inconsistencies across SECURITY.md and CHANGELOG.md
- Improved .gitignore with Python packaging, testing, and log patterns
- Set repository description, homepage, and topics

## 2026-03-20

### amazon-analysis v1.1.5
- Fixed potential API key exposure risk in example configurations
- Removed hardcoded endpoint URLs from skill documentation
- Rewrote all reference files with improved field descriptions and usage examples
- Improved SKILL.md descriptions for better agent intent matching

## 2026-03-18

### amazon-analysis v1.1.4
- Updated scenario references with more realistic evaluation criteria
- Improved pricing strategy reference with profit margin calculation examples

### apiclaw v1.0.0
- Initial release of general skill — lightweight overview of all 6 API endpoints
- Published to ClawHub

## 2026-03-13

### amazon-analysis v1.0.0
- Initial release with full Amazon seller analytics skill
- CLI tool (`apiclaw.py`) with 8 subcommands and 14 preset search modes
- Full API reference documentation covering all endpoints and response fields
- 7 scenario reference files: composite, evaluation, pricing, operations, expansion, listing, and market monitoring
