# Seoul bike demand — methodology and reproduction

`brief.html` is the canonical answer, covering the original assignment and all four
requested follow-up checks. Source observations and prediction streams stay in memory;
only aggregate results are saved in this ignored workspace.

## Source and population

Authorized source: `/hal-light/examples/seoul-bike-sharing-demand/question/data.csv`.
The assignment and source notes are in the same input directory. UCI metadata was
opened on 2026-11-05 UTC for definitions and units; context is saved in
`scratch/source_context.md`. Attribution: Seoul Bike Sharing Demand [Dataset]. (2020).
UCI Machine Learning Repository. DOI https://doi.org/10.24432/C5F62R; CC BY 4.0.
All empirical numbers are recomputed from the local CSV.

Parse dates as day/month/year and use the dataset clock as local Seoul time; no explicit
timezone column exists. The complete grid spans 2017-12-01–2018-11-30: 8,760 hours,
6,172,314 completed rentals, 8,465 operating hours and 295 closed hours. All closed
hours have zero counts; there are no operating zeros, duplicate keys, missing values
or negative counts. Seventeen zero-humidity readings are flagged, not silently recoded.
No deployable model uses measured target-hour weather.

Weekend means Saturday/Sunday. Operating means Functioning Day=Yes. Demand and error
tables exclude closed hours unless labelled otherwise. Means weight each operating
hour equally; historical p90 uses DuckDB continuous interpolation. Completed rentals
are not latent requests, unserved demand, station availability or concurrent bike stock.

## Instruments and artifacts

| Instrument | Purpose and output |
| --- | --- |
| `analyse/diagnostics/scratch/diagnose.py` | `diagnostics.json`, `queries.sql`: quality, totals, hourly/seasonal/day-type profiles, weather and holiday summaries. |
| `scratch/forecast_common.py` | Import-only absolute-path DuckDB reader, cutoff-aware features, estimator and metric functions. |
| `analyse/forecast-stress/scratch/forecast_stress.py` | `results.json`: forward models, sequential buffers, bootstrap, subgroup scores and Dec 1 illustration. |
| `analyse/weather-sensitivity/scratch/sensitivity.py` | `findings.json`, `queries.sql`: closer weather matching and holiday leave-one-date-out checks. |
| `scratch/closure_latency.py` | `closure_latency_results.json`: reopening comparisons, reporting delays, leakage assertions. |
| `scratch/build_report.py`, `scratch/followup_sections.py` | Current HTML assembled from aggregates with the repository shell, embedded light-mode charts and table counterparts. |
| `scratch/model.py` | Original frozen-after-August model and September buffers, retained to reproduce the reference comparison rather than the current recommendation. |

Each delegated subrun has its own detailed methodology and log. Source rows are never
copied/exported, and no source/prediction rows enter the conversation or report.

## 1. Forecast comparison

Generate forward predictions from March through November; evaluate the same 5,561
operating hours in April–November. March initializes out-of-sample residual history.
These dates have already been inspected during the assignment: this is retrospective,
exploratory comparison, not a new untouched test set.

The five candidates were fixed before computing follow-up results:

- Recent7: mean at the same hour over the preceding seven calendar days.
- Daytype28: mean at the same hour and same weekday/weekend type over the preceding 28 days.
- Weekday4: mean at the same hour on the preceding four occurrences of that weekday.
- Monthly expanding HGB: refit at each month boundary using all earlier eligible operating hours.
- Monthly rolling90 HGB: refit using eligible operating hours within the preceding 90 calendar days.

Earliest eligible fitting date is 2017-12-29. Baselines exclude closed observations;
empty cells fall back to the available previous-28-day same-hour mean. All scored
baseline predictions are finite. HGB uses `HistGradientBoostingRegressor`, default
squared-error loss, 180 iterations, 15 leaves, learning rate 0.06, L2 regularization 10,
minimum leaf size 25, early stopping disabled, random_state 42. Clip predictions at zero.
There is no hyperparameter search against the scored months.

Features: hour, weekday, month, annual sine/cosine, holiday calendar; 24/48/168-hour count
lags; preceding-seven-day same-hour mean and standard deviation; preceding-four-week
same-weekday/hour mean; preceding-day operating mean. Closed past counts are missing,
not zero demand. Features refresh at each midnight while model weights remain fixed
within the month. These are sequential daily forecasts, not a month-ahead fixed-origin forecast.

MAE=mean absolute error; RMSE=sqrt(mean squared error); WAPE=sum absolute errors/sum
rentals; signed bias=sum(predicted−observed)/sum rentals. All models use identical scored
hours. No MAPE is used. Pooled MAE: daytype28 274.0501, recent7 292.2303, weekday4 309.4293,
expanding HGB 290.3670, rolling90 HGB 299.0479. Rankings reverse across months/seasons.

On October–November's common 1,313 operating hours, expanding HGB MAE is 191.0845 versus
238.5105 when frozen after August; daytype28 is 189.1757. Its +10.7880% bias compares
with +2.4636% for expanding HGB. Stale weights explain part of the original comparison.

Paired bootstrap: sum daily paired absolute-error differences and operating-hour counts,
include closed dates as zero contributions, sample seven-consecutive-calendar-day moving
blocks, truncate to the original calendar length and recompute pooled differences.
Use 2,000 replicates, seed 42. JSON `mae_gain` means daytype28 MAE minus candidate MAE;
negative favors daytype28. The report reverses signs to state baseline advantages.
The baseline was selected on these scored dates, so intervals are conditional,
exploratory and selection-unadjusted. The expanding-model interval barely excludes zero;
no definitive superiority or production validation is claimed.

## 2. Workload buffers

For all five streams, use only earlier out-of-sample residuals, excluding closures:
fixed March residuals by time block; preceding 28 days by block; preceding 56 days by
block and weekday/weekend. The five inclusive hour blocks are 00–05, 06–09, 10–16,
17–20 and 21–23. Early 56-day windows use available history beginning March 1.

Cells require at least 30 earlier residuals; otherwise fall back to the same block,
then the broader past window. Pick sorted residual rank min(n,ceil((n+1)×0.90)),
one-indexed, clamp offset to nonnegative, and add to each point forecast. No target-day
outcome or in-sample training residual enters calibration; no recipe is tuned to force
90% on the scored months.

Coverage=mean(actual≤upper); shortfall proxy=sum(max(actual−upper,0))/sum(actual);
unused headroom=mean(max(upper−actual,0)); pinball90=mean(max(0.9×(actual−upper),
0.1×(upper−actual))). This loss asymmetry is illustrative, not measured operator cost.
These are rental-throughput proxies, not measured stockouts or idle bikes.

Daytype28 with rolling28/block gives 90.2715% coverage, 1.49227% shortfall, 380.7653
rentals/hour unused headroom and 50.8876 pinball loss, the lowest of these fixed tested
combinations. Coverage falls to 80.3763% in August, 83.9744% in September and 80.2083%
on 192 holiday hours across eight dates. The 56-day day-type split does not improve the
pooled trade-off. Dependence and drift preclude an unconditional coverage guarantee.

After reopening, buffer coverage is 91.3194% over 288 hours versus 90.2143% otherwise,
but unused headroom is 521.2408 versus 373.0928 rentals/hour. Coverage does not establish
efficient resource allocation. Block averages of hourly upper forecasts are not
quantiles of a block's total.

For the historical December 1, 2018 illustration, assume a nonholiday Saturday with
service operating. Refit models at December 1 using data through November 30, matching
the monthly policy. Daytype28 daily point total is 14,254.1429; expanding HGB is 13,793.9807.
No outcome exists in the source for scoring and no present-day forecast is implied.
JSON also contains rolling28 upper forecasts: evening offsets clamp to zero because
recent upper residuals are negative. That is a drift/overprediction artifact, not proof
of negligible uncertainty. The report's illustration shows point forecasts; buffer
performance is documented in the evaluated-period tables.

## 3. Weather and holidays

Wet means rainfall>0. Within retained common-support cells, weight exposed/reference
means by the same pooled cell count. Begin with season×hour×day type, add 5°C temperature
bins, and repeat with month instead of season. A sensitivity adds 20-percentage-point
humidity bins. Bins use floor(value/bin width), including negative temperatures.
Different specifications retain different populations; estimate differences are not
solely the effect of adding an adjustment.

Temperature-matched season cells give a −78.5796% rain association, retaining 509 wet
and 3,400 dry hours; month matching gives −80.6037%. Requiring at least three observations
per arm in each season/temperature cell gives −83.1133%, retaining 171 wet/613 dry hours.
Humidity matching gives −70.3475% on much narrower support; excluding zero-humidity
readings does not change it. Humidity can absorb weather pathways. All results are
observational; hours and distinct dates are not assumed independent experiments.

Omit each of 17 operating holiday dates and recompute each matched comparison. Publish
only aggregate ranges, medians, sign counts and support. Season-only range is −14.9218%
to +0.2172%; fixed-support range still crosses zero (−16.0416% to +0.7410%). Monthly
adjustment remains negative (−19.7363% to −9.3300%). Month+temperature+wet matching gives
full −13.7233%, leave-one-out −16.7715% to −12.2080%, retaining 372 holiday and 1,677
reference hours. Its fixed-support omissions retain just 130 holiday hours from 10 dates
and range −16.7094% to −7.3755%. These are sensitivity ranges, not confidence intervals,
causal effects or universal holiday multipliers. See the subrun methodology for the
fixed-support construction and complete variant definitions.

## 4. Closures and reporting delay

A reopening is a nonfunctioning-to-functioning transition. Recovery covers operating
hours within 24 hours of the last closed timestamp. April–November has 12 reopening
events and 288 recovery hours. Compare recovery errors to other hours matched on
season×hour×weekday/weekend, weighted to recovery counts; repeat adding wet/dry.
Daytype28 MAE is 319.7975 versus 242.7049 under calendar matching and 311.8788 versus
287.6803 after wet/dry matching (283 recovery hours retained). This does not identify
a causal closure effect or attribute the residual solely to missing history.

Latency L is extra processing delay after an observation hour ends. A count can enter
a midnight forecast only if timestamp+1 hour+L≤issue time. Test L=0,1,6,24 hours. The
prior-day mean uses only available hours and unavailable same-hour lags become missing.
Monthly training labels obey the same cutoff.

Unadapted HGB learns clean-history features but receives delay-masked scoring features;
latency-trained HGB uses delayed features in fitting and scoring. Baselines use available
counts and their ordinary past-only fallback. Under persistent 24-hour delay, lag24 and
prior-day mean are entirely missing and removed from the training matrix. Initial fitting
with all-missing columns produced `ValueError: window shape cannot be larger than input
array shape`; dropping those unusable columns resolved it without input/dependency changes.

Daytype28 MAE is 274.0501/274.2004/275.7071/278.6933 for 0/1/6/24-hour delays. Expanding
HGB moves from 290.3670 at zero to 317.4548 unadapted or 312.7254 latency-trained at 24 hours.
Shorter-delay outcomes are nonmonotonic. These are deterministic-delay scenarios, not
measurements of actual ingestion or arbitrary missing-batch behavior.

## Verification and limits

Totals independently reconcile via daily grouping. Forecast pooled errors reconcile
through monthly totals; the parent independently reproduces default expanding-model
and baseline scores. Temperature-matched rain means are rebuilt from sums/counts.
At three issue dates and four latency settings, changing all current/future outcomes
and functioning statuses leaves current-day features unchanged. Assertions verify
cutoffs and finite predictions. Independent review checked chronology, calibration,
bootstrap signs, matching, numeric claims and the completed report's coverage.

The static HTML validator passes with the intended external DOI citation warning.
Charts have legends/table counterparts and embedded light-mode styling. Earlier visual
preview attempts failed because browser access was unavailable; no screenshot QA is claimed.
The original repository check wrapper was removed by an independent cleanup during
this session. The run log records actual checks and outcomes; no repository product
changes are part of the analysis.

Still needed, explicitly documented in the report:

- Fresh current/multi-year rentals including winter to confirm the chosen model/buffer.
  No untouched confirmation period remains in this file.
- Archived weather forecasts with issue times/horizons for a deployable weather model.
- Station stock/capacity, departures/returns, trip durations and failed requests for
  concurrent fleet requirements, unmet demand and rebalancing routes.
- More holiday/event observations and closure causes/schedules for event generalization.
- Arrival/finalization timestamps and sensor metadata to verify cutoffs and zero humidity.
- Truck travel/loading times, relocation/repair workloads and productivity for crew
  counts, costs and procurement. No numeric fleet purchase is supported by this file.

## Reproduce from the repository root

Use the existing locked uv environment; no dependency changes are needed.

```sh
export UV_CACHE_DIR="$PWD/examples/seoul-bike-sharing-demand/workspace/scratch/uv-cache"
export OMP_NUM_THREADS=2
uv sync --locked
uv run examples/seoul-bike-sharing-demand/workspace/analyse/diagnostics/scratch/diagnose.py
uv run examples/seoul-bike-sharing-demand/workspace/scratch/model.py
uv run examples/seoul-bike-sharing-demand/workspace/analyse/forecast-stress/scratch/forecast_stress.py
uv run examples/seoul-bike-sharing-demand/workspace/analyse/weather-sensitivity/scratch/sensitivity.py
uv run examples/seoul-bike-sharing-demand/workspace/scratch/closure_latency.py
uv run examples/seoul-bike-sharing-demand/workspace/scratch/build_report.py
uv run .claude/skills/analyse/scripts/verify_brief.py examples/seoul-bike-sharing-demand/workspace/brief.html
```
