# Diagnostic methodology

Source: `/hal-light/examples/seoul-bike-sharing-demand/question/data.csv` (authorized user input). Source metadata and citation are maintained by the parent run. Python executes with project `uv run`, DuckDB in-memory SQL, no downloaded or exported records.

Reproduce from repository root:

```sh
UV_CACHE_DIR="$PWD/examples/seoul-bike-sharing-demand/workspace/analyse/diagnostics/scratch/uv-cache" uv run examples/seoul-bike-sharing-demand/workspace/analyse/diagnostics/scratch/diagnose.py
```

The instrument parses day/month/year dates, casts count/hour/weather numerics, derives weekend from ISO day-of-week, and treats any positive rainfall as wet. Source `Functioning Day=Yes` defines operating observations. No imputation, trimming, or removal of zero-humidity observations is applied. Quality checks use all observations; demand profiles use only operating observations unless the output key ends in `_all` or explicitly describes status/quality.

For each requested group, hours is its denominator; rentals is the sum of completed hourly rentals; mean is rentals/hours; p90 is DuckDB continuous interpolation at the 90th percentile of hourly counts. It is a retrospective marginal workload percentile, not a calibrated forecast, fleet capacity, or service availability probability. Hourly means pool the historical year and include holidays. Temporal plots of season/month have one cycle only.

Standardization: aggregate each season×hour×daytype cell (and separately each month×hour×daytype cell) into exposure/reference counts and means; retain cells with at least one observation in each group. For rain, exposure is rain>0 and reference rain=0. For holidays, exposure is Holiday and reference No Holiday. The reported standardized means weight each cell's exposure and reference mean by the same pooled n1+n0. Relative difference is 100×(standardized exposure/reference−1). Additional exposed-mix means weight reference cells by exposed counts. Both variants are descriptive associations, not experimental estimates, and neither adjusts for all other weather/supply variables. Hour-level counts overstate independent evidence when weather/holiday observations cluster by date. No causal confidence intervals are asserted.

Weather correlations are Pearson correlations with count among operating hours; they do not estimate independent effects. Coarse temperature bins are <0, [0,10), [10,20), [20,30), ≥30°C. Snow is >0 versus zero. Weather-quality ranges use all hours. Zero humidity is flagged as suspicious rather than automatically reclassified as missing.

Operational windows: 02–05, 07–09, 10–16, 17–19 include both endpoints; Other hours is the complement. Season×daytype×wet×window cells with fewer than five hours are omitted from the detailed output. Seasonal peak hour maximizes the operating hourly mean per season and day type. All eight peak-cell counts exceed five.

Verification: unique date-hour coverage, 24 observations per day, no missing fields/malformed dates/negative targets, closure-zero correspondence, and direct total independently reconciled through daily grouped sums (zero residual). `diagnostics.json` contains aggregate outputs; `queries.sql` contains aggregate SELECT statements with session views defined in the Python instrument. No brief is required for this delegated findings sub-run.
