# Traffic Observation Field Semantics

Load this file after retrieving `product-traffic-terms`, `competitor-product-keywords`, `product-traffic-terms-timeline`, or `product-traffic-terms-profile`. It owns the meaning and inference limits of their returned traffic, placement, coverage, timeline, and aggregate-profile fields.

## Traffic-term rows

- `trafficShare` is the row's sampled share within the returned ASIN traffic period, not exact Amazon share of voice.
- `estimateImpressionPoint` and the ORG/SP/SB/SBV/SPR fields describe observed placement exposure. They do not establish clicks, conversion, sales attribution, or profitability.
- When the shared ranked-detail protocol verifies `sortBy`, `sortOrder`, page, page size, filters, identity, and period, returned traffic-term rows may be described as Top N by that exact field and direction. `Top N by trafficShare descending` ranks the endpoint's sampled row-level traffic share only; it is not a generic Top N keyword-value or conversion claim.
- A sponsored-only row or one selected page of returned rows does not establish overall advertising dependence, weak organic relevance, algorithmic recognition, or organic improvement potential.
- `daysCoverageRate`, `observationCount`, and returned period boundaries describe observation support. Low coverage limits confidence rather than proving instability; do not call coverage full, complete, or stable unless those fields and the resolved period directly establish it.

## Timeline observations

- `asinSnapshot` is tied to the series date. Traffic, placement, and `adActivity` belong to the returned weekly period. `keywordMetrics` belongs to its own weekly `metricWindow`; do not merge these grains into one timestamp.
- `keywordEstimateSearchCount` and `keywordAbaRank` are keyword-level context scoped to `keywordMetrics.metricWindow`; they do not describe ASIN-level traffic, placement, clicks, conversion, or sales attribution.
- Exposure-position fields under `placement` return `null` both when period data is unavailable and when no position was observed. A null position cannot distinguish those states by itself: use returned period boundaries plus observation and coverage fields, and never coerce the position to numeric zero.
- Compare like fields across aligned returned periods. One observation supports only a point-in-time description; at least two comparable observations are required to describe directional movement.
- `adActivity` counts and coverage describe observed ad participation. They do not establish CPC, auction competition, spend posture, ROI, or campaign intent.
- Product, demand, placement, traffic, and ad-activity changes are observations. Time-aligned co-movement can narrow an explanation but does not establish causality by itself.
- An ASIN appearing only in sponsored placements is a placement-posture observation, not proof of weak organic relevance or conversion.

## Aggregate traffic-term profile

- `productTrafficTermsProfile` is a server-calculated metric object for the item identity and returned data window. Preserve each returned module, channel key, field name, value, and period scope.
- `status=empty`, a null profile, or an omitted/nullable module field is a coverage boundary. It does not establish low traffic, zero exposure, stability, or absence of change.
- In the profile's previous-period count, share, and impression-point fields, `null` means the previous weekly data is unavailable. Numeric `0` means that weekly period exists but the relevant signal was not observed. This rule does not apply to exposure-position fields, whose null value covers both unavailable data and no observation. Never coerce `null` to zero, relabel zero as missing data, or calculate a comparison across an unavailable previous period.
- Compare current and previous evidence only when the profile explicitly returns compatible values and both period scopes. Do not infer a missing previous window from weekly cadence.
- When `dataWindow.previousPeriod` is null, empty `newTerms`, `lostTerms`, `top10Gainers`, or `top10Losers` arrays carry no zero-change conclusion. When the previous period exists, interpret a returned zero count as no observation for that field within the endpoint's resolved scope, not proof of global absence outside that scope.
- Do not project retired flat overview fields, channel lists, `*Prev` values, or entry/exit arrays onto the profile. Do not reconstruct a missing profile from traffic-term rows.
- Report per-keyword new/lost/gainer/loser detail only from a non-empty returned profile array and preserve its actual item fields. Do not infer an array-item schema from an empty array or turn a returned driver list into causal proof.

## Cross-source limits

- Search demand falling across multiple comparable weekly points is a demand-trend concern only for that returned window.
- Timeline evidence owns ASIN × keyword movement observations; profile evidence owns its returned ASIN-wide aggregate dimensions and compatible period comparisons. Neither substitutes for keyword-level traffic-term rows.
- Keep all traffic observations below seller-funnel and Ads evidence authority defined in `execution-guide.md`.
