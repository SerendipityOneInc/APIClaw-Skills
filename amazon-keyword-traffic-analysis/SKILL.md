---
name: amazon-keyword-traffic-analysis
description: >
  Analyze Amazon keyword value and product traffic health through keyword demand,
  market structure, weekly trends, observed SERP signals, ASIN traffic structure,
  traffic terms, changes, and named-term timelines. Use for keyword expansion,
  keyword deep dives, traffic-term value analysis, and ASIN-centered product traffic
  analysis or diagnosis. Produces evidence-bounded validation priorities;
  does not make direct bid, budget, pause, or negative-keyword decisions without
  seller ABA-SQP and Amazon Ads data. Requires ZOODATA_API_KEY.
metadata:
  version: "0.1.9"
  author: SerendipityOneInc
  homepage: https://github.com/SerendipityOneInc/ZooData-Skills
  openclaw: {"requires": {"env": ["ZOODATA_API_KEY"]}, "primaryEnv": "ZOODATA_API_KEY"}
---

# ZooData — Amazon Keyword Intelligence

Respond in the user's language.

## Start here

1. Classify the request: seed-keyword expansion, target-keyword analysis, product traffic analysis, or a single lookup.
   - Route keyword-centered questions about demand, market/SERP structure, trend, value, relevance, or targeting fit to target-keyword analysis. An ASIN may be supporting evidence without changing the keyword-centered subject.
   - Route ASIN-centered questions about traffic health, current traffic terms or sources, channel/term structure, changes, trends, anomalies, or causes to product traffic analysis.
   - Route a broad ASIN traffic analysis, overview, or health check directly to the product traffic health overview. Do not ask the user to choose between structure and change first.
   - For an ASIN × keyword request, route value/fit/relevance questions without movement or causal intent to target-keyword analysis; route visibility, placement, exposure, movement, anomaly, or causal questions to product traffic analysis.
   - If product traffic analysis identifies a term and the follow-up asks about its value, start target-keyword analysis and reuse compatible ASIN traffic evidence. If keyword analysis identifies a product-side movement question, start product traffic analysis and reuse compatible keyword evidence.
2. Read the local `references/cli-contract.md`, `references/reference.md`, and the relevant `zoodata.py --help` before selecting a tool. The shared contract owns CLI invocation and result handling; `reference.md` is the sole source for production endpoint availability, parameters, response fields, dates, batching, credits, and API capability boundaries.
3. Load `references/output-rules.md` for user-facing rendering and apply `execution-guide.md § Final Output Gate` on every rendering path. For a single lookup, also load only `references/execution-guide.md` sections `Authority and routing`, `Execution mode`, `Structured Field Identity Gate`, `Interface Failure Stop Gate`, `Final Output Gate`, `HTTP Validation Rule`, and `Credential and Credit Failures`; use `output-rules.md § Quick Mode Output` and do not load a scenario unless the follow-up broadens the request.
4. For every full-mode request, load the complete `references/execution-guide.md`, `references/evidence-protocols.md`, and the applicable scenario guide below. The guide is the sole scenario/stage and Gate contract; evidence protocols operate only inside its active stage. After every retrieval or tool result, apply its `Interface Failure Stop Gate` before selecting any next capability or command. Route to one applicable scenario, or multiple non-exclusive scenarios only when the guide permits combination:
   - `references/scenarios-expand.md`
   - `references/scenarios-keyword-analysis.md`
   - `references/scenarios-product-traffic-analysis.md`
5. For a causal, anomaly, or action question, additionally load `references/diagnosis-action-protocols.md`. Do not load it for a non-diagnostic stage merely because diagnosis is available.
6. After API retrieval, load only the field-semantic reference needed for the returned data:
   - `references/metrics-market-profile.md` for `market-profile`
   - `references/metrics-trend-profile.md` for `trend-profile`
   - `references/serp-and-rollover.md` for SERP or `organicRolloverRate`
   - `references/traffic-observation-semantics.md` for traffic-term lists, traffic timelines, or traffic-profile data
7. Before requesting or interpreting a seller artifact, load `references/sqp-field-semantics.md`. Treat it as the sole acquisition and field-semantics source for user-provided ABA-SQP or Amazon Ads data.

## Source-of-truth boundaries

- This file owns only trigger classification, reference loading, scenario routing, and non-negotiable global acquisition/safety boundaries. It may point to an owner module but must not define endpoint contracts, shared workflow procedures, field semantics, or scenario-specific stage logic.
- `cli-contract.md` owns only the project-wide invocation form, command-identity validation, execution-environment permission handling, caller/CLI responsibilities, composite-result reuse, result acquisition, transport-status precedence, terminal-interface classification, retry ownership, and partial-result handling. It must not define skill-specific command allowlists, endpoint fields, keyword evidence meaning, scenario selection, conclusion authority, or user-facing rendering.
- `reference.md` owns only production API and acquisition-surface facts: availability, request parameters, response schema, endpoint-specific status meaning, batching, dates, and billing. It may name fields and capabilities to describe their contract, but must not redefine the shared CLI contract, Agent workflow, action/output policy, business interpretation, or scenario transitions.
- `execution-guide.md` owns only the shared scenario/stage schema, stage execution and handoff, Gate order/decisions, keyword-stage consequences after shared CLI classification, evidence-level conclusion ceilings, and follow-up reclassification. It may reference owner modules but must not redefine the shared CLI contract, API contracts, field meanings, detailed evidence procedures, detailed diagnosis procedures, output rendering, or scenario-specific capability/stage maps.
- `evidence-protocols.md` owns only shared evidence planning, retrieval, interpretation, reconciliation, coverage, continuity, comparison, and batching procedures inside an active stage. It must not select stages, define Gate outcomes, render handoff lists, or raise conclusion authority.
- `diagnosis-action-protocols.md` owns only the detailed causal-diagnosis and evidence-to-action procedures inside an active stage. It must not select stages, define the Diagnostic Closure Gate result, create handoff routes, or raise conclusion authority.
- `output-rules.md` owns only user-facing language, progress updates, the local interface-failure template, the canonical full-mode report template and headings, Data Notes, and API-usage presentation. It must not select stages, define Gate outcomes, change conclusion authority, or define the contents of the stage-end selection list.
- The metric/observation semantic references (`metrics-*.md`, `serp-and-rollover.md`, and `traffic-observation-semantics.md`) own only documented field meaning, direction, scope, and permitted/prohibited inference. They may identify source fields/endpoints, but must not define production availability or request parameters, shared workflow policy, or scenario routing/stages.
- `sqp-field-semantics.md` owns seller-artifact acquisition order, schema identity, denominator rules, field meaning, and seller-artifact output labels. It must not define ZooData API contracts or scenario-specific stage triggers and conclusions.
- Scenario files own only scenario-specific stage entry requirements, capability selection, conclusion authority, and section-content requirements inside the canonical report template. They define evidence levels, not report headings/order, workflow-completion states, automatic progression, or mandatory traversal of every listed stage. They may reference owner-defined capabilities, fields, and gates, but must not restate, relax, replace, or create exceptions to their contracts or semantics.
- For the documented keyword endpoints and `realtime/product` used by this skill, `{skill_base_dir}/scripts/zoodata.py` owns a fixed blind transport retry budget, preservation of the final response body, and request/transport/credit metadata. It must not assign HTTP-status meaning, choose status-specific workflow actions, or emit Agent-control instructions. Within those command paths, it also must not define field meaning, stage selection, evidence interpretation, conclusion authority, or user-facing prose/report templates; `cli-contract.md` owns result classification and shared invocation handling, `execution-guide.md` owns keyword-stage Gate consequences, and `output-rules.md` owns rendered prose including the local interface-failure template. The credential-only `check` path and opt-in endpoint probes are diagnostic utilities outside this evidence-command contract. Other commands bundled in the shared CLI remain outside this skill's responsibility map.
- `README.md` is a human-facing package overview and module index only. It must not define or modify runtime routing, endpoint contracts, workflow policy, field semantics, stage transitions, or conclusion authority.
- Cross-module references are allowed; cross-module redefinition and duplicated policy are not. When statements span modules, split API fact, shared workflow consequence, field interpretation, and scenario application into their respective owners.
- Apply each rule from its responsible owner module above. A downstream module may narrow behavior but must not override an owner contract.

## Non-negotiable boundaries

- Require `ZOODATA_API_KEY`. If it is missing or rejected, follow the credential procedure in `execution-guide.md`; do not substitute public web data.
- Use the bundled `{skill_base_dir}/scripts/zoodata.py` for documented keyword endpoints and `realtime/product`; the bundled manifest `scripts/allowed-commands.json` enforces that scope — the CLI refuses out-of-scope subcommands with a structured `COMMAND_NOT_ALLOWED` error before any API request. Use ZooData WebTools `/search`, `/scrape`, and `/scrape-interactive` only through an exposed, documented ZooData WebTools surface after inspecting its live schema.
- Use only the acquisition routes whitelisted in `reference.md`. WebTools `/search` is permitted URL discovery; it is not `products/search`. Never use `products/search`, external browser automation, direct Amazon navigation, or non-ZooData public web search as evidence or fallback.
- WebTools calls are read-only public-page acquisition. Never use `/scrape-interactive` actions to log in, submit forms, purchase, or otherwise change page or account state; use click/write/press/scroll/JavaScript actions only to render or reveal the requested public content.
- Treat keyword inputs as Amazon search queries. Default an omitted marketplace to `US`; choose T-1 or earlier before the first request for endpoints requiring `date` or `dateTo` unless the user requests today's data.
- ZooData keyword data is estimated search, visibility, rank, placement, and impression evidence. It is not the seller's ABA-SQP conversion funnel. Keep product-specific value, profitability, bids, spend, budgets, pauses, negatives, and unconditional go/no-go decisions within the evidence authority defined in `execution-guide.md`.
- Preserve returned status, period, subject, field scope, and uncertainty. `status=empty` is an observation-coverage boundary, not proof of low demand.
- Do not report an API root cause, strategy recommendation, or undocumented metric as though the API returned it.

## Execution entry

Use:

```bash
python {skill_base_dir}/scripts/zoodata.py <documented-subcommand> ...
```

Run bare `python {skill_base_dir}/scripts/zoodata.py check` for credential diagnostics only. Without `--endpoints` or `--keyword-endpoints`, it makes no evidence calls; those opt-in probe flags consume credits and are outside this skill's evidence workflow.

The bundled manifest allows exactly: `keyword-detail`, `keyword-market-profile`, `keyword-trend-profile`, `keyword-trend`, `keyword-extends`, `keyword-search-results`, `keyword-competitor-product-keywords`, `keyword-product-traffic-terms`, `product-traffic-terms-profile`, `product-traffic-terms-timeline`, `product`, and the diagnostic `check`.

WebTools has no bundled subcommand in this skill. Use only an exposed ZooData WebTools session/callable surface as documented in `reference.md`.
