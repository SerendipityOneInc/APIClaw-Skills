# Keyword Analysis Capability Guide

Use this downstream scenario after loading the applicable top-level references. It selects evidence combinations for a target-keyword question and must align upward with `execution-guide.md`, `evidence-protocols.md`, `output-rules.md`, `reference.md`, and the field-semantic references; it does not define independent decision or action rules.

## Scenario boundary

This scenario owns keyword-centered analysis. The keyword is the primary subject; ASIN evidence may refine product fit without turning the conclusion into a product traffic-health diagnosis.

- Analyze keyword demand, keyword-market and SERP traffic structure, and keyword trend to judge the term's evidence-bounded value.
- Use keyword analysis as supporting evidence for product traffic analysis when a product-side movement question requires external demand, competition, or SERP context. The keyword conclusion does not by itself establish product traffic health or cause.
- Treat traffic-term value as demand, structure, trend, visibility, and product-fit evidence. Without seller ABA-SQP, Ads performance, and required economics, do not equate it with measured conversion, profitability, bid, or budget value.
- Requests outside this keyword-centered conclusion boundary must be reclassified through the routing owner in `SKILL.md`.

## Capability combinations

| User question / available subject | Primary capabilities | Optional capability when the named question requires it |
|---|---|---|
| Market demand, structure, or entry context for a keyword | `market-profile` + `trend-profile` | `search-results` for observed product type, intent, or placement structure; `detail` for a documented raw field absent from the metric contract |
| Official ZooData organic rollover/stability indicator | `detail.snapshotData.organicRolloverRate` | Load `serp-and-rollover.md`; do not relabel it as a Top-N turnover calculation |
| Keyword plus ASIN admitted to this scenario | Carry compatible market evidence + `keywords/product-traffic-terms` filtered to the target keyword + `realtime/product` or compatible carried direct product evidence | `search-results` only for a named SERP question; do not substitute `keywords/competitor-product-keywords` for the target-ASIN route. |
| Seller-real calibration | User-provided ABA-SQP, plus Amazon Ads data when economics or execution settings are requested | Load `sqp-field-semantics.md` before interpreting SQP fields |

## Evidence stages

| Stage | Entry input | Evidence | Conclusion authority |
|---|---|---|---|
| 1. Market screen | Target keyword | `market-profile` + `trend-profile`; SERP evidence only for a named question | Give a market-screen conclusion and decide only whether ASIN-level evidence is warranted. Do not give product-specific priority or operating conclusions. |
| 2. ASIN observation | Compatible Stage 1 evidence + target ASIN | Carried market evidence + the exact target-keyword row returned by `keywords/product-traffic-terms` for the target ASIN + `realtime/product` or compatible carried direct product evidence; add `search-results` only for a named SERP question | Give the target keyword's provisional ASIN-fit posture. Do not give seller-measured conversion, final product-specific priority, profitability, bid, or budget conclusions. |
| 3. Candidate comparison | Explicit user request for a multi-term comparison + user-confirmed terms + compatible ASIN evidence | Batched market evidence for the confirmed comparison set plus retained direct product evidence | Give an evidence-bounded multi-term validation pool. Do not replace the known target-term decision with candidate expansion or give seller-calibrated priority. |
| 4. Seller-funnel calibration | Explicit seller-funnel or product-priority request + compatible market and ASIN evidence + SQP artifact for one named target term | Compatible carried evidence plus user-provided ABA-SQP interpreted through `sqp-field-semantics.md` | Give the product-specific funnel and priority conclusion supported for that target term. Do not give Ads economics, profitability, exact bid, or budget conclusions. |
| 5. Ads-performance calibration | Explicit Ads-performance request + compatible earlier-stage evidence + Ads artifact for one named target term | Compatible carried evidence plus the user-provided Ads search-term report interpreted through `sqp-field-semantics.md` | Give only the attributed Ads-performance conclusion supported for the named scope. Do not infer profitability or recommend a bid or budget. |
| 6. Profitability calibration | Explicit profitability request + compatible earlier-stage and Ads evidence + seller-supplied unit economics or an economics-grounded break-even/target ACOS or ROAS | Compatible carried evidence plus the supplied Ads performance and economics interpreted through `sqp-field-semantics.md` | Give only the named profitability conclusion supported for the preserved scope. Do not give an exact bid or budget decision. |
| 7. Advertising-control decision | Explicit exact bid or budget request + compatible earlier-stage evidence + the complete controlled-target, performance, current-control, objective/economics, and validation inputs required by `diagnosis-action-protocols.md` | Compatible carried evidence plus only the seller inputs required for the named control under `diagnosis-action-protocols.md` and `sqp-field-semantics.md` | Give only the named reversible control decision when fully authorized; otherwise conclude with the exact unresolved evidence boundary and no number. |

## ASIN-fit posture labels

Use these labels only in Stage 2 or Stage 3 after the required keyword-market and directly observed ASIN evidence is available. They describe keyword value or fit for the product; they are not product traffic-health labels or operating decisions.

- `Established posture`: the target term has directly observed product fit and meaningful current ASIN traffic or comparatively strong placement evidence.
- `Headroom validation`: keyword-market and product-fit evidence support further validation, but seller-funnel evidence is still required for final product-specific priority.
- `Observe`: evidence is relevant but sparse, unstable, mixed, or insufficient for a stronger value conclusion.
- `No current support`: current evidence shows weak fit or lacks support for further validation. Do not assign it merely because one endpoint is empty or one observation is poor.

### Stage application constraints

- Apply the shared `Interactive Stage Gate`, `Stage Handoff Closure Gate`, and `Stage-End Selection List Rule` from `execution-guide.md`. The rows above are evidence levels, not a required end-to-end traversal.
- For natural target-keyword questions such as `worth targeting` or `worth focusing on`, Stage 1 supports only the market-screen conclusion; higher product-specific conclusions require the matching later-stage evidence.
- Stage 3 applies only to an explicit multi-term comparison. A known target term may use Stage 4 after compatible Stage 1 and Stage 2 evidence exists; do not require candidate expansion or candidate-list confirmation first.
- Do not interpret Stage 2 evidence before a target ASIN is supplied. Do not interpret SQP before compatible market and ASIN evidence exists for the named target term.
- At a seller-data boundary, load `sqp-field-semantics.md` and follow its acquisition, sequencing, sufficiency, and field-interpretation rules. Do not redefine those shared rules here.
- Do not request price, contribution margin, budget, SQP, or Ads data as a substitute for unavailable market demand, trend, structure, or SERP evidence. Those inputs cannot repair a failed Stage 1 retrieval.

## Supported report outputs

- Market-screen result: demand/trend/market-structure/SERP evidence and whether ASIN-level validation is supported.
- ASIN observation: carried market constraints plus current ASIN fit, placement, traffic, and observed posture.
- Candidate validation: a market-profile-validated pool for seller-funnel validation.
- Seller-funnel calibration: SQP-based interpretation combined with retained earlier-stage constraints.
- Ads-performance calibration: attributed advertising performance for the explicitly requested named scope.
- Profitability or advertising-control calibration: only when the user explicitly requests that decision and supplies its additional economics or control inputs.

## Report progression

- Present the active stage's new evidence plus only the compatible prior-stage evidence needed for its analysis and conclusion.
- With ASIN evidence, retain compatible market constraints and add the observed subject posture without collapsing market and subject signals.

Use `evidence-protocols.md` for reconciliation and coverage, `diagnosis-action-protocols.md` only for a causal/action question, and `output-rules.md` for rendering.

## Section content requirements

Use the canonical Full-Mode Stage Output template from `output-rules.md` without renaming, adding, removing, or reordering its report sections.

- Keep Data Notes limited to source, returned period, and current semantic scope.
- Put only the active target-keyword stage's observations in Evidence, its reconciliation in Analysis, and its authorized judgment in Conclusion.
- Do not include another stage's evidence or conclusion or expose internal reasoning mechanics.
