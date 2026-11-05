# Iranian Telecom Churn — methodology

The canonical answer is `brief.html`. Supporting files are `prompt.md`, `run_log.md`, the aggregate analysis and build scripts in `scratch/`, and the delegated diagnostics summary under `analyse/diagnostics/`. No source, repository or skill files were edited. No individual customer record or prediction extract was saved.

## Source and scope

Empirical input: `/hal-light/examples/iranian-telecom-churn-local/question/data.csv`. All 3,150 records are retained, with 495 churn labels. `question/BRIEF.md` defines the assignment; `question/SOURCE.txt` supplies provenance, not numerical evidence. The canonical UCI page was opened on 2026-11-05 UTC: https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset. Citation: Iranian Churn [Dataset] (2020), DOI 10.24432/C5JW3Z, CC BY 4.0. Its timing and encoding metadata are paraphrased in `scratch/source_context.md`.

The source describes nine months of predictors and churn at month 12. The local file supplies neither customer identifiers nor calendar timestamps, treatment assignments, intervention costs, reachability, verified revenue nor future contribution margin. This is a historical predictive exercise, not a causal retention estimate. The copied SOURCE.txt's Seoul-date sentence is unrelated and was not applied.

## Diagnostics

`analyse/diagnostics/scratch/diagnostics.py` reads the absolute input path with DuckDB and writes only aggregates to `aggregates.json`. It profiles every column, missingness, ranges, duplicate records, conflicting-label profiles, categorical rates, numeric quartile rates, status stratification and selected status-by-complaint stratification. Churn rate is sum of the label divided by row count. Numeric descriptive cutoffs use the full sample; tied quartiles collapse. Display labels round value cutoffs, while predicates use exact values. The scorecard does not use these full-sample diagnostic cutoffs.

There are no missing values; 300 excess exact duplicates, 2,836 distinct predictor profiles, and 14 predictor profiles with conflicting labels spanning 64 records. Primary estimates retain rows because no ID identifies the correct deduplication unit. Deduplication is a sensitivity only: 446/2,850 distinct full rows churn (15.649%). Status/complaint associations persist. Status totals, status-by-complaint totals and all numeric partitions reconcile to 3,150 records / 495 churners with zero residual.

Call failures divided by call frequency is exploratory exposure normalization, not a documented network failure probability. Three records have failures exceeding calls. Age has only five codes and is redundant with Age Group. Charge contains code 10 despite the documented 0–9 range. Customer Value is a calculated index with unspecified units; do not interpret it as money. Detailed diagnostic instruments and methodology are in the sub-run folder.

## Scorecard and split

`scratch/model.py` contains the complete saved modeling instrument; `model_queries.sql` records all executed SQL. Source rows stay inside an in-memory DuckDB connection. Python receives only cell counts and aggregated evaluation results. No row extract was needed or produced. `model_results.json` holds the resulting aggregates.

Use DuckDB 1.5.4's built-in `hash` over all 13 predictor values (excluding Churn), with seed argument 20261104 for split assignment. Hash modulo 100 below 60 selects training, 60–79 validation, and 80–99 test. The profile hash, without seed, identifies matching predictor profiles for overlap checks. These are ordinary deterministic partitions, not security or integrity hashes. DuckDB's hash may change across versions, so the recorded environment/version matters. No feature profile crosses splits. Counts are 1,888 / 609 / 653, containing 300 / 91 / 104 churners. Profile counts sum to 2,836. Row weights are retained, so evaluation is record-weighted rather than equal-weighted by profile. Lack of customer IDs still prevents confirming independence.

Three candidates were fixed before validation: complaint; complaint × usage; complaint × usage × status. Usage is zero, positive through 3,100 seconds, or above 3,100 seconds. The threshold is the median positive usage in training only. A cell with n records and k churners scores `(k + 20 * p_train) / (n + 20)`, where `p_train=300/1888`; smoothing strength 20 is fixed rather than tuned. Unseen combinations use the global training prevalence. All twelve three-feature combinations exist in training, although some are small. The fitted probabilities are descriptive estimates and are not recalibrated on test.

Select maximum validation precision at floor(20% × validation n), with validation AUC breaking any tie. Tie order for contacts is built-in `hash(profile,19)`, then input row position; neither uses outcomes. Complaint × usage × status wins: precision 50.41%, against 44.63% for complaint × usage and 34.71% for complaint only. No refit on validation occurs: the published scorecard is the same training-only model evaluated on test.

ROC AUC and average precision use distinct-score aggregate positive/negative counts as sample weights in scikit-learn 1.9.0; this reproduces record-level metrics without exporting records. Brier score is SQL average squared prediction error. Test AUC is .907016, AP .632182, Brier .079194. Calibration tables compare mean risk with observed churn by fixed bands. Test prevalence is 15.926%; mean prediction is 13.884%. The selected tail also underpredicts risk, so the score is a ranking aid rather than a calibrated economic probability.

## Campaign evaluation and policy

Assumed contact capacity is 20% because no cash budget is specified. For n evaluated records, k=floor(budget × n). Sensitivities are 5%, 10%, 20%, 30%. Precision=selected churners/k; recall=selected churners/all churners; prediction lift=precision/population churn prevalence; false positives=selected observed non-churners. These outcomes are historical, not verified untreated potential outcomes. Captured churners are not saved customers.

At k=130, TP=77, FP=53, FN=27, TN=496. Independent status grouping reconstructs 14 active and 116 non-active contacts, with 14+63=77 detected churners. Direct and grouped all-source prevalence also reconcile. Outcome-blind tie seeds 0–19 produce 70–77 detections. Exact expected detections from uniform random selection within the marginal score cell are 74.2727, calculated from cell n, events and remaining slots. The 95% Wilson precision interval in `derived_metrics.json` is nominal and assumes independent observations; it is not cluster- or selection-adjusted. It is not a future performance guarantee.

Policy comparisons at identical 130-contact capacity rank risk; complaints then tie-break; risk × value; or value alone. Value recall is sum(selected value × churn)/sum(all value × churn). Multiplying risk by value is only an exploratory surrogate: it does not incorporate intervention effect, future margin or costs. The 20%-of-all active-only policies retain a 130-slot capacity (26.4% of 493 active records); their stored all-population recall/lift denominators must not be confused with active-population metrics. The separately reported active-only 20% analysis uses 98 contacts, 29 active churners and a 5.882% baseline. It detects 21 churners, precision 21.429%, recall 72.414%, and lift 3.643.

Rival framing: the status-free scorecard still has AUC .855743 and detects 66 churners at 130 contacts. A conventional row split is a sensitivity, not a replacement model or a temporal test: it re-estimates its own training prior and positive-usage median but uses the selected feature set. It yields AUC .883574 and precision 48.0%, with 69 test feature profiles shared with training. Different held-out populations mean this contrast does not isolate the magnitude of duplicate leakage.

The flip test compares risk, risk × value and active eligibility. The heavy inactive concentration reverses any indiscriminate discount recommendation. The memo proposes enhanced-service testing for active complainants, with 22 historical test candidates (17 churners / 5 non-churners). No blanket offers: active non-complaint cells are structurally below the exploratory 20% risk threshold. The offer experiment is a proposed subsequent design, not a test-selected proven optimal policy: active complainants with value at least the training median 222.815 receive random assignment to service-only or service-plus-offer after margin and eligibility verification. Seven historical test records meet that index threshold; no effect is estimated. No individual contact list is produced.

The memo specifies two randomized comparisons, intention-to-treat churn and net-margin effects, confidence intervals, operational eligibility, stratification and a later validation cohort. `scratch/build_brief.py` calculates an illustrative normal-approximation sample size: equal groups, control risk .60, treatment risk .50, 80% power, two-sided alpha .025 per comparison, giving 470 per arm. These are explicit planning assumptions, not effects inferred from the dataset. Real power must reflect the actual cohort and economically relevant effect.

## Reproduction

Use the existing project-local environment (Python 3.13.13 in this run, compatible with the project's 3.12+ requirement). All Python uses uv. From repository root:

```sh
export UV_CACHE_DIR="$PWD/examples/iranian-telecom-churn-local/workspace/scratch/uv-cache"
export PYTHONDONTWRITEBYTECODE=1
uv run --no-sync examples/iranian-telecom-churn-local/workspace/analyse/diagnostics/scratch/diagnostics.py
uv run --no-sync examples/iranian-telecom-churn-local/workspace/scratch/model.py
uv run --no-sync examples/iranian-telecom-churn-local/workspace/scratch/build_brief.py
uv run --no-sync .claude/skills/analyse/scripts/verify_brief.py examples/iranian-telecom-churn-local/workspace/brief.html
```

The builder uses the repository brief shell and its CSS, creates chart_specs.json, renders the inline SVG pinned to light with the bundled renderer, writes derived_metrics.json and assembles brief.html. Chart data also appears in a table. All output is inside this run; caches are directed to scratch. No raw input copy or record-level output exists to delete.

## Verification

Aggregate sum checks, profile-split disjointness, headline reconstruction, status-free comparison, row-split sensitivity, eligibility/value comparisons and tie sensitivity passed. Independent review found no arithmetic or split-leakage error and its policy/denominator concerns are addressed explicitly. Brief lint passed with one intended citation-link warning. The single-blue chart palette passed all applicable validator checks. Native Safari visual checks confirmed readable opening content, chart and policy table without clipping; its initial launch stalled but the subsequent local preview succeeded.

The required `uv run tools/check.py` passed Ruff lint and formatting, then failed importing tests because the pre-existing `examples/charts.json` deletion leaves that required fixture missing. The pre-existing `examples/demo.py` deletion would also prevent the demo stage. Neither unrelated deletion was restored. No product code changed; this is a repository baseline limitation, not a passing full test suite.

## Requested robustness extension — 2026-11-05

The follow-up explicitly authorizes checks 1–4 proposed in conversation: repeated grouped splits, regularized/shallow-tree model comparisons, calibration plus exact-row-deduplicated modeling, and active-policy comparisons. The existing frozen holdout remains a reproducible worked example in the memo; the repeated results carry the stability and comparative conclusions. This is internal robustness on previously explored data, not a new external validation. The three unavailable operational checks are presented in the memo with the required missing fields and why they matter.

### Fixed design and local compute

Use 30 fixed split seeds, integers 20261105–20261134 inclusive, in the original `hash(all 13 predictors, seed)%100` expression, with <60 training, 60–79 validation, >=80 test. All exact predictor profiles share a partition, even when their labels conflict. Full-data and exact-row-deduplicated pipelines use identical mappings. Exact deduplication includes every source column including the outcome, preserving contradictory outcomes within the same predictor group. This changes both training and test weighting; the paired difference is a duplicate sensitivity, not a pure training-data intervention.

Each model uses the same train/validation/test records within each source variant and seed. Settings are selected with validation expected precision at a 20% cap, with AUC breaking ties. There is no test-set tuning, no refit using test labels, no class rebalancing, no synthetic oversampling. Model-family comparisons are prespecified internal comparisons; a production model is not declared validated merely because one wins these tests.

`scratch/extended_models.py` reads the authorized CSV through DuckDB into transient local arrays. The explicit follow-up accepts the proposed continuous-feature modeling work, for which coarse scorecard aggregates would discard the joint distribution under test. Source columns, outcome, value for evaluation and profile group keys remain only in process memory. No row-level file, per-customer probability list, serialized model/training rows or contact list is saved or printed. Age and age group are used only in the original profile grouping, not model fitting. Only aggregate metrics and settings persist. This differs from the original SQL-only scorecard computation and is confined to this requested extension.

### Five model families

1. Scorecard: original three candidates (complaint; complaint × binned usage; complaint × binned usage × status), fixed smoothing of 20 training-prevalence pseudo-observations, training-only median positive seconds. All 60 full/dedup selections choose the three-feature candidate.
2. Core regularized logistic: complaint, non-active flag, and log1p(seconds). StandardScaler fits on training only; L2 regularization C selected from .01, .1, 1, 10, solver lbfgs, maximum 2,000 iterations.
3. Core shallow tree: complaint, non-active flag, raw seconds; depths 2,3,4,5 and minimum leaf sizes 20,50, fixed random state 901.
4. Expanded regularized logistic: core inputs plus failures, tenure, charge, call frequency, SMS, distinct called numbers and contractual-tariff flag. The seconds/failure/call/SMS/distinct counts use log1p; remaining numerical columns are used directly; all are scaled using training statistics only. Same C grid.
5. Expanded shallow tree: the same ten inputs, with raw counts and the same depth/leaf grid.

Neither age nor the undefined Customer Value index enters prediction fitting. Value is retained only as an evaluation weight, so value capture is not money, and excludes any asserted intervention effect. Unexpected charge code 10 is used as the observed ordinal value in expanded models; the data-quality caveat remains. Core comparisons separate model-form improvement from the addition of behavioral features.

### Expected campaign metrics and active policies

All repeated comparisons use exact expected contacts under uniform random tie-breaking at the capacity boundary. For ordered prediction groups, include preceding groups fully, the marginal group at fraction `(k−preceding_n)/marginal_n`, and later groups with zero weight. The resulting weighted outcomes/values provide expected detections, precision, recall and index-value capture; fractional detections are expectations, not fractional actual customers. Capacity is floor(.2 × evaluation-population n). This removes arbitrary tie-seed effects. The original frozen illustration still uses its stated integer seed19 contacts and separately reports tie sensitivity.

AUC, AP, Brier, signed probability bias and campaign metrics are calculated separately for all test records and for active test records. Active results use active prevalence and active churn/value denominators and a 20%-of-active contact cap, not the all-population cap. Expanded models and calibrators are still fitted/tuned on all accounts; active-only model training is not claimed.

The independent aggregate-SQL sub-run `analyse/robustness/scratch/repeat_policy.py` repeats scorecard selection and evaluation plus active policies: complaint-first then random, low seconds ascending, scorecard, complaint-first then low seconds. All use the same active cap and exact tie expectation. It also evaluates contacting only active complainants, without filling unused capacity; that policy never reaches the cap. Its high precision cannot be compared as an equal-volume result against the full-cap rules.

The SQL sub-run produces `summary.json`, `per_split_metrics.json`, `paired_dedup_minus_full.json` and `repeat_policy_queries.sql`. Independently computed parent and sub-run scorecard means agree to better than 1e-10 for full/active precision, recall and value recall. Count, subset, budget, capture and scorecard formula checks also pass. The deduplicated sample loses 300 records and 49 churn labels overall; among active records it loses 202 records but only four churn labels, changing the active baseline. This helps explain higher active precision after deduplication without implying more predictive information.

### Calibration

For each selected model in each seed/source variant, fit logistic regression of the validation outcome on logit(raw probability), clipping raw probabilities to [1e-6,1−1e-6], with C=1e6 and max_iter=2000. Evaluate adjusted probabilities only on that split's held-out test data. Validation is shared between hyperparameter selection and calibration, but test outcomes remain excluded from both. All calibration slopes are positive (approximately .349–1.671), so campaign rankings and capture metrics are unchanged in all 300 fitted model instances.

`scratch/extended_summary.py` derives fixed-band calibration error from aggregate test bands [0,.1), [.1,.3), [.3,.6), [.6,1]: sum over bands of absolute(prediction sum − event sum), divided by test n. Also report mean absolute overall bias per split, mean signed top20 predicted-minus-observed risk, and paired Brier changes. Brier incorporates both calibration and discrimination; these additional bias summaries clarify the probability adjustment.

Scorecard mean Brier falls .079421→.077650 (25/30 splits improve), top20 bias −9.946→+1.097 percentage points, mean absolute overall bias 2.157→1.684 points, and band error 2.930→2.696 points. For all four logistic/tree families, this sigmoid step slightly worsens mean Brier; the memo therefore does not recommend automatic recalibration. No calibration output is presented as proof of future reliability.

### Reporting and results

`scratch/extended_results.json` records all 300 model instances (30 seeds × two source variants × five families), per-split aggregate metrics, chosen settings, calibration bands, summary distributions and same-seed paired differences. `extended_calibration_summary.json` adds calibration diagnostics. Source and split query expressions are in `extended_source.sql` and the script. All reported ranges are descriptive 10th–90th percentiles or explicitly identified minima/maxima, not confidence intervals. Repeated test populations overlap, and win counts across seeds are not independent statistical tests. Active test subsets have only 12–38 churn outcomes.

Across full-data splits, scorecard precision/recall mean .542539/.703441. Expanded-logistic means .598993/.777378; mean paired gains +5.645/+7.394 points, positive in all 30 splits. Deduplicated expanded logistic means .598887/.778282, preserving the comparison. Active scorecard precision/recall mean .161133/.627904; complaints then low seconds .191216/.742302; expanded logistic .208111/.811623; core shallow tree .207551/.803720. Core-tree active index-value recall .839451 versus expanded-logistic .688956 provides an objective trade-off rather than a proven monetary advantage. Service-only complainants consume mean 3.386% of active records with mean cohort churn .688320 and active recall .451143. These are prediction/selection results, not treatment effects.

`scratch/extend_report.py` assembles the four checks into the existing brief, updates the summary and policy implications, generates a repeat-split precision chart and adds the three missing-evidence explanations. `build_brief.py` invokes this extension when its aggregate inputs exist, so rebuilding does not silently discard the follow-up. The existing HTML shell/CSS and inline SVG conventions are preserved.

### Reproduce the extension

Run from repository root after the original diagnostics/scorecard instruments:

```sh
export UV_CACHE_DIR="$PWD/examples/iranian-telecom-churn-local/workspace/scratch/uv-cache"
export PYTHONDONTWRITEBYTECODE=1
uv run --no-sync examples/iranian-telecom-churn-local/workspace/analyse/robustness/scratch/repeat_policy.py
uv run --no-sync examples/iranian-telecom-churn-local/workspace/scratch/extended_models.py
uv run --no-sync examples/iranian-telecom-churn-local/workspace/scratch/extended_summary.py
uv run --no-sync examples/iranian-telecom-churn-local/workspace/scratch/build_brief.py
uv run --no-sync .claude/skills/analyse/scripts/verify_brief.py examples/iranian-telecom-churn-local/workspace/brief.html
```

No new package was installed and no source data was copied. All persistence remains inside the ignored run workspace. The original test-suite limitation was revisited: the current repository no longer has tools/check.py, so invoking it fails `Failed to spawn: tools/check.py; No such file or directory (os error 2)`. Direct current Ruff lint and format checks pass, and all 11 current unittest tests pass. Brief validation passes with the intentional UCI citation-link warning, and the blue chart palette passes all applicable checks. No concurrent repository edits were modified.

## Workspace location

At the user’s request, this run now resides in `examples/iranian-telecom-churn-local/workspace/`, next to the unchanged `question/` inputs. Reproduction commands above use this location; active scripts resolve input paths from their own location and continue to supply absolute paths to DuckDB. Generated artifacts remain locally ignored by Git. Historical log entries retain their original execution paths.
