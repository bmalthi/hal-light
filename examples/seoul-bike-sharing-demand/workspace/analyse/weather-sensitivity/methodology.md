# Weather and holiday robustness

The source is the authorized local CSV at
`/hal-light/examples/seoul-bike-sharing-demand/question/data.csv`.
All calculations use in-memory DuckDB temporary views and output aggregates only.
No rows, date-specific holiday findings, extracts or raw predictions are saved.

Run from the repository root:

```sh
UV_CACHE_DIR="$PWD/examples/seoul-bike-sharing-demand/workspace/analyse/weather-sensitivity/scratch/uv-cache" uv run examples/seoul-bike-sharing-demand/workspace/analyse/weather-sensitivity/scratch/sensitivity.py
```

`scratch/sensitivity.py` is the executable instrument; `scratch/queries.sql` records
the queries (holiday omission dates are bound in memory by the script).
`scratch/findings.json` contains all aggregate results and support counts.

## Population and matching

Keep only Functioning Day = Yes. Parse date with day/month/year, weekends as Saturday
or Sunday, wet as rainfall > 0. The file supplies season labels. Temperature bands
are floor(temperature / 5), so bins include −5 to <0°C and 0 to <5°C rather than
using truncation toward zero. Humidity bands are floor(humidity / 20).

Each comparison creates calendar cells defined in the JSON `axes` field. For each
cell compute exposed and reference count and mean. Require at least one observation
in each arm, or at least three for the specified sparse-support sensitivity. Weight
both means by the same pooled cell count (n_exposed+n_reference), sum and divide by
the sum of those pooled counts. The reported relative difference is
100 × (standardized exposed mean / standardized reference mean − 1).

An additional exposed-mix estimate weights each arm by exposed counts. Support counts,
retained percentages and distinct dates refer to the actual retained matched sample.
Distinct dates are descriptive counts; adjacent dates and observations within a date
need not be independent. The comparisons do not isolate causal effects. Adding humidity
changes both conditional question and retained support and can absorb weather pathways;
it is a sensitivity, not an unambiguously better adjustment.

Rain variants: season/hour/weekend; add temperature5; replace season by month; apply
minimum-three-per-arm to both temperature variants; add humidity20 to the season-based
temperature variant; and exclude zero-humidity records from that final comparison.
The minimum-three month variant retains only 9.1% of wet hours, so its estimate is a
narrow-support stress test and cannot replace the broad comparison.

## Holiday leave-one-date-out

Holiday variants: season/hour/weekend; month/hour/weekend; add temperature5 and wet/dry
status to both. Each operating holiday date is omitted in turn and the entire matched
comparison recomputed. Only min/median/max, sign counts and support ranges across all
17 omissions are published. Ranges are sensitivity ranges, not confidence intervals.

To distinguish loss of cells from within-cell influence, a fixed-support variant
first keeps cells with at least two holiday observations and at least one nonholiday
observation. Because each date contributes at most one observation to each exact-hour
cell, these cells remain represented after removing any one holiday date. This fixes
the set of cells, but pooled weights and means still change when a date is omitted.
These fixed-support subsets differ from the full population: notably the monthly
weather-matched version retains only 130 holiday hours from 10 dates. Report its
support limits, not just the tighter sign range.

## Findings and interpretation

- Matching temperature within season/hour/weekend cells gives 200.98 wet versus
  938.28 dry rentals/hour, a −78.58% difference. It retains 509/516 wet hours across
  all 100 wet dates and 3,400/7,949 dry hours across 332 dates. Month matching gives
  −80.60%, retaining 458 wet and 1,882 dry hours. Temperature differences do not
  explain away the strong negative rain association in the retained sample.
- Adding humidity yields −70.35% but retains only 365 wet and 735 dry hours. Excluding
  all zero-humidity readings leaves these matched hours and the estimate unchanged.
  Finer adjustment narrows support; it does not justify a universal rain multiplier.
- Holiday estimates are −7.33% with season matching, −13.31% with month matching,
  −12.02% with season+weather matching, and −13.72% with month+weather matching.
- Seasonal holiday leave-one-out ranges from −14.92% to +0.22% (16/17 negative).
  On a fixed set of seasonal support cells it still ranges from −16.04% to +0.74%,
  showing the sign fragility is not solely caused by cells disappearing.
- Monthly holiday leave-one-out remains negative, −19.74% to −9.33%. Monthly weather
  matching also remains negative, −16.77% to −12.21%, on variable matched support;
  fixed-support sensitivity ranges −16.71% to −7.38% on its smaller subset. This
  supports caution about the size and universality of holiday adjustments, rather
  than interpreting the initial −7.3% as a stable operational discount.

## Verification and additional data

The original season-only rain and holiday standardized estimates reproduce to floating
point precision. An independent sum/count path reconstructs the temperature-matched
rain means; assertions match within 1e-9. All 17 holiday omissions are runnable for
each specification. No model selection or future prediction is implied by this
descriptive analysis.

Need more data for stronger operational claims: multiple years and event-specific
holiday information; actual forecast weather archived at issue time; station inventory,
trip duration/origin–destination flows and unsuccessful rental attempts; and sensor
metadata to interpret zero-humidity values. Completed rentals can be constrained by
availability, and this file cannot identify the lost demand. These missing inputs
remain necessary even though temperature matching and holiday sensitivities are now run.
