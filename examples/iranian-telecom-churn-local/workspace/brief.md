**Retention targeting · analytical memo**

# Prioritize service recovery; test offers before scaling

*Iranian Telecom Churn · 3,150 records · prepared 4 November 2026 (Pacific)*

*[Original HTML report](brief.html) · [Methodology](methodology.md) · [Run log](run_log.md)*

This is the GitHub-readable edition of the full report. Download the HTML and open it in a browser for the original layout; references to embedded styling describe that version.

> [!IMPORTANT]
> **Pilot service recovery for active complainants; use richer models to test broader outreach.** Across 30 grouped splits, expanded logistic detects 77.7% of all-account churn at a 20% contact cap, versus 70.3% for the scorecard, and the gain survives duplicate removal. Among active accounts, a simple complaints-then-low-usage rule improves coverage, but neither predictive accuracy nor the value index proves that an offer prevents churn or pays for itself.

## Complaints identify risk even among active customers

Overall churn is **495 / 3,150 (15.7%)**. Customers with complaints churn at **83.0%**, versus **10.1%** without. Among active customers alone, the comparison is **71.1% versus 2.9%**, so the complaint signal is not explained solely by account status.

| Status | Complaints | Customers | Churners | Churn rate |
| --- | --- | --- | --- | --- |
| Active | No | 2,285 | 66 | 2.9% |
| Active | Yes | 83 | 59 | 71.1% |
| Non-active | No | 624 | 229 | 36.7% |
| Non-active | Yes | 158 | 141 | 89.2% |

These are associations, not evidence that complaints cause churn or that resolving them prevents it. Activity changes the interpretation: the highest call-seconds quartile has **0 / 788** observed churners, including **0 / 22** customers with complaints. Zero observed events do not establish zero future risk.

## Lower engagement dominates the descriptive profile

Each row below is a separate split of the full sample. Numeric bins use full-sample quartiles for description only; the scorecard uses a different, training-only threshold. Counts and percentages are unadjusted. Age values are five codes mapping one-to-one to age groups, not a continuous age distribution.

| Profile | Segment | Customers | Churners | Rate |
| --- | --- | --- | --- | --- |
| Complaints | No | 2,909 | 295 | 10.1% |
| Complaints | Yes | 241 | 200 | 83.0% |
| Status | Active | 2,368 | 125 | 5.3% |
| Status | Non-active | 782 | 370 | 47.3% |
| Tariff | Pay as you go | 2,905 | 489 | 16.8% |
| Tariff | Contractual | 245 | 6 | 2.4% |
| Age code | 15 (group 1) | 123 | 0 | 0.0% |
| Age code | 25 (group 2) | 1,037 | 184 | 17.7% |
| Age code | 30 (group 3) | 1,425 | 230 | 16.1% |
| Age code | 45 (group 4) | 395 | 79 | 20.0% |
| Age code | 55 (group 5) | 170 | 2 | 1.2% |

### Raw failure counts do not show a monotonic gradient

| Call failures | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 1 | 823 | 152 | 18.5% |
| &gt; 1 to &lt;= 6 | 816 | 125 | 15.3% |
| &gt; 6 to &lt;= 12 | 817 | 109 | 13.3% |
| &gt; 12 | 694 | 109 | 15.7% |

### Tenure risk peaks in the 31–35 month band

| Months subscribed | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 30 | 867 | 109 | 12.6% |
| &gt; 30 to &lt;= 35 | 806 | 180 | 22.3% |
| &gt; 35 to &lt;= 38 | 763 | 129 | 16.9% |
| &gt; 38 | 714 | 77 | 10.8% |

### Churn is concentrated at lower call duration

| Call seconds | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 1391.25 | 788 | 281 | 35.7% |
| &gt; 1391.25 to &lt;= 2990 | 788 | 145 | 18.4% |
| &gt; 2990 to &lt;= 6478.25 | 786 | 69 | 8.8% |
| &gt; 6478.25 | 788 | 0 | 0.0% |

### Lower call frequency also marks risk

| Call count | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 27 | 795 | 256 | 32.2% |
| &gt; 27 to &lt;= 54 | 801 | 177 | 22.1% |
| &gt; 54 to &lt;= 95 | 776 | 49 | 6.3% |
| &gt; 95 | 778 | 13 | 1.7% |

### High SMS use is associated with little observed churn

| SMS count | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 6 | 800 | 176 | 22.0% |
| &gt; 6 to &lt;= 21 | 785 | 185 | 23.6% |
| &gt; 21 to &lt;= 87 | 778 | 129 | 16.6% |
| &gt; 87 | 787 | 5 | 0.6% |

### Calling fewer distinct numbers marks risk

| Distinct numbers | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 10 | 803 | 251 | 31.3% |
| &gt; 10 to &lt;= 21 | 808 | 140 | 17.3% |
| &gt; 21 to &lt;= 34 | 793 | 88 | 11.1% |
| &gt; 34 | 746 | 16 | 2.1% |

### The value index runs opposite to churn risk

| Value index | Customers | Churners | Rate |
| --- | --- | --- | --- |
| &lt;= 113.801 | 788 | 276 | 35.0% |
| &gt; 113.801 to &lt;= 228.48 | 788 | 142 | 18.0% |
| &gt; 228.48 to &lt;= 788.389 | 786 | 72 | 9.2% |
| &gt; 788.389 | 788 | 5 | 0.6% |

Call failures require an exposure denominator: among customers with calls, failure/call ratios above 15% have **270 / 1,037 (26.0%)** churn, compared with **6 / 345 (1.7%)** for positive ratios up to 5%. Even among active customers without complaints, the rates are **24 / 585 (4.1%)** versus **2 / 333 (0.6%)**. This is a diagnostic ratio, not a validated network failure probability: three records have more failures than calls.

Some apparent drivers change after stratification. Among active customers, tenure of at most 30 months has **71 / 716 (9.9%)** churn versus **8 / 535 (1.5%)** above 38 months. The age-45 code has 20.0% overall churn but only **5 / 252 (2.0%)** among active customers. Active contractual customers have **5 / 244 (2.0%)** churn versus **120 / 2,124 (5.6%)** for active pay-as-you-go customers; this does not establish that migrating tariff plans prevents churn.

Customer Value is an undocumented calculated index, not verified revenue or future margin. Churners average **124.8** index units versus **535.5** for non-churners. Use it as a provisional prioritization signal only; do not translate these units into a cash return.

## The scorecard is stable enough to benchmark, but leaves predictive gains available

**Thirty grouped train/validation/test splits** test stability, model capacity, calibration and duplicate sensitivity. The same predictor profiles remain together, and every model in a split sees the same held-out records. All settings and probability calibration are fitted without test outcomes. Results below use **mean performance across splits**; ranges are the 10th–90th percentiles. They describe sensitivity to splitting, **not confidence intervals**: tests overlap and the dataset has already been explored.

The scorecard averages **54.3% precision** (48.1–59.1%) and **70.3% recall** (66.0–74.5%) at a 20% all-account contact cap. Its complete recall range is 62.9–77.9%. The original 74.0% single-split recall is plausible, but sits toward the favorable end of this distribution. Boundary ties are averaged exactly rather than allowing a lucky tie seed to decide performance.

Compare models first on the same three inputs—complaints, status and call seconds—then expand to ten behavioral inputs. The expanded models add failures, tenure, charge, call frequency, SMS, distinct called numbers and tariff. Age and the undocumented value index are excluded from risk fitting; value remains an evaluation weight. Logistic models use regularization and log transforms for usage/counts; shallow trees learn a small number of interactions. Neither model family is tuned on test.

![Richer models improve predictive precision](brief-assets/repeated-precision.svg)

*Every value is repeated in the table. Selection quality does not measure treatment benefit.*

| Model | AUC | Precision | Precision range | Recall | Value captured |
| --- | --- | --- | --- | --- | --- |
| Scorecard | 0.896 | 54.3% | 48.1%–59.1% | 70.3% | 64.2% |
| Logistic: 3 inputs | 0.910 | 56.9% | 51.5%–64.3% | 73.8% | 64.7% |
| Shallow tree: 3 inputs | 0.926 | 58.5% | 51.4%–65.1% | 75.8% | 72.5% |
| Logistic: 10 inputs | 0.935 | 59.9% | 55.0%–65.2% | 77.7% | 67.8% |
| Shallow tree: 10 inputs | 0.924 | 59.6% | 53.7%–66.3% | 77.3% | 72.7% |

The ten-input logistic model improves precision by **5.65 percentage points** and recall by **7.39 points** versus the scorecard on average, with positive differences on all 30 matched splits. That is consistency across resamples, not 30 independent demonstrations. The three-input shallow tree also improves recall and value capture, so the gain is not solely from collecting more features. Expanded trees capture more of the churn-associated value index than expanded logistic models, despite similar overall precision; model choice depends on the operational objective.

## Duplicate removal preserves the model comparison

Repeat the complete fit, validation selection and test pipeline on **2,850 exact distinct rows**, keeping each profile in the same partition as in the full-data counterpart. Contradictory-label profiles remain grouped; no outcome is used to split them. Deduplication changes both training and evaluation weights, so the difference is a sensitivity result—not a pure improvement in training.

| Model | Full precision | Dedup precision | Full recall | Dedup recall |
| --- | --- | --- | --- | --- |
| Scorecard | 54.3% | 53.7% | 70.3% | 69.7% |
| Logistic: 3 inputs | 56.9% | 56.2% | 73.8% | 73.0% |
| Shallow tree: 3 inputs | 58.5% | 57.6% | 75.8% | 74.9% |
| Logistic: 10 inputs | 59.9% | 59.9% | 77.7% | 77.8% |
| Shallow tree: 10 inputs | 59.6% | 58.9% | 77.3% | 76.4% |

Scorecard precision changes by **−0.56 points** on average; expanded-logistic precision changes by **−0.01 points**. The richer-model advantage therefore does not depend on the exact duplicate rows. Without customer IDs, neither keeping nor removing matching rows can establish the true number of independent customers.

## Calibration helps the scorecard’s probabilities, not its ranking

A sigmoid calibration model is fitted to each selected model’s validation predictions and evaluated on the separate test subset. The same validation subset selects model settings and fits calibration; it never becomes test data. Lower Brier score means lower mean squared probability error. The table reports mean test error before and after calibration.

| Model | Raw Brier | Calibrated Brier | Splits improved / 30 |
| --- | --- | --- | --- |
| Scorecard | 0.0794 | 0.0776 | 25 |
| Logistic: 3 inputs | 0.0745 | 0.0747 | 9 |
| Shallow tree: 3 inputs | 0.0708 | 0.0716 | 9 |
| Logistic: 10 inputs | 0.0690 | 0.0691 | 15 |
| Shallow tree: 10 inputs | 0.0661 | 0.0672 | 10 |

The scorecard underpredicts the selected top fifth’s churn by **9.95 points** on average; calibration changes that to **1.10 points of overprediction**. Its mean absolute overall calibration bias falls from **2.16 to 1.68 points**, and fixed-band calibration error falls from **2.93 to 2.70 points**. Brier improves in **25 / 30** splits. In contrast, all four logistic/tree alternatives have slightly worse mean Brier after this calibration step; do not apply it automatically. All fitted calibration slopes are positive, so rankings, precision and recall are unchanged. These checks do not establish calibration on future accounts.

## Among active customers, combine complaints with usage

For an operational retention comparison, allocate **20% of each active test population** to every rule—87–101 contacts, about 94 on average. This is a different denominator from the all-account table. Each active test subset has only **12–38 churn events**; precision and recall remain variable. The model alternatives are trained and tuned on all accounts, then restricted to active accounts for this evaluation; dedicated active-only fitting is not claimed.

| Active targeting rule | Precision | Precision range | Recall | Value captured |
| --- | --- | --- | --- | --- |
| Complaints first, then random | 14.0% | 10.3%–17.3% | 54.5% | 59.5% |
| Lowest call seconds | 15.9% | 11.6%–20.5% | 61.8% | 41.7% |
| Scorecard | 16.1% | 12.6%–19.4% | 62.8% | 57.8% |
| Complaints, then lowest seconds | 19.1% | 14.5%–23.1% | 74.2% | 61.0% |
| Logistic: 3 inputs | 19.1% | 14.5%–23.1% | 74.2% | 61.0% |
| Shallow tree: 3 inputs | 20.8% | 15.1%–25.1% | 80.4% | 83.9% |
| Logistic: 10 inputs | 20.8% | 16.9%–24.9% | 81.2% | 68.9% |
| Shallow tree: 10 inputs | 19.0% | 14.1%–23.4% | 73.6% | 70.0% |

**Complaints followed by low call seconds** improves active precision by **3.01 points** and recall by **11.44 points** over the scorecard, with positive differences in all 30 splits, both with and without exact duplicates. Low usage alone has lower value capture than the scorecard in every full-data split. The ten-input logistic model adds further breadth: **81.2% active-churn recall** versus 62.8% for the scorecard, but still only **20.8% precision**. Roughly four in five contacts therefore have observed non-churn labels.

The three-input shallow tree is a useful competing candidate: **80.4% active-churn recall** and **83.9% capture of the churn-associated value index**, versus 81.2% and 68.9% for expanded logistic. Its larger index capture does not establish higher profit. Prospective validation should compare these objectives after defining true margin.

**A small service-only cohort is a different trade-off.** Contacting only active complainants averages **16 contacts**, or **3.4% of active accounts**, with **68.8% observed churn** and **45.1% active-churn recall**. Its churn fraction ranges from 52.9% to 84.8% across the middle 80% of splits; the cap never binds. This supports it as a focused service-recovery experiment, but it misses over half of active churn. Do not compare its precision with full-budget rules as if contact volume were equal.

**Policy implication:** begin with the focused service pilot; if seeking broader coverage, test a complaints-then-low-usage outreach rule and compare the three-input tree and expanded logistic as predictive challengers. Broader contact is not a reason to send blanket discounts. Reserve offers for randomized, margin-qualified treatment tests and retain ordinary service for everyone.

## Three operational questions need data this file does not contain

| Check worth doing | Why it could change the call | Why it cannot be completed here |
| --- | --- | --- |
| Status and timing audit | Establish whether non-active accounts are still reachable/retainable and whether each predictor existed before campaign assignment. | The CSV has one summarized Status value, no customer ID, dated feature snapshots, status-change or churn timestamps, contactability fields, or campaign-assignment date. UCI describes a nominal nine-to-twelve-month design; that does not verify row-level timing or eligibility. |
| Validate customer value and margin | Choose economically worthwhile interventions and assess whether index-weighted capture reflects future profit. | No authoritative value formula, currency/unit definition, longitudinal revenue, contribution margin, service cost, offer cost or redemption data is supplied. The index can be profiled but cannot be validated as future cash margin. |
| Measure intervention effectiveness | Distinguish customers whose churn can be prevented from customers merely likely to churn; estimate incremental net benefit. | No randomized assignment, service/offer exposure, usual-care control, treatment timing, uptake or intervention cost fields exist. Churn outcomes alone cannot identify treatment effects. A prospective experiment is needed. |

These gaps are missing evidence, not inconclusive statistical tests. Repeated splitting, deduplication and better prediction cannot fill them. The experiment design below specifies how to obtain the causal evidence.

## A frozen holdout illustrates the scorecard and budget mechanics

The following scorecard and budget tables retain one reproducible training/validation/test split. Use the 30-split comparisons above for stability and policy selection; this worked example explains the scorecard and contact-count arithmetic.

### The twelve-cell scorecard

Split by identical predictor profiles: **1,888 training**, **609 validation**, and **653 test** records. No predictor profile crosses splits. All cutoffs and probabilities are learned from training; validation precision at 20% capacity selects among the three candidates below. The test set is then used for evaluation and explicitly labeled policy sensitivities, without retuning the scorecard.

| Candidate | Validation AUC | Precision at 20% | Detected / 91 churners |
| --- | --- | --- | --- |
| Complaints | 0.705 | 34.7% | 42 |
| Complaints + usage | 0.830 | 44.6% | 54 |
| Complaints + usage + status | 0.876 | 50.4% | 61 |

For each complaint × status × usage cell, the score is `(training churners + 20 × 300/1888) / (training customers + 20)`. This fixed smoothing prevents zero/one probabilities in small cells. Call usage is **zero**, **1–3,100 seconds**, or **above 3,100 seconds**; 3,100 is the median positive training usage. A new combination falls back to the training prevalence, **15.9%**. Unexpected codes or missing inputs require review. Age and value do not enter any fitted risk model in this memo.

| Complaints | Status | Seconds | Training n | Score |
| --- | --- | --- | --- | --- |
| Yes | Non-active | 1–3,100 | 80 | 72.2% |
| Yes | Active | 1–3,100 | 22 | 59.9% |
| No | Non-active | 0 | 68 | 46.8% |
| Yes | Non-active | &gt;3,100 | 11 | 45.7% |
| Yes | Non-active | 0 | 9 | 42.0% |
| No | Non-active | 1–3,100 | 308 | 31.5% |
| No | Non-active | &gt;3,100 | 6 | 27.6% |
| Yes | Active | 0 | 2 | 23.5% |
| Yes | Active | &gt;3,100 | 15 | 23.4% |
| No | Active | 0 | 17 | 16.7% |
| No | Active | 1–3,100 | 487 | 5.4% |
| No | Active | &gt;3,100 | 863 | 1.8% |

On test: **AUC 0.907**, **average precision 0.632** (prevalence 15.9%), and **Brier score 0.079**. A constant training-prevalence prediction has Brier about 0.134 on this test. The status-free candidate still reaches **AUC 0.856** and detects **66 / 104** churners at 130 contacts.

Calibration is imperfect: the selected 130 average **45.7%** predicted risk but show **59.2%** observed churn. Sparse cells are strongly pulled toward the prior. Treat the score as a ranking aid; validate and recalibrate on a later cohort before using probabilities for pricing or expected returns.

| Score band | Test n | Mean prediction | Observed churn |
| --- | --- | --- | --- |
| &lt;10% | 462 | 3.1% | 2.4% |
| 10–&lt;30% | 19 | 20.7% | 31.6% |
| 30–&lt;60% | 150 | 37.8% | 46.7% |
| 60%+ | 22 | 72.2% | 77.3% |

## A contact cap exposes the cost of false positives

Assume a **20% contact cap**, not a known currency budget. Take `floor(cap × eligible population)` contacts; the main retrospective comparison allows all 653 test records. Rank descending by score and use an outcome-blind tie-break (fixed seed 19). Each table reports observed labels, not prevented churn. “Non-churners” are prediction false positives; they are not proven wasted interventions.

| Cap | Contacts | Churners detected | Non-churners | Precision | Recall |
| --- | --- | --- | --- | --- | --- |
| 5.0% | 32 | 27 | 5 | 84.4% | 26.0% |
| 10.0% | 65 | 49 | 16 | 75.4% | 47.1% |
| 20.0% | 130 | 77 | 53 | 59.2% | 74.0% |
| 30.0% | 195 | 93 | 102 | 47.7% | 89.4% |

At 20%, the confusion counts are **77 detected, 53 false positives, 27 missed, and 496 true negatives**. The selection lift is **3.72×** relative to random selection, which would find **20.7** churners on average. This is prediction lift, not retention lift.

Tied scores matter: 20 fixed tie seeds detect **70–77** churners (53.8%–59.2% precision). The exact expectation under uniform random tie-breaking is **74.3**. A nominal 95% Wilson interval for the fixed-seed precision is **50.6%–67.3%**; it assumes independent records and does not account for duplicate clusters, model selection or future distribution change.

![Risk ranking finds more observed churners per contact](brief-assets/policy-precision.svg)

*Same 130-contact capacity; every plotted value appears below.*

| Policy | Detected | Non-churners | Precision | Churn-value captured |
| --- | --- | --- | --- | --- |
| Risk score | 77 | 53 | 59.2% | 68.3% |
| Complaints first | 54 | 76 | 41.5% | 69.0% |
| Risk × value | 38 | 92 | 29.2% | 67.4% |
| Value only | 1 | 129 | 0.8% | 8.0% |

“Churn-value captured” is the share of `sum(value × observed churn)` in selected records, not money saved. Risk × value finds fewer churners and does not improve that share here. Value-only targeting contacts 129 observed non-churners out of 130. Multiplying risk by value would also require comparable intervention effectiveness and costs to approximate an economic ranking; neither assumption is established.

**Eligibility changes the decision.** Risk-only selects **116 non-active** and only **14 active** customers. Restricting to the **493 active** test records and contacting 20% gives **98 contacts, 21 detected churners, and 77 non-churners**: **21.4% precision**, **72.4% recall of 29 active churners**, and **3.64×** lift over the active baseline of 5.9%. Spending the full 130-contact capacity on active customers still detects only 21, adding 32 non-churners. Do not spend the cap merely because it is available.

## Use separate service, offer and no-action routes

**Service intervention:** verify active eligibility and contact customers with complaints; use call usage and the tested model candidates to design prioritization if capacity is scarce. Diagnose the complaint and call-failure history before proposing a remedy. In the single frozen holdout, the service cohort contains **22 active complainants**, including **17 observed churners and 5 non-churners**, well below the 130-contact cap. This is a candidate pilot rule, not a proven effect.

**Offer:** no automatic blanket discount. Test an offer added to service recovery among active complainants with value at least the training median, **222.815 index units**, after checking reachability and actual future contribution margin. There are only **7** such test records, insufficient for an effect estimate. Randomize eligible customers to service-only or service-plus-offer; a high historical risk score alone does not justify payment.

**No proactive paid action:** active customers without complaints unless fresh operational evidence creates a service need; low-risk, high-value customers do not receive a discount solely for their value. Broader low-usage outreach belongs in a measured pilot; do not fill spare capacity with unproven discounts. Non-active accounts need eligibility verification and a separately measured reactivation route before inclusion in retention.

For a cash budget, choose actions with positive `incremental retention probability × future contribution margin − contact/service cost − expected incentive cost`, subject to both the total spending limit and service capacity. Costs must include discounts to customers who would stay anyway. Risk × value is not a substitute for the incremental probability. The dataset supplies neither treatment effects, cash margin nor costs, so it cannot identify a profit-maximizing spend.

## Only a randomized comparison can establish incremental lift here

Run two prespecified randomized comparisons: **enhanced service versus usual care** among verified active complainants, and **service plus offer versus the same service alone** among value-qualified active complainants. Define eligibility and scores before assignment; preserve ordinary support in all arms. Randomize at account level (or household level if spillovers occur), stratifying by risk, value and complaint type. Keep contact intensity comparable where practical and log assignment, delivery, uptake and costs.

The primary effect is **control churn rate minus treatment churn rate** over a fixed three-month window after assignment, analyzed by intention to treat. Report confidence intervals for retention lift and incremental contribution margin net of all costs; track complaints and adverse customer experience. Do not use redemption, treated-only retention or before/after comparisons as proof. Freeze the analysis, avoid repeated unplanned peeking, and reserve a later cohort to validate any learned treatment-effect targeting.

Size the trial from an operational baseline and the minimum economically useful effect. For illustration only, a reduction from **60% to 50%**, 80% power, and a two-sided **2.5%** significance level per comparison (two primary comparisons) requires approximately **470 customers per arm** under independent binomial sampling. Recalculate for the actual baseline, smaller effect, nonresponse and cluster design; the seven offer-eligible test records cannot answer this question.

## Watch items that could change the policy

- **Status timing and eligibility:** verify that the scoring snapshot predates the campaign and that non-active accounts can still be retained. If status is unavailable, use the tested status-free scorecard and revalidate on current accounts.

- **Repeated and conflicting records:** 300 excess exact duplicates; 14 identical predictor profiles have conflicting outcomes. Keeping profiles together avoids cross-split overlap, but customer IDs and timestamps are needed to distinguish duplicates from genuinely similar customers. Deduplicated descriptive churn is 446 / 2,850 (15.6%); the complaint association persists.

- **Out-of-time performance:** no dated snapshots are provided. A conventional row split gives AUC 0.884 and 48.0% precision at 20%, but shares 69 test profiles with training and uses a different test population. Neither split establishes prospective performance.

- **Value and quality:** obtain the value formula, currency margin, eligibility and intervention costs. There are no missing values, but charge code 10 occurs despite source documentation specifying 0–9; charge is excluded from the scorecard.

- **Selection and fairness:** age does not enter the scorecard, but investigate service access and errors by age and tariff in a larger prospective cohort. Small groups and zero-event segments are not safe grounds for denying ordinary support.

## Methodology

All empirical figures were computed from the supplied local `question/data.csv`, with no population filters. Source: [Iranian Churn, UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset) (2020), DOI 10.24432/C5JW3Z, CC BY 4.0; metadata retrieved 5 November 2026 UTC. UCI describes first-nine-month attributes and month-12 churn labels; calendar dates and historical intervention assignments are absent. The local exercise’s author is unverified.

Descriptive tables use full-sample aggregates; predictive bins, prior and cell rates use training only. Three candidate feature sets and smoothing strength were fixed before validation. Profile splitting excludes the outcome from the grouping key. Holdout metrics preserve row weights. The original scorecard and policy checks run inside in-memory DuckDB; the expanded model comparisons use transient local arrays and emit only aggregates. For the requested continuous-feature model comparisons, authorized source records are processed transiently in local memory; no row-level file, prediction list or customer contact list is saved. Saved scripts, SQL, aggregate outputs, checks and limitations are documented in `methodology.md` and `run_log.md`.

## Question &amp; Framing

**As asked:** Complete the Iranian Telecom Churn assignment: profile churn by complaints, call failures, subscription length, usage, tariff plan, status, age and customer value; build a model or scorecard and evaluate a budget-constrained campaign; recommend offer, service or no action; explain the evidence needed for incremental retention lift. The follow-up additionally requests repeated grouped splits, regularized/tree comparisons, calibration and duplicate sensitivity, active-policy comparisons, and explicit reasons the three operational checks remain unavailable.

| Framing decision | Resolved as |
| --- | --- |
| Period | Nine-month feature summary; month-12 churn, per source metadata. No calendar backtest possible; 30 repeated grouped splits provide internal sensitivity only. |
| Metrics | Churn rate, AUC, average precision, Brier score, contacts, precision, recall, observed false positives and value-weighted capture. |
| Budget | Assumed 20% contact capacity; sensitivity at 5%, 10%, 30%. Cash-budget optimization remains conditional on costs and effects. |
| Deliverable | Self-contained memo, reproducible scorecard and model/policy comparisons, with missing operational evidence explained; no notebook required. |

---

*Prediction is not treatment response. Offer and service policies require a prospective experiment before scaling.*
