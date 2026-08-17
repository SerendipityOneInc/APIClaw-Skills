# Evidence Protocols — Amazon Keyword Intelligence

This file owns shared evidence planning, retrieval, interpretation, reconciliation, coverage, continuity, and batching procedures. It operates inside the active stage selected by `execution-guide.md`; it does not select stages, define Gate outcomes, or raise conclusion authority.

## Contents

- [Evidence planning and interpretation](#evidence-planning-and-interpretation)
- [Tool and contract discipline](#tool-and-contract-discipline)
- [Metric-First Access Protocol](#metric-first-access-protocol)
- [Claim Scope and Ranked Detail Protocol](#claim-scope-and-ranked-detail-protocol)
- [Batch Response Protocol](#batch-response-protocol)
- [Partial Data Protocol](#partial-data-protocol)
- [Cross-Metric Reconciliation Protocol](#cross-metric-reconciliation-protocol)
- [Evidence Coverage Protocol](#evidence-coverage-protocol)
- [Valid No-Data Reporting](#valid-no-data-reporting)
- [Cross-Stage Evidence Continuity Protocol](#cross-stage-evidence-continuity-protocol)
- [Comparative Claims](#comparative-claims)
- [Date and channel handling](#date-and-channel-handling)
- [Anomaly evidence minimums](#anomaly-evidence-minimums)
- [Monitoring cadence](#monitoring-cadence)

## Evidence planning and interpretation

Inside the active stage, keep acquisition and judgment logically separate:

1. Translate the user's current question into claim-sized evidence needs allowed by the stage's `Evidence` cell.
2. Map each need to the primary documented capability and exact expected field before retrieval. Do not draft a verdict or strategy label yet.
3. Retrieve the smallest sufficient response, applying metric-first and batch rules below.
4. Inspect returned status, period, coverage, subject, and fields. After every result, return to the Interface Failure Stop Gate before another command.
5. Load the field-semantic owner routed by `SKILL.md`, then map every candidate claim to exact returned evidence and a forbidden stronger inference.
6. Reconcile material signals, account for evidence coverage, and return the evidence ledger to the guide-owned Evidence and Conclusion Authority Gates.

Documentation alone is never a metric result. An additional call is justified only when one named stage inference remains unresolved, another documented contract contains the missing evidence, and no interface failure has occurred.

When a required comparison value or period boundary is absent, use another documented capability only if it preserves the claim's subject, grain, marketplace, and comparison meaning inside the active stage. A named ASIN × keyword timeline may resolve a named keyword movement question, but it cannot replace an ASIN-wide aggregate traffic-term profile. If no equivalent authorized capability exists, leave the comparison unavailable and do not infer the missing value or period from cadence.

## Tool and contract discipline

- Read candidate CLI help or live tool schema before selection; never infer capability from a name.
- Prefer the documented local CLI. Use an exposed ZooData session/callable surface only after inspecting its exact live schema.
- For a known page URL, use ZooData WebTools `/scrape`; use `/scrape-interactive` only when rendering or page actions are required. Use WebTools `/search` only when the URL must first be discovered.
- WebTools `/search` is not `products/search`. Never substitute external browser automation, direct Amazon navigation, or non-ZooData public search.
- Use exact documented arguments, dates, limits, status meanings, and callable mappings from `reference.md` and CLI help.
- If no documented execution path exists, return the evidence gap to the guide instead of substituting an adjacent source.
- Never switch execution surfaces as runtime recovery after an interface failure.

## Metric-First Access Protocol

1. Call the matching metric endpoint first when one exists for the stage inference.
2. Map each requested conclusion to a returned metric dimension/field and verify what it can express.
3. Stop when every named stage inference is supported.
4. Distinguish calculation-data absence from metric-contract insufficiency. Data absence normally ends that inference; it does not automatically authorize source-data access.
5. Descend only after a successful metric response when the documented data contract exposes extra fields/grain required for one named inference.
6. Record the missing inference and exact extra fields expected before descending.
7. Do not duplicate or double-check a supported metric through a source endpoint.
8. Direct data access is correct when rows/series are the requested deliverable or no corresponding metric exists.

## Claim Scope and Ranked Detail Protocol

Every interpretation must carry a resolved scope tuple: `(source, subject, marketplace/site, requested and resolved period, metric, unit, population or returned coverage, filters/channels, grain)`. Add sort field, sort direction, page, page size, and tie/missing-value handling whenever ranking or Top-N language is used. An unresolved material scope component limits or blocks the claim; it does not authorize a vague label.

For paginated detail rows:

1. Verify the documented sort contract and the actual `_query.params` or equivalent request metadata before assigning a rank label.
2. A Top-N statement is allowed when the response identity and period match the claim, page 1 was requested, the exact `sortBy` and `sortOrder` are known, filters/channels are disclosed, and at least N usable sorted rows were returned. State the ranking as `Top N by <exact metric> <direction>` within that resolved scope.
3. If page size exceeds N, use only the first N compatible rows. If fewer than N usable rows return, state the actual count. If missing sort values, ties, deduplication, or unstable pagination affect the boundary, disclose the handling and do not imply a strict unique order that the evidence does not establish.
4. When sort identity or pagination coverage is unverified, say only `the N returned rows` or an equivalent localized phrase. Do not relabel them Top N.
5. Top N describes an ordered slice under one metric and request scope. It does not mean the endpoint universe is exhaustive, that the same rows are top under another metric, or that the rows have the strongest product value, conversion, or profitability.

For aggregate, comparative, entry/exit, growth, or decline explanations, state the exact current and comparison periods, population or set boundary, metric/unit, and included channels or filters. Terms such as `share`, `new`, `lost`, `increase`, and `decrease` must name what denominator, set, or field changed. Preserve that scope through the analysis and conclusion rather than replacing it with an unqualified business label.

## Batch Response Protocol

1. After a capability is justified, collect all subjects with compatible documented context.
2. Prefer documented batch arguments over repeated single calls. Deduplicate case-insensitively and preserve first-occurrence order.
3. Split sets larger than the documented limit into sequential valid chunks and restore global input order.
4. Use a single-subject call only for one subject, incompatible contexts, or a capability without batching.
5. Inspect every item's status; retain valid empty items and reasons, and analyze only usable items.
6. Outer `success=true` does not upgrade empty items.
7. Use returned `meta.creditsConsumed`; do not estimate billing from request size or batch width.
8. Do not call both metric and source data merely because both support batching.

## Partial Data Protocol

Apply this only to successful responses containing both usable and valid empty/unsupported evidence. A service/interface failure returns immediately to the Interface Failure Stop Gate.

1. Produce claims only from retrieved evidence.
2. Mention a missing unit only when it blocks the current stage decision.
3. Never infer a missing capability's output from non-equivalent evidence.
4. Downgrade the stage conclusion scope to the weakest evidence required by the joint claim.
5. Return any resolvable gap to the guide-owned handoff rule; do not request an input directly from this module.

## Cross-Metric Reconciliation Protocol

1. Group returned metrics by the operator question they inform.
2. Normalize subject, measure, population/grain, period, reference scope, direction, and conclusion authority.
3. Classify each relationship internally:
   - `aligned`: synthesize only the common supported scope;
   - `complementary`: preserve each distinct axis and bounded joint meaning;
   - `incomparable`: report separately without a shared score or ranking;
   - `genuinely inconsistent`: verify context/status/fields and retain the conflict unless discriminating evidence exists.
4. Preserve every material signal. Do not average unlike scores, silently choose one, invent a causal bridge, or create an undocumented umbrella metric.
5. Limit the synthesis to the intersection of evidence authority.
6. Integrate material reconciliation into the initial stage analysis, not a later corrective reply.
7. Use the applicable semantic owner for field meaning and forbidden inference.
8. Keep internal relationship labels out of user output unless one materially aids domain understanding.

## Evidence Coverage Protocol

1. Inventory decision-relevant units returned by every justified call.
2. Give each unit one internal disposition: `explained`, `synthesized`, `unavailable`, `inapplicable`, or `superseded`; record a scope/status reason for non-explained units.
3. Account for every usable material unit with its meaning, subject, scope, period, and direction.
4. Assign each material unit to an operator question and explain whether it supports, limits, complements, conflicts with, or is incomparable to the other evidence.
5. Include decisive supporting and limiting evidence in the conclusion basis.
6. Reconcile `returned units → dispositions → evidence → analysis → conclusion basis`; an unaccounted material unit blocks the conclusion.

## Valid No-Data Reporting

A valid `status=empty` or documented unsupported result is retrieval evidence, not an interface error.

1. **Evidence:** identify source, subject, requested/resolved period, returned status, and whether any usable field exists.
2. **Analysis:** identify the exact current-stage claims left untested.
3. **Conclusion:** state only the supported boundary and return any authorized resolvable gap to the guide-owned handoff rule.

Do not replace this chain with generic capability disclaimers, guessed recommendations, or a negative-demand conclusion.

## Cross-Stage Evidence Continuity Protocol

1. Build a prior-stage ledger containing field identity, value/direction, period, scope, authority, and decision axis.
2. Check compatibility with current subject, keyword, marketplace, period, and decision. Reuse compatible evidence; refresh only when the stage requires a newer or incompatible scope.
3. Mark each prior material signal `carried`, `updated`, `superseded`, `incompatible`, or `unavailable`.
4. Merge observations by decision axis without collapsing different target levels, populations, or grains.
5. Resolve accessibility/difficulty claims separately for target-set entry, higher-position competition, stability, and the observed subject's current gap.
6. Re-run reconciliation and limit the new conclusion to combined authority. Never strengthen a later conclusion merely because an earlier adverse signal disappeared from the report.

## Comparative Claims

- Compare a product, listing, CTR, CVR, rank, or traffic quality to competitors only with direct same-metric, same-query, same-marketplace, comparable-period, and comparable-placement evidence.
- Otherwise compare to a disclosed market median, midpoint, or band rather than named competitors.
- State how a calculated average/median/band was formed and its limitation.
- Never treat a market-wide query average as competitor-specific proof.
- When position/placement cannot be controlled, downgrade confidence and avoid strong superiority claims.

## Date and channel handling

- Treat keyword inputs as search queries, select dates from the documented contract, and report returned periods rather than inferred periods.
- If a date endpoint returns `status=empty` with a null `resolvedDate` (the requested date is outside the available window per `reference.md`), reselect a recent completed in-window week and re-request once before interpreting; do not treat the out-of-window response as keyword evidence. A `status=empty` result carrying a non-null `resolvedDate` is valid no-observation evidence and is not re-requested on this basis.
- Never compare incompatible grains or periods as equivalent.
- Keep organic and sponsored observations separate.
- Do not equate placement-record counts with exposure contribution or exposure with CPC, conversion, bid economics, or budget priority.

## Anomaly evidence minimums

| Signal type | Minimum evidence | Maximum confidence label |
|---|---|---|
| Weekly trend change | Two or more comparable weekly points in the same direction | 🔍 |
| SERP change | Two comparable timestamps showing a changed rank mix | 🔍 |
| One-day movement | One snapshot difference | 💡 |

## Monitoring cadence

- Use weekly cadence for keyword opportunity watchlists, launched terms, and incident follow-up with the latest resolved weekly period.
- Use explicitly daily-granular seller Ads or other first-party evidence for intraweek monitoring; do not present repeated weekly ZooData calls as daily tracking.
