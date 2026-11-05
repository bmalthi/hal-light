# Forecast and workload-buffer follow-up

## Reproduction and artifacts

From repository root:

```sh
UV_CACHE_DIR="$PWD/examples/seoul-bike-sharing-demand/workspace/analyse/forecast-stress/scratch/uv-cache" OMP_NUM_THREADS=2 uv run examples/seoul-bike-sharing-demand/workspace/analyse/forecast-stress/scratch/forecast_stress.py
```

The script imports the parent run's `scratch/forecast_common.py` helper. Its absolute
reader points to the authorized `examples/seoul-bike-sharing-demand/question/data.csv`.
Input observations and forecast/residual rows stay in process memory. Only aggregate
JSON and console output are persisted. `scratch/results.json` is the complete numerical
instrument; this file and `run_log.md` provide interpretation. No separate brief is required.

## Fixed comparison before execution

Five candidates: recent7 (same-hour mean over preceding seven calendar days), daytype28
(same-hour mean over preceding 28 calendar days for the same weekday/weekend category),
weekday4 (same-hour counts on the prior four occurrences of the exact weekday),
monthly-expanding histogram gradient boosting, and monthly rolling90-day boosting.
All means exclude closed hours; an empty baseline stratum falls back to a preceding
28-day same-hour mean. Weekday includes weekday holidays. Baseline definitions do not
change after the error comparison.

Boosting settings match the parent's original instrument: squared-error loss,
180 iterations, 15 leaves, learning_rate .06, L2 10, minimum leaf sample 25,
early_stopping=False, random_state=42. It uses only calendar and past rental features.
No weather readings enter these models. Features are hour, weekday, month,
annual sine/cosine, holiday, count lags 24/48/168 hours, past-seven-day same-hour
mean and SD, prior-four-week same-weekday/hour mean, and prior-day open-hour mean.
Negative predictions are clipped to zero.

For each month March–November, fit only observations dated before that month's first
day and on or after 2017-12-29. Rolling90 additionally starts no earlier than 90 days
before issue-month start. Weights stay fixed for the month while past count features
update each midnight. This assumes every previous-day count is finalized at midnight;
the parent evaluates reporting-delay sensitivities independently. These are sequential
daily forecasts, not month-ahead fixed-origin predictions.

March initializes strictly out-of-sample residual history. April–November is the common
scoring period: 5,561 operating hours. Score MAE, RMSE, WAPE=sum(abs(error))/sum(rentals),
and bias=sum(prediction-actual)/sum(rentals), pooled and per month/season/day type/block.
Spring scores include April–May only; no winter forecast score exists in this extension.
The December 1 historical scenario refits boosting at December 1 using data through
November 30, consistent with the monthly policy. It assumes operation/nonholiday
Saturday and reports block means and daily point totals. The daytype28 upper column
averages separate hourly trailing28-day residual envelopes, not a block-total quantile.
It has no known outcome and is not a present-day forecast.

## Calibration recipes

For each of all five candidate prediction streams, evaluate three recipes:

1. Fixed March residuals by hour block, never updated.
2. Previous 28 calendar days' residuals by block, recalculated daily.
3. Previous 56 calendar days' residuals by block and weekday/weekend, recalculated daily.

Blocks are inclusive hours 00–05, 06–09, 10–16, 17–20, 21–23. Residuals are actual minus
the prediction as issued at that past date, and must be dated strictly before today's
midnight issue. No in-sample training residuals or target-day outcomes are used. At the
start of April, the 56-day recipe has only March history; this warm-start limitation is
part of the evaluated rule. Cells require at least 30 residual observations; otherwise
pool to the same block across day types, then all blocks in the same window. The script
asserts that the final calibration pool has at least 30 observations. It records how
often the requested cell needed a fallback. The 56-day day-type recipe falls back for
three scored hours (0.0539%); the others never require fallback.

Choose the sorted residual at one-indexed rank min(n, ceil((n+1) × .90)); clamp the
offset to nonnegative, and add to each hourly point prediction. This empirical method
does not carry a conformal coverage guarantee under seasonality, correlated hours or
changes in fitted models. The recipes and window lengths were fixed before inspecting
their results, not optimized to make the observed coverage exactly 90%.

Coverage = fraction actual ≤ envelope. Shortfall proxy = sum(max(actual−envelope,0)) /
sum(actual). Unused headroom = mean(max(envelope−actual,0)). Pinball90 = mean of
max(.90 × (actual−envelope), .10 × (envelope−actual)). These are hourly rental-throughput
metrics, not fleet stock, lost customer requests or customer bike-availability scores.

Post-reopening sensitivity defines recovery hours as operating observations with
0 < current timestamp − most recent closed timestamp <=24 hours. Daytype28/rolling28
coverage is91.32% over288 recovery hours and90.21% over5273 other hours; unused headroom
521.24 versus373.09/hour. These are descriptive slices; closure attribution requires
schedule/cause records and an appropriate causal comparison.

## Uncertainty and verification

The best simple baseline by pooled MAE is identified retrospectively as daytype28.
For each other candidate, resample daily paired error differences and denominators
in seven-calendar-day moving blocks for 2,000 replicates; seed 42. Closed days have
zero numerator/denominator contributions. The result's `mae_gain` means reference
daytype28 MAE minus candidate MAE: negative favors daytype28. These percentile intervals
are conditional, selection-unadjusted, and based on an already explored file. They
must not be read as fresh confirmatory model-superiority evidence.

Pooled MAE independently rebuilt from month-level absolute errors agrees to floating-point
precision for every candidate. Assertions check complete hourly source chronology,
finite predictions, and strictly past residual pools. All candidate and envelope scores
use the same 5,561 operating hours. No source or prediction rows are saved.

## Findings and additional-data needs

Daytype28 gives MAE274.05, versus recent7 292.23, expanding HGB290.37, rolling90 HGB299.05,
and weekday4 309.43. It improves morning MAE from recent7's380.08 to255.94. It wins only
3 of8 months; recent7 also wins3, expanding HGB2. Expanding HGB wins spring (April–May)
MAE331.21 against daytype28 353.42. Thus a day-type-aware simple benchmark is provisionally
useful, with model performance varying across seasonal transitions.

October–November MAE is daytype28 189.18 and monthly-expanding HGB191.08, compared with
the original frozen model238.51. The updated HGB has lower Oct–Nov bias (+2.46%) and
RMSE320.01 than daytype28 (+10.79%,330.98), exposing a cost/bias trade-off despite
daytype28's lower MAE. These retrospective comparisons do not establish deployment superiority.

Daytype28 + trailing28/block buffer gives the lowest pooled pinball90 among fixed recipes:
50.89, coverage90.27%, shortfall1.49%, unused380.77/hour. Its own fixed-March buffer has
pinball57.25, coverage88.89%, shortfall1.86%, unused412.82. Adding a 56-day/day-type residual
split gives pinball55.26 and does not improve the pooled trade-off. However, daytype28's
rolling28 coverage varies from80.38% in August to96.91% in November; holidays80.21%
(192 hours), weekends88.94%, wet hours99.78% with unused1,178.48/hour. Near-90% pooled
coverage masks seasonal/event weakness and rainy-day excess capacity.

Still needed: fresh current/multi-year rental data for confirmation and winter coverage;
archived weather forecasts as issued for deployable weather adjustment; more holiday
dates and event calendars for sparse special-day behavior; actual data-latency records;
station inventory, trip durations, returns, unserved requests and staffing productivity
for fleet and service-level planning. No parameter refinement on these already examined
dates can substitute for those missing inputs.

For the historical December1 illustration, trailing28 evening/late-night residual
90th percentiles are negative and the prespecified nonnegative-offset rule makes the
upper equal the point forecast in those blocks. This is a consequence of November's
declining demand and the empirical rule; it does not establish negligible uncertainty
or reliable winter coverage.
