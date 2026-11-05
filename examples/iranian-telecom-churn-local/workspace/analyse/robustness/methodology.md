# Repeated scorecard and active-policy robustness

This is a summary-only sub-run of the parent Iranian telecom churn analysis. Its output is the closing summary in `run_log.md`, with machine-readable aggregate results in `scratch/`. It performs no calibration or intervention-effect estimation.

## Source and population

The source is `/hal-light/examples/iranian-telecom-churn-local/question/data.csv`, opened by `read_csv_auto` in an in-memory DuckDB connection. The field aliases and order match the explicitly authorized parent `scratch/model.py`: `failures, complaint, tenure, charge, seconds, calls, sms, distinct_calls, age_group, tariff, status, age, value`, with `churn` the label. All row-level computations occur inside temporary DuckDB tables. Returned/saved data are aggregates only.

The full variant retains every source record. The dedup variant applies `SELECT DISTINCT` to all 13 predictors plus `churn`; profiles with different labels are therefore not discarded. Full data contain 3,150 records and 495 churn labels, versus 2,850 and 446 after exact-row deduplication. This changes record weights; it does not establish that the removed rows are duplicate customers. Active targeting includes `status=1` only: 2,368 records / 125 churn labels in full data, 2,166 / 121 in dedup data.

## Split, fit and select

For each integer seed 20261105 through 20261134 inclusive, compute DuckDB `hash(failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value,seed)%100`. Values below 60 are training, 60–79 validation, and 80–99 test. Hashing uses predictor values, not row position or label. Both variants execute the identical expression, so an identical predictor profile has the same split in both. The source's exact predictor profiles stay wholly within one partition. The DuckDB version is recorded in `scratch/summary.json`; reproduce with the locked project environment.

Within each variant and seed, compute the median of strictly positive training `seconds`. Usage has three categories: zero; positive through that median inclusive; above the median. Training prevalence is the prior. Each candidate cell predicts `(training_events + 20 × training_prevalence)/(training_n + 20)`, with unseen cells assigned the training prevalence. Candidates, in original order, are complaint; complaint × usage; complaint × usage × status.

Select the candidate with the greatest validation expected precision at `floor(0.20 × validation_n)`. At any tied score boundary, selection is uniform among all members of the tied score group. The exact expected event count is the sum of events in wholly selected groups plus `remaining_slots × boundary_events / boundary_n`. Python `Fraction` preserves this rational expected precision for selection; no random tie sample is used. AUC breaks an exact precision tie; the original candidate order breaks a remaining exact tie. The complaint × usage × status candidate won all 60 selections. No test metric is used for model selection. The no-status scorecard is also evaluated as an auxiliary sensitivity.

## Metrics and policies

Test scorecard metrics include AUC, Brier, mean predicted probability, and the expected precision, recall and value recall of the 20% campaign. AUC is computed from risk-group event/non-event counts, giving tied event/non-event pairs half credit. Brier is the average squared difference between risk and label. Precision divides expected selected churn labels by contacts; recall divides them by test churn labels; value recall divides expected selected `value × churn` by all `value × churn` in the relevant evaluation population. `Customer Value` is an observed dataset variable; value recall is not revenue saved or a causal benefit.

The active analysis filters the selected model's test population to `status=1` and defines one shared capacity, `floor(0.20 × active_test_n)`. It uses active-only prevalence, churn and churn-value denominators. The four equal-budget policies are:

1. Complaint-first: complaint descending, with uniform tie selection; if complaints do not fill capacity, fill from non-complainers uniformly.
2. Low seconds: `seconds` ascending, with uniform ties.
3. Scorecard: the selected scorecard's risk descending, with uniform ties.
4. Complaint-first then low seconds: lexicographically complaint descending and seconds ascending, with uniform ties on both values.

The active random-contact baseline has expected precision equal to active test prevalence and expected recall/value recall equal to capacity divided by active test size. The service-only policy contacts active complainants only and never fills unused capacity. It is capped at the same active capacity with uniform selection among complainants if needed; no evaluated split required capping. The uncapped cohort's size, observed churn fraction, fraction contacted, recall and value recall are retained separately.

Thirty split metrics are summarized with arithmetic mean, median, minimum, maximum and linearly interpolated p10/p90 (`numpy.quantile` defaults). They describe variation across overlapping repeated holdouts, not independent observations or confidence intervals. Policy differences compare the same seed and data variant. Dedup-minus-full differences also pair by seed. Differences compare predictive capture and error; they are not treatment effects.

## Reproduction and verification

Run from the repository root:

```sh
UV_CACHE_DIR=examples/iranian-telecom-churn-local/workspace/analyse/robustness/scratch/uv-cache uv run examples/iranian-telecom-churn-local/workspace/analyse/robustness/scratch/repeat_policy.py
```

`scratch/repeat_policy.py` is the saved instrument; it writes every executed query to `scratch/repeat_policy_queries.sql` before execution. Outputs are `scratch/per_split_metrics.json` (60 records), `scratch/summary.json` (distribution summaries, paired policy comparisons, input checks and design), and `scratch/paired_dedup_minus_full.json` (30 paired records). No raw-record extract or persistent database is created.

Assertions verify source totals against independent complaint/status grouping; split totals against source totals; absence of profile leakage; fitted counts/events and smoothing algebra; Brier via grouped and direct SQL; and overall/active scorecard capture using independent row-rank and tie-count windows aggregated by status. Counts reconcile exactly and floating sums reconcile within 1e-8. Final JSON validation verifies 30 results per variant and equal active capacities. The parent independently reproduced the full-data scorecard precision, recall, AUC and Brier, agreeing to reported numerical precision.

The recommendation flip test is the same-seed active comparison. Complaint-first then low seconds improves precision and recall versus the scorecard in all 60 variant/split evaluations, while its value-recall advantage is not universal. Deduplication preserves that ordering. Prospective testing is required to learn whether service or offers reduce churn; this dataset evaluates prioritization against observed labels only.
