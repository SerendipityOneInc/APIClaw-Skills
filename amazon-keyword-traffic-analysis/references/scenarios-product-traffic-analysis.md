# Product Traffic Analysis Capability Guide

Use this downstream scenario after loading the applicable top-level references. It selects evidence for ASIN-centered traffic structure, change, trend, and health questions and must align upward with `execution-guide.md`, `evidence-protocols.md`, `diagnosis-action-protocols.md`, `output-rules.md`, `reference.md`, and the field-semantic references; it does not authorize causal or operating conclusions beyond them.

## Scenario boundary

This scenario owns product traffic analysis. The ASIN is the primary subject; keyword evidence is used only to explain or validate that product's observed traffic.

- Apply it only after `SKILL.md` has selected the ASIN-centered product-traffic route. Requests outside this conclusion boundary must be reclassified through that routing owner.
- A broad ASIN traffic analysis, overview, or health request enters the product traffic health overview directly. Do not require the user to choose between structure and change before selecting this scenario.
- Do not equate a returned traffic observation with clicks, conversion, sales attribution, profitability, or advertising effectiveness. Seller-real conclusions remain gated by the later evidence stages.

## Capability combinations

| Product traffic question | Primary capability | Add only when the named conclusion requires it |
|---|---|---|
| Broad health overview or ASIN-wide structure/change | `product-traffic-terms-profile` | Stop when the returned aggregate modules answer the question; do not reconstruct or duplicate them from one traffic-term page |
| Current traffic terms, sources, contributors, or one named term's current visibility/placement | `keywords/product-traffic-terms` | For a named term, select only its exact returned row after retrieval; add `search-results` only when the question explicitly requires that keyword's observed SERP placement. Select `keywords/competitor-product-keywords` before retrieval only for competitor/overlap framing; it is not a runtime-failure fallback |
| Named ASIN × keyword movement or trend | `product-traffic-terms-timeline` | Add only the market, SERP, product-event, or aggregate evidence required to resolve the named movement question |
| External keyword demand / ABA-rank movement | `trend-profile` | Use raw `trend` only for explicitly required weekly points absent from the metric profile |
| Observed keyword SERP structure | `search-results` | Use only for a named SERP or placement question |
| Current product representation | `realtime/product` | Use only when the named diagnosis requires current product evidence absent from compatible carried data or timeline snapshots |

If the aggregate profile is empty or unavailable, do not reconstruct it from traffic-term rows. If neither ASIN traffic-list endpoint is available, do not make keyword-level product traffic-source claims. `detail`, `market-profile`, and `search-results` cannot replace those contracts.

Apply the shared diagnostic procedure from `diagnosis-action-protocols.md` only when the active question asks for a cause, anomaly explanation, or action. Return every reported diagnostic branch to the `Diagnostic Closure Gate` in `execution-guide.md`.

## Product traffic dimensions

| Dimension | Returned evidence and boundary |
|---|---|
| Aggregate structure | Profile channel shares, impression points, term counts, and current-period scope |
| Aggregate change | Compatible current/previous profile evidence, gained/lost terms, and returned change drivers |
| Current traffic-term structure | `trafficShare`, `estimateImpressionPoint`, placement, coverage, and keyword-size fields from returned traffic-term rows |
| Named-term trend | Timeline placement, traffic, keyword metrics, ad activity, and ASIN snapshots across aligned returned periods |
| External keyword context | Keyword demand, ABA rank, market profile, or SERP evidence acquired only for the named product-traffic explanation |
| Product events | Timeline or current product price, BSR, sales, rating/review count, title, image, offer, and listing observations when available |

Interpret profile, traffic-term, timeline, placement, coverage, and ad-activity fields only through `traffic-observation-semantics.md`. A product-traffic health conclusion is an Agent synthesis bounded by returned dimensions; it is not an API health score. Report the health of each supported dimension and leave unsupported dimensions unresolved instead of producing an undocumented composite score.

## Supported report outputs

- Product traffic health overview covering the returned structure, comparison, coverage, and unresolved dimensions.
- Current traffic-term table with contribution, placement/coverage, and keyword-size evidence.
- Change table comparing compatible returned periods and fields.
- Named ASIN × keyword timeline with product, placement, traffic, demand, and event evidence kept at their returned grains.
- Evidence-bounded movement or anomaly explanation that separates external keyword demand from product-side visibility, placement, ad-activity, and product-event evidence.
- A handoff of selected traffic terms for skill-owned follow-up reclassification when the user asks about their value; product traffic evidence remains supporting ASIN context and does not become the keyword-value conclusion.

## Evidence stages

| Stage | Entry input | Evidence | Conclusion authority |
|---|---|---|---|
| 1A. Product traffic health overview | ASIN + broad traffic analysis/health request, current aggregate structure question, or ASIN-wide change question without a named keyword | `product-traffic-terms-profile` interpreted through `traffic-observation-semantics.md` | Describe returned aggregate structure, compatible current/previous movement, and dimension-level health boundaries. Do not infer omitted modules, per-keyword contribution, longer-term trend, or cause. |
| 1B. Current traffic-term or named-visibility structure | ASIN + explicit current traffic-term, source, contribution, candidate-discovery, or named ASIN × keyword visibility/placement/exposure question without movement or causal intent | Traffic-term list, narrowed locally to the exact returned keyword row when a target term is named, interpreted through `traffic-observation-semantics.md`; add `search-results` only for an explicitly requested observed-SERP placement conclusion | Describe the returned keyword-level product traffic structure or the named term's current visibility, placement, exposure, and coverage posture. Do not infer movement from one period, judge keyword value, infer causes, or give operating priority. |
| 2. Named traffic-term trend diagnosis | ASIN + keyword + relevant observation range + movement, trend, anomaly, or causal question | Timeline plus only the external keyword, SERP, product-event, or aggregate evidence required by the named product-traffic question | Give the movement description, product-traffic health implication, and explanation status permitted by the semantic owner and shared conclusion gates. Do not infer seller conversion, profitability, bids, or budget. |
| 3. Seller-funnel impact calibration | Explicit seller-funnel, conversion-impact, or product-priority request + compatible product-traffic evidence + SQP artifact for one named ASIN × keyword | Compatible carried evidence plus user-provided ABA-SQP interpreted through `sqp-field-semantics.md` | Update only the funnel, conversion-impact, or product-priority conclusion supported for the named scope. Do not give Ads economics, profitability, exact bid, or budget conclusions. |
| 4. Ads-performance calibration | Explicit Ads-performance request + compatible earlier-stage evidence + Ads artifact for one named ASIN × keyword | Compatible carried evidence plus the user-provided Ads search-term report interpreted through `sqp-field-semantics.md` | Give only the attributed Ads-performance conclusion supported for the named scope. Do not infer profitability or recommend a bid or budget. |
| 5. Profitability calibration | Explicit profitability request + compatible earlier-stage and Ads evidence + seller-supplied unit economics or an economics-grounded break-even/target ACOS or ROAS | Compatible carried evidence plus the supplied Ads performance and economics interpreted through `sqp-field-semantics.md` | Give only the named profitability conclusion supported for the preserved scope. Do not give an exact bid or budget decision. |
| 6. Advertising-control decision | Explicit exact bid or budget request + compatible earlier-stage evidence + the complete controlled-target, performance, current-control, objective/economics, and validation inputs required by `diagnosis-action-protocols.md` | Compatible carried evidence plus only the seller inputs required for the named control under `diagnosis-action-protocols.md` and `sqp-field-semantics.md` | Give only the named reversible control decision when fully authorized; otherwise conclude with the exact unresolved evidence boundary and no number. |

### Stage application constraints

- Apply the shared `Interactive Stage Gate`, `Stage Handoff Closure Gate`, and `Stage-End Selection List Rule` from `execution-guide.md`. The rows above are evidence levels, not a required traversal.
- Stages 1A and 1B are alternative current-product entry points selected by the requested deliverable. A broad health request enters Stage 1A; an explicit traffic-term/source request or a current named-term visibility/placement/exposure request enters Stage 1B. Do not call both merely to make the report broader.
- When one request explicitly requires both aggregate health and exact traffic-term contributors, complete Stage 1A first and expose Stage 1B only when the unresolved conclusion requires its row-level evidence.
- Stage 1A follows metric-first access. Preserve profile item status, coverage, current/previous period scope, returned modules, fields, and evidence. Do not reconstruct the profile from traffic rows.
- Stage 1B may use Top-N wording only when the shared ranked-detail protocol verifies the exact sort field, direction, page, page size, filters, identity, period, and usable row count. Otherwise describe only the returned rows.
- Stage 1B discovers product traffic terms or describes one named term's current product-side observation; it does not determine keyword value or movement from a single period. Reclassify any follow-up through `SKILL.md` and reuse compatible ASIN traffic evidence only when the selected scenario permits it.
- Stage 2 requires one named keyword and a relevant range. Do not call the timeline for an unnamed ASIN-wide question or use a current traffic-term row as a movement series.
- Separate external keyword movement from product-side movement. Keyword trend evidence can explain market context; it does not by itself establish that the product gained or lost visibility. Product timeline evidence can show product-side movement; it does not by itself establish market demand or cause.
- Do not call `realtime/product` or page acquisition during Stage 1A or Stage 1B unless the user's current question explicitly requires a current product-representation field that those traffic contracts cannot provide.
- Stage 1A does not authorize SQP interpretation. At seller-data evidence levels, load `sqp-field-semantics.md` and follow its acquisition, sequencing, sufficiency, and field-interpretation rules.
- Do not present a bid, budget, pause, negative-keyword, profitability, or unconditional health/action conclusion before the required seller-data stage.

## Section content requirements

Use the canonical Full-Mode Stage Output template from `output-rules.md` without renaming, adding, removing, or reordering its report sections.

- Put the active stage's returned product-traffic observations and period/coverage scope in Evidence.
- Put dimension-level health interpretation, movement reconciliation, bounded hypotheses, and unresolved diagnostic boundaries in Analysis.
- Put only the product-traffic health or diagnostic conclusion authorized by the active stage in Conclusion.
- Do not include a generic list of possible causes, a separate keyword-value verdict, a repeated earlier-stage report, or later-stage analysis in the same response.
- When a supported continuation selects traffic terms for keyword-value analysis or named-term trend diagnosis, place every selectable term and its observed reason directly in the single final numbered selection list under the shared handoff rule.
