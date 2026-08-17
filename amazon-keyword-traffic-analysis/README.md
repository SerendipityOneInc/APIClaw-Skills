# Amazon Keyword Traffic Analysis

This package provides the `amazon-keyword-traffic-analysis` Codex skill for Amazon keyword value analysis and ASIN-centered product traffic health analysis.

This README is a human-facing overview and module index. Runtime behavior is defined by [`SKILL.md`](SKILL.md) and the owner modules it routes to; this file does not add or override skill policy.

## Package map

- [`SKILL.md`](SKILL.md) — runtime router, loading path, responsibility map, and global boundaries
- [`references/reference.md`](references/reference.md) — production API and acquisition-surface contract
- [`references/execution-guide.md`](references/execution-guide.md) — shared scenario/stage contract, Gate order, handoff, and stage-end selection rules
- [`references/evidence-protocols.md`](references/evidence-protocols.md) — evidence planning, retrieval, reconciliation, coverage, continuity, and batching
- [`references/diagnosis-action-protocols.md`](references/diagnosis-action-protocols.md) — causal-diagnosis and evidence-to-action procedures
- [`references/output-rules.md`](references/output-rules.md) — localized progress, canonical report template and headings, Data Notes, and API usage
- `references/metrics-*.md`, [`serp-and-rollover.md`](references/serp-and-rollover.md), and [`traffic-observation-semantics.md`](references/traffic-observation-semantics.md) — returned-field semantics and inference limits
- [`references/sqp-field-semantics.md`](references/sqp-field-semantics.md) — seller-artifact acquisition and field semantics
- `references/scenarios-*.md` — scenario-specific stage entry requirements, capability selection, conclusion authority, and report-section content
- [`references/scenarios-expand.md`](references/scenarios-expand.md) — keyword expansion
- [`references/scenarios-keyword-analysis.md`](references/scenarios-keyword-analysis.md) — keyword demand, market structure, trend, value, and ASIN fit
- [`references/scenarios-product-traffic-analysis.md`](references/scenarios-product-traffic-analysis.md) — product traffic structure, terms, change, trend, health, and diagnosis
- [`scripts/zoodata.py`](scripts/zoodata.py) — bundled ZooData CLI

## Data & privacy

- Runtime queries — keywords, ASINs, marketplaces, dates, and numeric filters — are sent to the ZooData API (`api.zoodata.ai`); WebTools page acquisition additionally sends the target public URLs. No seller-account or free-text profile data is transmitted.
- WebTools usage is read-only public-page acquisition; the global boundaries in [`SKILL.md`](SKILL.md) prohibit state-changing page interactions.
- The package persists no query state between runs; every API call consumes account credits.
