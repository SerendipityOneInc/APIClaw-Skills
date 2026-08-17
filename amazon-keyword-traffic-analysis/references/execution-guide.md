# Execution Guide — Amazon Keyword Intelligence

This file defines the shared scenario/stage contract and Gate system for Amazon keyword workflows. Scenario files instantiate stages; this guide controls how one stage is selected, executed, bounded, and closed.

## Contents

- [Authority and routing](#authority-and-routing)
- [Execution mode](#execution-mode)
- [Scenario contract](#scenario-contract)
- [Stage schema](#stage-schema)
- [Shared evidence levels](#shared-evidence-levels)
- [Stage execution sequence](#stage-execution-sequence)
- [Gate order](#gate-order)
- [Structured Field Identity Gate](#structured-field-identity-gate)
- [Interactive Stage Gate](#interactive-stage-gate)
- [Interface Failure Stop Gate](#interface-failure-stop-gate)
- [Evidence Gate](#evidence-gate)
- [General Conclusion Authority Gate](#general-conclusion-authority-gate)
- [Diagnostic Closure Gate](#diagnostic-closure-gate)
- [Stage Handoff Closure Gate](#stage-handoff-closure-gate)
- [Stage-End Selection List Rule](#stage-end-selection-list-rule)
- [Final Output Gate](#final-output-gate)
- [Pending Handoff Reclassification Rule](#pending-handoff-reclassification-rule)
- [Scenario Selection Rule](#scenario-selection-rule)
- [Candidate Validation Rule](#candidate-validation-rule)
- [HTTP Validation Rule](#http-validation-rule)
- [Credential and Credit Failures](#credential-and-credit-failures)

## Authority and routing

Apply this control sequence:

`question → scenario → active stage → stage evidence → Gate checks → stage conclusion → stage-end selection list → final output validation`.

- `SKILL.md` owns trigger classification, module loading, and non-negotiable boundaries.
- This guide owns the shared scenario/stage structure, Gate order and decisions, evidence-level conclusion ceilings, stage handoff, final pre-send validation, and follow-up reclassification.
- `evidence-protocols.md` owns shared evidence planning, retrieval, interpretation, reconciliation, coverage, continuity, and batching procedures.
- `diagnosis-action-protocols.md` owns the detailed causal-diagnosis and evidence-to-action procedures. This guide retains the Diagnostic Closure Gate that decides whether a diagnostic stage may close.
- `output-rules.md` owns language, progress updates, the canonical report template and headings, Data Notes, and API-usage presentation. This guide retains the stage-end selection contract.
- Scenario files define scenario-specific stage entry requirements, capability combinations, conclusion authority, and section-content requirements. They must not redefine report headings/order, workflow-completion states, automatic progression, Gate exceptions, or a competing handoff rule.
- `reference.md` remains authoritative for API facts. Field-semantic references remain authoritative for returned-field meaning and inference limits.

When owner modules conflict, apply the stricter evidence/action limit. Never recover a capability from non-equivalent evidence or let a downstream scenario weaken a Gate.

## Execution mode

| Task type | Mode | Stage behavior |
|---|---|---|
| One exact field or snapshot lookup | Quick | Answer under `output-rules.md § Quick Mode Output`; no scenario stage is required unless the follow-up broadens the task. |
| Expansion, target-keyword judgment, product traffic analysis, or product traffic-health diagnosis | Full | Select and complete exactly one applicable scenario stage, then render the stage-end selection list. |

Quick Mode still applies the Structured Field Identity Gate, Interface Failure Stop Gate, and Final Output Gate. It is not a multi-stage workflow and does not require the stage-end list.

## Scenario contract

Every full-mode scenario must:

1. define an ordered set of evidence stages using the Stage Schema below;
2. select capabilities only for the active stage's named evidence;
3. keep every conclusion within that stage's authority and the shared evidence ceiling;
4. inherit every applicable Gate in this guide;
5. render the active stage's new evidence plus only the compatible prior-stage evidence needed to support its analysis and conclusion; and
6. close every normally completed stage with the Stage-End Selection List Rule.

The ordered stage list expresses increasing or different evidence authority. It is not a mandatory traversal, automatic queue, workflow status model, or promise that every later stage will be visited.

## Stage schema

Every scenario stage row must contain exactly these runtime roles:

| Role | Required definition |
|---|---|
| `Stage` | A stable stage name and the decision scope it addresses. |
| `Entry input` | The exact subject, selection, artifact, or compatible prior evidence required before the stage may start. |
| `Evidence` | The capability combination or user-provided evidence that may be acquired and interpreted inside this stage. |
| `Conclusion authority` | The strongest conclusion this evidence can support and the stronger conclusions still prohibited. |

Do not add a transition, completion, next-stage trigger, or handoff-status column. The shared handoff rule derives any supported continuation from the user's still-current question, the current conclusion, and the next applicable stage's `Entry input`.

## Shared evidence levels

| Evidence level | Evidence scope | Shared maximum authority |
|---|---|---|
| Market evidence | Keyword demand, trend, market profile, and SERP observations | Market attractiveness, structure, relative difficulty, and directional opportunity |
| Subject observation evidence | Market evidence plus observed ASIN, listing, placement, traffic, or timeline signals | Subject-specific fit, current posture, movement, and evidence-supported bounded hypotheses |
| Seller-real evidence | User-provided ABA-SQP funnel and, when relevant, Amazon Ads performance | Calibrated operating decisions limited to the supplied seller fields |

A scenario may impose a stricter stage ceiling but cannot exceed the shared ceiling.

## Stage execution sequence

For one active full-mode stage:

1. Verify the Stage Entry input and retain later-stage inputs without interpreting them.
2. Translate the current question into the evidence named by the stage. Use `evidence-protocols.md` for evidence planning and capability execution.
3. Retrieve only evidence required to complete this stage. Multiple justified calls and valid batch chunks remain inside one stage.
4. Apply the Interface Failure Stop Gate after every tool or retrieval result before selecting another command.
5. Apply the Structured Field Identity Gate and the routed semantic owner before interpreting returned fields.
6. Apply the Evidence Gate, General Conclusion Authority Gate, and Diagnostic Closure Gate when applicable.
7. Render one stage in `evidence → analysis → stage conclusion` order through `output-rules.md`.
8. After required usage reporting, render the Stage-End Selection List. Do not execute a later stage in the same turn.
9. Apply the Final Output Gate to the complete rendered response immediately before sending it.

Retrieval and interpretation remain separate operations inside the stage, while the stage's `Evidence` cell decides what must be acquired.

## Gate order

| Order | Gate | Apply when | Effect |
|---:|---|---|---|
| 1 | Interactive Stage Gate | A full-mode scenario has been selected | Select one stage whose entry input exists; block later-stage calls. |
| 2 | Interface Failure Stop Gate | After every tool/result | Hard-stop the turn on a qualifying interface failure. |
| 3 | Structured Field Identity Gate | Before translating or interpreting any field | Block interpretation when source identity is unresolved. |
| 4 | Evidence Gate | Before drafting a claim | Require the correct evidence type and forbid endpoint substitution. |
| 5 | General Conclusion Authority Gate | Before the stage conclusion | Cap the conclusion at the shared and scenario-specific authority. |
| 6 | Diagnostic Closure Gate | A causal or anomaly branch is part of the active stage | Block unsupported or abandoned diagnostic branches. |
| 7 | Stage Handoff Closure Gate | After the stage conclusion | Determine which continuation items, if any, are supported without assigning a workflow status. |
| 8 | Stage-End Selection List Rule | Every normally completed full-mode stage | Render all supported continuations plus the fixed new-question/exit item. |
| 9 | Final Output Gate | Immediately before every user-facing send | Validate the entire rendered draft against its selected output route; discard and re-render any noncompliant draft. |
| 10 | Pending Handoff Reclassification Rule | At the next user turn | Follow the user's actual reply instead of forcing the pending path. |

The hard-stop interface, credential, and credit failure routes are not normally completed stages and do not render a stage-end list.

### Structured Field Identity Gate

Before translating or interpreting an API field, screenshot, CSV, or report field:

1. Resolve `(source, view, selected subject, metric path, field, unit, denominator, grain, period)`; leave unreadable components unknown.
2. Preserve the full metric path and ownership. Do not reassign market, brand, ASIN, query, placement, or campaign evidence to another subject.
3. Translate the documented measurement, not a presumed business meaning. Verify compatible denominators before comparing or calculating rates; label each derivation with its formula.
4. Treat cross-stage or cross-metric patterns as bounded relationships, never as causes or operating actions without separately authorized evidence.

### Interactive Stage Gate

1. Complete at most one user-decision stage per assistant turn. A stage changes evidence level, subject scope, candidate set, or decision authority.
2. Enter a stage only when its `Entry input` is available and the user's latest request asks for a report or decision within that stage's `Conclusion authority`. Possession of compatible data does not by itself select a stage. A broad request for a complete analysis does not supply missing inputs or pre-authorize later stages.
3. Keep all calls, field interpretation, analysis, and conclusions inside the active stage's `Evidence` and `Conclusion authority` cells.
4. Retain compatible later-stage data supplied early without interpreting it. Do not ask the user to upload or supply the same exact input again.
5. A supplied required ASIN, file, or candidate set may select a displayed continuation and satisfy its entry input in one reply. Do not require a second confirmation.
6. A displayed final-list number, label, `confirm`, or `continue` selects a route only when its referent is unambiguous. A bare integer refers only to the most recent final numbered selection list; numeric ranks or metric values elsewhere in the report are not selectable identifiers. Do not start the next stage until its required entry input is also available.
7. Do not combine several stage conclusions, call a later-stage capability, or narrate the full future stage list in the current response.
8. Enter a seller-funnel, Ads-performance, profitability, or advertising-control stage only when the user's latest request explicitly asks for the corresponding report or decision. Completion of an earlier stage does not make any later seller-data stage mandatory.
9. Base the active stage conclusion on its new evidence together with compatible prior-stage evidence. Carry only the prior evidence needed for the current question; do not repeat an earlier report or import later-stage evidence.

### Interface Failure Stop Gate

Classify every bundled CLI result through the local `cli-contract.md` before interpreting response fields or selecting another capability. Its terminal-interface classification is a hard interrupt for the active keyword stage and the current turn.

A local parsing, transformation, extraction, or formatting command that fails after a paid API response is also an interface failure for that evidence unit. If the original valid structured response remains available, use it directly without another evidence call; otherwise stop. Never call the same paid endpoint again merely to change output format or recover from local post-processing failure.

1. Do not produce the requested market/product/operating conclusion and do not request ASIN, price, margin, SQP, Ads, or any other next-stage input.
2. Retain earlier successful retrieval for compatible later reuse, but expose it only as permitted by `output-rules.md § Interface Failure Output`.
3. Do not render the normal stage-end selection list.
4. A result that the shared contract classifies as non-terminal may enter the separately supported credential, credit, validation, or `status=empty` route; none of those routes may override a terminal classification.

### Evidence Gate

- Every claim must use the evidence type and subject designed for that claim.
- Do not bridge a missing evidence type with an adjacent endpoint, documentation statement, keyword wording, or unrelated seller field.
- A successful valid empty/unsupported result follows `evidence-protocols.md`; it is not an interface failure and does not silently become negative evidence.
- A causal claim requires discriminating evidence through `diagnosis-action-protocols.md`; a compatible cause list is not a diagnosis.
- Observed facts, Agent inference, provisional action, and seller-calibrated action must remain distinct.

### General Conclusion Authority Gate

- Market evidence cannot support product-specific priority, measured conversion performance, profitability, bids, spend, budget allocation, or unconditional go/no-go decisions.
- Subject observation evidence cannot support measured click/conversion claims without seller-funnel data or profitability/exact ad-budget decisions without Ads performance.
- Intermediate labels describe current posture or validation priority only; they do not authorize execution changes.
- Use bounded language below seller-real evidence. Do not call a pre-seller-data result a final calibrated conclusion.
- Never volunteer a numeric bid, bid range, bid-change percentage, budget amount, or budget-allocation percentage. Such a value is in scope only when the user's latest request explicitly asks for that exact advertising decision.
- An explicit request is not action authorization. A numeric advertising recommendation remains prohibited unless `diagnosis-action-protocols.md` authorizes a `Change` using seller evidence interpreted through `sqp-field-semantics.md`. If authorization is absent, give no number and return only the exact evidence gap to the guide-owned handoff rule.
- Require Amazon Ads performance in addition to ABA-SQP for ACOS/ROAS interpretation, but do not infer profitability from either source alone. A profitability conclusion additionally requires seller-supplied unit economics or an explicit break-even/target ACOS or ROAS grounded in those economics.
- Apply the active scenario's stricter `Conclusion authority` after applying this shared ceiling.

### Diagnostic Closure Gate

Use `diagnosis-action-protocols.md` for the detailed diagnostic procedure, then apply this gate before closing a diagnostic stage:

- Open a branch only when the user requested a causal explanation or the requested decision depends on it.
- Every reported diagnostic branch must be resolved by cited evidence, actively pursued inside the current stage, or represented by one directly matching continuation item in the stage-end list.
- The requested evidence must discriminate the exact explanations named in the unresolved question.
- If no available or requestable evidence can resolve a branch, omit it unless the user's explicit question requires stating the unresolved boundary.
- Do not treat “further investigation is needed” as a closed branch.

### Stage Handoff Closure Gate

After the stage conclusion and before rendering the stage-end list:

1. Re-read the user's still-current question and the current stage conclusion.
2. Add a continuation only when the current decision still requires another evidence level or subject, an authorized source can resolve the named gap, and a scenario stage names the exact `Entry input`.
3. If multiple finite subjects are supported, add each supported subject as its own selectable continuation in the final list. Do not render a separate selectable-subject list in Evidence, Analysis, or Conclusion and then point to it from an umbrella action. If one ASIN, candidate-set confirmation, report, file, or field is required, add one continuation item containing that exact action.
4. If no further evidence is required, do not manufacture a deeper analysis merely because a later stage or capability exists.
5. If the decision remains unresolved but no authorized evidence/input can resolve it, state the boundary and add no continuation route.
6. Scenario rows define evidence levels, not completion or transition states. Do not assume that every stage must be visited, create an automatic loop, or maintain a hidden pending queue.

### Stage-End Selection List Rule

Every normally completed full-mode stage must end with one concise localized numbered selection list after API Usage when present, or immediately after the stage conclusion when no live API data was used. Use the list even when there is only one supported continuation or no supported continuation.

1. Populate continuation items only from the Stage Handoff Closure Gate. Write each continuation label and description in user-domain language; do not expose internal workflow identity, ordering, progression claims, control vocabulary, implementation details, or usage accounting.
2. Keep every user-selectable subject and action out of separate lists in Evidence, Analysis, and Conclusion. Those sections may discuss the underlying evidence and named subjects naturally, but must not assign selection keys, present a candidate/action menu, or ask the user to select from body content.
3. Merge every supported selectable subject and action directly into this one final list. Number the final selection list sequentially with bare integers `1`, `2`, `3`, ... in display order; it is the only user-selectable list in the response. Each item must contain the exact subject label and action needed to make the choice self-contained.
4. When two or more finite subjects support the same repeatable continuation and the next stage accepts a set, first give every subject its own numbered item, then append exactly one numbered `select all` equivalent for that complete displayed subject set. Allow the user to choose one item, multiple individual items, or the select-all item. Do not emit a select-all item for one subject or when the next stage cannot accept a set.
5. For one required ASIN, confirmation, report, file, or field, render that single continuation as one numbered item rather than a prose request.
6. Append exactly one final numbered item, with no description or explanatory suffix, using a localized equivalent of: **Ask another question or end this analysis**.
7. If no continuation is supported, `1` is the only item and is the fixed new-question/exit choice.
8. Put an evidence-supported priority continuation first and mark it with a localized equivalent of `recommended`; otherwise preserve the evidence-supported order without manufacturing a recommendation.
9. Tell the user they may reply with the displayed final-list number or label, one or more final-list numbers or the displayed select-all item when set selection is supported, directly supply/upload the listed input, enter a new question, or state that they want to stop.
10. Do not auto-select an item. A route selection does not waive its stage `Entry input`.
11. Keep the list decision-sized. Do not copy every raw row or append unsupported adjacent analyses.

This list is an interaction contract, not a workflow status. The user is never required to continue.

### Final Output Gate

Apply this gate immediately before every user-facing send, including clarification, Quick Mode, normally completed Full Mode, interface failure, credential failure, credit failure, and validation failure.

1. Select exactly one output route, then obtain that route's complete permitted rendering shape from `output-rules.md` and, for a normally completed Full-Mode stage, the Stage-End Selection List Rule above.
2. Validate the entire draft from its first emitted character through its last emitted character. Text that happens to contain a valid template is not compliant when any prefix, suffix, heading, explanation, separator, or unrelated block falls outside that route's permitted shape.
3. If validation fails, discard the entire draft and render the selected route again from its owner contract. Do not patch the invalid draft, retain its wrapper, or append a correction.
4. For a hard interface failure, validate the complete draft exclusively against `output-rules.md § Interface Failure Output`; any deviation from that owner-defined rendering contract fails this Gate.
5. Apply `output-rules.md § Internal Identifier Rewrite` as an explicit whole-draft rejection check. Keep all identifier definitions, examples, and rewrite requirements authoritative in that output owner.
6. Do not send until the complete assistant draft passes the selected route and the internal-identifier check. If an invalid draft cannot be repaired confidently, discard it and emit only that route's minimal owner-defined rendering. Client-generated task notifications are outside this assistant-output validation boundary.

### Pending Handoff Reclassification Rule

A stage-end list closes the current turn; it does not reserve the next turn.

1. At every follow-up, classify the user's actual latest message through `SKILL.md` before continuing a displayed route.
2. Continue a pending validation only when the message selects its item by displayed final-list number or label and supplies the required entry input, or when it directly supplies that input unambiguously.
3. If a selected item still lacks its ASIN, artifact, candidate set, or field, do not make an evidence call. Re-render the smallest executable selection list containing the required-input action and the fixed new-question/exit item.
4. If the user selects the fixed final item, asks a new question, changes scope, or states that they want to stop, leave the previous handoff inactive and follow the latest instruction.
5. Do not treat arbitrary prose as an ASIN/artifact, invent a missing input, call a later-stage capability, or append a stale request to the new response.
6. Reuse compatible earlier evidence if the user later returns to the prior journey.

### Scenario Selection Rule

- Use the scenario already selected through `SKILL.md`; this guide does not redefine the skill-owned subject or conclusion routing map.
- Inside that scenario, select one stage whose entry input exists and whose conclusion authority matches the current question.
- Combine scenario capabilities only when scenario boundaries are non-exclusive and every call belongs to the same active stage. Never combine scenarios to bypass a Gate or stage ceiling.

### Candidate Validation Rule

Use a scenario label only as a description of the current evidence-bounded validation posture. It must not imply a bid, match type, budget, pause, negative keyword, profitability, or final expansion decision.

Before assigning a product-specific candidate label, require appropriate subject evidence, supported material market dimensions, directly observed product-fit evidence, and no unobserved placement/conversion/strategy inference. A scenario may require more.

### HTTP Validation Rule

- For an HTTP 422 validation state classified by `reference.md`, do not repeat the unchanged request.
- Inspect the structured error and request metadata, then use `reference.md` and CLI help to correct only the documented contract violation before retrying.

### Credential and Credit Failures

- If `ZOODATA_API_KEY` is missing, run the documented credential-only check, stop before evidence retrieval, and direct the user to the key page. Do not substitute another data source or render a stage-end list.
- On HTTP 401, stop further calls and report that the key was rejected. Do not render a stage-end list.
- On HTTP 402, stop further calls and report only already retrieved partial evidence. Do not estimate required credits from request size; request a credit top-up or narrower scope without presenting it as a completed-stage list.
