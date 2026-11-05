# Diagnostics methodology

The sole empirical source is `/hal-light/examples/iranian-telecom-churn-local/question/data.csv`. Parent-supplied `/hal-light/examples/iranian-telecom-churn-local/workspace/scratch/source_context.md` supplies encodings and timing paraphrased from UCI (retrieved 2026-11-05 UTC): first-nine-month predictors, month-12 churn; Status 1 active / 2 non-active; Tariff 1 pay as you go / 2 contractual. Those notes supply interpretation only, not computed findings. No domain KB is configured.

The population is all 3,150 input records. Churn rate is `sum(Churn)/count(*)`; there are no weights or exclusion filters. The CSV has 14 columns and no missing values. No identifier is supplied, so records cannot be verified as distinct customers. Preserve source rows for primary prevalence; exact-row deduplication is a sensitivity check rather than an assumed correction.

`scratch/diagnostics.py` is the saved instrument. It reads the absolute CSV path into a DuckDB temporary view, normalizes column aliases in the query, and computes only aggregate results. Full-row and feature-only SQL groupings count duplicate excess rows and conflicting-label profiles; grouped values are not returned or saved. No raw records enter the conversation, scripts' output, or files. `scratch/schema.py` is the schema-only discovery instrument.

Every categorical variable is grouped on its supplied code. Numeric variables use full-sample 25th, 50th and 75th percentiles with right-closed intervals; tied boundaries are collapsed, so some fields have fewer than four bins. Labels round thresholds for display, while the saved `profile` numbers and SQL predicates use exact numeric thresholds. `quantile_rates` contains the full-population rates. `status_stratified` repeats each comparison inside recorded status; `complaint_status_stratified` adds complaint to failure, call-seconds, call-frequency, SMS and value comparisons. Status-by-tariff and status-by-age tables address sample composition. No models are fit, and these conditional comparisons do not establish causation.

For context about exposure, `failure_relative_bin` divides failure count by call frequency where frequency is positive, and separates zero-call records. This is an exploratory ratio rather than a documented failed-call probability: failures exceed call frequency in three records. The ratio's bands are 0, >0–5%, >5–15%, >15%, with no calls separately. No correction is applied.

`profile` records missingness, distinct count, ranges, quartiles, mean and sample standard deviation. `value_correlations` contains Pearson correlations with observed usage, age and ordinal charge. Customer Value is an index with unspecified monetary units; its 0.9249 correlation with SMS means it should not be described as independent spending evidence. Age and Age Group are perfectly redundant categories in this file. Charge Amount code 10 occurs in seven rows, beyond the documented 0–9 range; retain and flag rather than invent a recode.

The rival framing was that non-active status explains marginal complaint/usage/failure associations. The status-stratified results retain the complaint association, but show heterogeneous usage and failure relationships. The follow-up activity cut finds no observed churn in the highest call-seconds quartile, including 22 complainants. This limits blanket interpretations of the complaint marker and highlights support limitations; it does not establish a zero future churn probability. Duplicate removal leaves the complaint/status association materially intact. No action effect or causal intervention recommendation is claimed.

`scratch/aggregates.json` contains the aggregate results for the parent. Outcome counts and rates in strata with fewer than ten records are null. All headline rates can be rebuilt from the stored numerators and denominators. Programmatic checks reconcile status totals, status-by-complaint totals and every numeric-bin table to 3,150 records / 495 churns, with zero residual. Total churn is also 446/2,850 = 15.6491% in distinct full rows, versus 15.7143% in all records.

Reproduce from repository root:

```sh
UV_CACHE_DIR=examples/iranian-telecom-churn-local/workspace/analyse/diagnostics/scratch/uv-cache PYTHONDONTWRITEBYTECODE=1 uv run --no-sync examples/iranian-telecom-churn-local/workspace/analyse/diagnostics/scratch/diagnostics.py
```

This summary-only sub-run produces no brief, charts or fitted models. Its closing findings are in `run_log.md`; the parent is responsible for combining them with independent model/evaluation results.
