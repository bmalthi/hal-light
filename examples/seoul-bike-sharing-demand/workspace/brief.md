**Fleet availability • historical planning study**

# Staff seasonal peaks with a calendar-aware forecast and a reviewed reserve

*Seoul bike sharing · 1 December 2017–30 November 2018 · prepared 4 November 2026*

*[Original HTML report](brief.html) · [Methodology](methodology.md) · [Run log](run_log.md)*

This is the GitHub-readable edition of the full report. Download the HTML and open it in a browser for the original layout; references to embedded styling describe that version.

> [!IMPORTANT]
> **Pilot a 28-day same-hour forecast that separates weekdays from weekends, with a rolling workload buffer and human review for holidays, rain and reopening.** It has the lowest April–November average error among the five tested candidates (274 rentals/hour), while the rolling buffer covers 90.3% of hours overall but only 80.2% on holidays. These are retrospective results from one historical year; fresh rental data, issued weather forecasts and station-level inventory/trip information are still required before production validation or numeric fleet sizing.

This report diagnoses completed rentals, tests a midnight-issued forecast for the coming day, and translates the results into staffing and rebalancing decisions. It is a historical assignment, not a forecast for present-day Seoul.

## Operating hours reveal the demand pattern; closures conceal it

The file contains 6,172,314 rentals across 8,760 hours, with a complete hourly grid over 365 days. There are no duplicate date/hour keys, missing values, negative rental counts, or zero-rental operating hours. All 295 nonfunctioning hours have zero rentals: 12 entire days and one partial day. Those zeros describe service status, not proof that nobody wanted a bike.

| Service status | Hours | Rentals | Mean/hour |
| --- | --- | --- | --- |
| No | 295 | 0 | 0.0 |
| Yes | 8,465 | 6,172,314 | 729.2 |

All demand summaries below exclude closed hours. Across the full file, counting closures lowers the average from 729 to 705 rentals/hour. In autumn, the same denominator change lowers 924 to 820. The dataset does not identify closure causes or whether each closure was scheduled.

## Peak timing changes with season and day of week

![Weekdays have two pronounced rental peaks](brief-assets/hourly.svg)

*Weekday (blue) · Weekend (green)<br>Hour labels use the dataset’s local clock. Weekday means include weekday holidays; holiday effects are examined separately below.*

Weekday 08:00 averages **1,306 rentals/hour**, versus 421 on weekends; weekday 18:00 averages **1,724**. Weekday 02:00–05:59 averages only **182**. Weekend demand builds later, so a weekday-only staffing schedule would allocate effort at the wrong time.

<details>
<summary>Hourly chart data: means and operating-hour sample sizes</summary>

| Hour | Weekday mean | n | Weekend mean | n |
| --- | --- | --- | --- | --- |
| 00:00 | 517.6 | 251 | 670.5 | 101 |
| 01:00 | 399.3 | 251 | 547.8 | 101 |
| 02:00 | 273.4 | 251 | 410.6 | 101 |
| 03:00 | 181.5 | 251 | 283.7 | 101 |
| 04:00 | 122.6 | 251 | 174.5 | 101 |
| 05:00 | 151.8 | 251 | 125.4 | 101 |
| 06:00 | 352.3 | 251 | 163.7 | 101 |
| 07:00 | 777.6 | 251 | 255.1 | 102 |
| 08:00 | 1,306.0 | 251 | 420.8 | 102 |
| 09:00 | 732.4 | 251 | 509.3 | 102 |
| 10:00 | 542.5 | 251 | 553.9 | 102 |
| 11:00 | 612.7 | 251 | 642.4 | 102 |
| 12:00 | 700.1 | 251 | 780.1 | 102 |
| 13:00 | 706.0 | 251 | 886.5 | 102 |
| 14:00 | 721.4 | 251 | 940.2 | 102 |
| 15:00 | 790.2 | 251 | 1,022.6 | 102 |
| 16:00 | 910.0 | 251 | 1,090.9 | 102 |
| 17:00 | 1,183.8 | 251 | 1,161.0 | 102 |
| 18:00 | 1,724.1 | 251 | 1,135.6 | 102 |
| 19:00 | 1,306.4 | 251 | 1,062.0 | 102 |
| 20:00 | 1,141.0 | 251 | 1,017.5 | 102 |
| 21:00 | 1,103.3 | 251 | 975.9 | 102 |
| 22:00 | 993.0 | 251 | 858.7 | 102 |
| 23:00 | 705.8 | 251 | 664.8 | 102 |

</details>

![Summer rental throughput is 4.6 times winter](brief-assets/seasons.svg)

*Each season is observed once. Temperature, daylight, calendar and any fleet changes are not separable causal effects here.*

| Season | Open hours | Mean/hour | 90th percentile |
| --- | --- | --- | --- |
| Summer | 2,208 | 1,034.1 | 2,094.6 |
| Autumn | 1,937 | 924.1 | 1,836.2 |
| Spring | 2,160 | 746.3 | 1,648.3 |
| Winter | 2,160 | 225.5 | 412.3 |

| Season | Day type | Peak hour | Mean at peak | n |
| --- | --- | --- | --- | --- |
| Autumn | Weekday | 18:00 | 2,201 | 57 |
| Autumn | Weekend | 17:00 | 1,531 | 24 |
| Spring | Weekday | 18:00 | 1,888 | 64 |
| Spring | Weekend | 17:00 | 1,272 | 26 |
| Summer | Weekday | 18:00 | 2,327 | 66 |
| Summer | Weekend | 20:00 | 1,761 | 26 |
| Winter | Weekday | 08:00 | 544 | 64 |
| Winter | Weekend | 15:00 | 340 | 26 |

**The staffing flip test matters:** winter weekdays peak at 08:00, while spring, summer and autumn peak at 18:00. Summer weekends peak at 20:00, versus 15:00 in winter. These are average peak hours, not guaranteed daily maxima.

## Rain matters strongly; the raw holiday discount is misleading

| Condition | Open hours | Mean rentals/hour |
| --- | --- | --- |
| Dry | 7,949 | 765.6 |
| Wet | 516 | 167.3 |
| No snow | 8,022 | 759.2 |
| Snow recorded | 443 | 185.1 |
| Holiday | 408 | 529.2 |
| No Holiday | 8,057 | 739.3 |

Wet hours average **167** rentals versus **766** in dry hours. Standardizing within season × hour × weekday/weekend cells gives **153.6 versus 884.4**, an 82.6% gap; matching by month instead gives an 84.0% gap. This remains an association: rain timing, temperature and other factors are not randomized.

The evening peak also weakens in rain. On summer weekdays, 17:00–19:59 averages **2,120 in dry hours versus 569 in wet hours** (174 and 24 hours); in autumn it is 1,868 versus 63 (164 and only 7 hours). Keep reserve crews flexible and avoid applying a universal rain multiplier.

Holidays average 529 rentals/hour versus 739 otherwise, a raw **28.4% discount**. After matching season, hour and weekend status, the comparison is 661 versus 713, only **7.3% lower**; month matching gives 13.3% lower. There are only 17 operating holiday dates. A blanket 28% holiday fleet reduction would overstate the evidence.

| Temperature | Open hours | Mean/hour |
| --- | --- | --- |
| &lt;0°C | 1,433 | 198.0 |
| 0–&lt;10°C | 2,118 | 426.3 |
| 10–&lt;20°C | 2,050 | 837.2 |
| 20–&lt;30°C | 2,340 | 1,148.1 |
| ≥30°C | 524 | 1,112.2 |

<details>
<summary>Other weather signals and interpretation</summary>

| Measured variable | Pearson correlation with rentals |
| --- | --- |
| Temperature (°C) | +0.563 |
| Humidity (%) | -0.202 |
| Wind (m/s) | +0.125 |
| Visibility (10 m) | +0.212 |
| Dew point (°C) | +0.400 |
| Solar radiation (MJ/m²) | +0.274 |
| Rainfall (mm) | -0.129 |
| Snowfall (cm) | -0.152 |

All correlations use 8,465 operating hours and are descriptive, unadjusted associations. Positive wind and solar correlations can reflect time-of-day and season; they do not justify increasing supply when wind rises. Rainfall’s weak linear correlation does not contradict the large wet/dry difference: most hours have zero rain. Temperature and dew point overlap; avoid interpreting correlated predictors as independent drivers. Seventeen observations record zero humidity and need a sensor/coding check before weather deployment. The deployable models do not use those weather readings.

</details>

### Temperature matching confirms the rain signal; holiday size depends on the comparison

Matching wet and dry observations on temperature as well as calendar leaves a large negative association. Each specification below also matches hour and weekday/weekend; 5°C bins group similar temperatures. Shares refer to retained operating wet/dry hours.

| Matched variables | Wet / dry hours | Wet / dry retained | Wet / dry mean | Difference |
| --- | --- | --- | --- | --- |
| Season | 516 / 6,087 | 100.0% / 76.6% | 153.6 / 884.4 | -82.6% |
| Season + temperature | 509 / 3,400 | 98.6% / 42.8% | 201.0 / 938.3 | -78.6% |
| Month + temperature | 458 / 1,882 | 88.8% / 23.7% | 181.8 / 937.2 | -80.6% |
| Season + temperature + humidity | 365 / 735 | 70.7% / 9.2% | 209.0 / 704.7 | -70.3% |

The season/temperature comparison contains 100 wet dates and 332 dry dates, with possible overlap; hours and dates are not independent experiments. Requiring at least three observations per arm in each cell gives a −83.1% rain gap but retains only 171 wet and 613 dry hours. Adding humidity narrows support sharply and may adjust away part of the weather pathway. Excluding the zero-humidity readings leaves that matched result unchanged. **The direction is consistent; none of these percentages is a causal rain effect or a ready-to-use forecast multiplier.** Different specifications retain different populations, so differences between estimates cannot be attributed entirely to the added matching variable.

Holiday stability is assessed by omitting each of the 17 operating holiday dates and recomputing the matched comparison. The ranges below are sensitivity ranges, not confidence intervals.

| Matching | Full difference | Leave-one-date-out range | Negative omissions |
| --- | --- | --- | --- |
| Season + hour + day type | -7.3% | -14.9% to +0.2% | 16 / 17 |
| Month + hour + day type | -13.3% | -19.7% to -9.3% | 17 / 17 |
| Season + calendar + temperature + rain | -12.0% | -17.7% to -9.3% | 17 / 17 |
| Month + calendar + temperature + rain | -13.7% | -16.8% to -12.2% | 17 / 17 |

The season-only holiday result can change sign when one date is removed; the sign flip persists when common-support cells are fixed (−16.0% to +0.7%). Month-and-weather matching remains negative, but retains only 372 of 408 holiday hours and 1,677 of 8,057 nonholiday hours. Holding support fixed across every weather-matched omission leaves just 130 holiday hours from 10 dates; its range is −16.7% to −7.4%. This supports event-specific review and additional years of holiday data, rather than a single fleet-reduction percentage.

## Calendar-aware recent demand is the strongest overall pilot candidate

**Forecast contract:** issue at 00:00 local time for hours 00–23 using only information already available. All counts through the preceding day are assumed finalized for the main comparison; reporting-delay scenarios are tested below. Target-day rentals and realized target-hour weather never enter deployable forecasts. Planned closures may override the forecast only when genuinely known in advance.

Five fixed candidates are evaluated on the same **5,561 operating hours from April through November**. Forecasts are generated forward from March; each fitted model trains only before its forecast month. All of these dates have already been examined during this assignment, so this is an exploratory retrospective comparison, not a new untouched holdout.

| Candidate | Construction / update |
| --- | --- |
| Recent 7 days | Mean of the same hour over the preceding 7 calendar days, excluding closed observations. |
| 28-day weekday/weekend | Mean of the same hour and same weekday/weekend type over the preceding 28 calendar days. |
| Previous 4 same weekdays | Mean of the same hour on the preceding 4 occurrences of the weekday. |
| Monthly expanding model | Fixed histogram gradient boosting settings; refit on all eligible earlier history at each month start. |
| Monthly 90-day model | Same settings/features; refit using eligible operating observations within the preceding 90 calendar days. |

The fitted models use hour, weekday, month, annual sine/cosine and the holiday calendar, plus lagged counts: 24/48/168-hour lags, prior seven-day same-hour mean/standard deviation, prior four-week same-weekday/hour mean, and prior-day mean. Closed past hours are unavailable, not demand zeros. Empty baseline strata fall back to a past-only 28-day same-hour mean. No holiday-specific baseline reduction is fitted from these sparse holidays.

| April–November | MAE | RMSE | WAPE | Bias | Month wins |
| --- | --- | --- | --- | --- | --- |
| Recent 7 days | 292.2 | 445.7 | 30.6% | -0.2% | 3/8 |
| 28-day weekday/weekend | 274.1 | 420.6 | 28.7% | -0.9% | 3/8 |
| Previous 4 same weekdays | 309.4 | 461.8 | 32.4% | -1.2% | 0/8 |
| Monthly expanding model | 290.4 | 456.8 | 30.4% | -0.3% | 2/8 |
| Monthly 90-day model | 299.0 | 460.6 | 31.4% | -1.3% | 0/8 |

Errors are rentals/hour. The calendar-aware baseline has MAE **274.1**, compared with 292.2 for the seven-day baseline and 290.4 for monthly expanding training. The morning 06:00–09:59 error improves from 380.1 to 255.9 relative to the seven-day baseline. However, it wins only three of eight months; the seven-day baseline also wins three, and the expanding model wins two. In April–May, expanding training has lower MAE (331.2 versus 353.4). Keep both alternatives visible in shadow evaluation.

<details>
<summary>Monthly MAE for every candidate</summary>

| Month | 7 days | Day type 28 | Same weekday 4 | Expanding | Rolling 90 |
| --- | --- | --- | --- | --- | --- |
| 2018-04 | 330.7 | 318.5 | 339.5 | 276.2 | 279.7 |
| 2018-05 | 378.7 | 387.2 | 434.0 | 384.4 | 384.4 |
| 2018-06 | 312.1 | 312.4 | 342.4 | 382.5 | 347.1 |
| 2018-07 | 295.1 | 246.0 | 293.3 | 300.6 | 348.3 |
| 2018-08 | 238.6 | 219.2 | 242.5 | 221.4 | 221.9 |
| 2018-09 | 310.0 | 327.2 | 350.4 | 370.3 | 366.0 |
| 2018-10 | 261.9 | 225.2 | 273.5 | 243.2 | 264.1 |
| 2018-11 | 205.0 | 152.3 | 195.0 | 137.6 | 175.0 |

</details>

On the common October–November slice, monthly retraining yields MAE **191.1**, compared with 238.5 when the same model is frozen after August. The calendar-aware baseline scores **189.2**, but its +10.8% bias is less favorable than the retrained model’s +2.5%. Thus stale model weights explain part of the earlier comparison; the baseline’s small autumn error advantage does not establish a universal winner.

| October–November | MAE | RMSE | Bias |
| --- | --- | --- | --- |
| Recent 7 days | 233.8 | 377.0 | +3.2% |
| 28-day weekday/weekend | 189.2 | 331.0 | +10.8% |
| Previous 4 same weekdays | 234.7 | 376.2 | +12.4% |
| Monthly expanding model | 191.1 | 320.0 | +2.5% |
| Monthly 90-day model | 220.1 | 343.4 | -3.1% |

Across April–November, the calendar-aware baseline’s paired MAE advantage is 18.2 rentals/hour over recent seven days and 16.3 over expanding training. Approximate seven-day-block bootstrap intervals are 0.8–39.6 and 0.05–37.6, respectively. Because the reference was selected on these scored dates, these intervals are conditional, exploratory and not adjusted for selection; the second barely excludes zero. **Recommend a pilot candidate, not proven statistical or operational superiority.**

Realized-weather readings remain a diagnostic only: the original October–November comparator scored MAE 182.5 using weather from the rental hour. Archived forecasts issued at planning time are needed to establish achievable weather-aware accuracy.

## Rolling buffers improve the trade-off, but miss some months and holidays

Each hourly upper workload estimate adds a nonnegative 90th-percentile residual buffer to its point forecast. Residuals come from **earlier out-of-sample forecasts** whose outcomes are available before the current day. Compare three fixed recipes: March-only buffers by time block; preceding 28 days by block; and preceding 56 days by block × weekday/weekend. Sparse cells fall back to broader past-only groups. No buffer is tuned to hit 90% on the scored period.

| 28-day calendar baseline buffer | Coverage | Shortfall | Unused/hour | 90% loss |
| --- | --- | --- | --- | --- |
| Fixed March / block | 88.89% | 1.86% | 413 | 57.3 |
| Rolling 28 days / block | 90.27% | 1.49% | 381 | 50.9 |
| Rolling 56 days / block + day type | 89.43% | 1.66% | 410 | 55.3 |

The rolling 28-day recipe covers **90.3%** of operating hours, with a **1.49%** shortfall proxy and **381 rentals/hour** of unused headroom. It has the lowest 90th-percentile loss among the tested model/recipe combinations. This loss weights each unit of underprediction nine times each unit of overprediction; it is an illustrative loss function, not measured operator cost. Splitting buffers further by weekday/weekend over 56 days does not improve the pooled trade-off.

Coverage is the fraction of hours with rentals ≤ upper estimate. Shortfall is total positive (rentals − upper) divided by total rentals; unused headroom is mean positive (upper − rentals). These remain workload proxies, not stockouts, unused bicycles or a guaranteed customer-availability level.

| Month | Hours | Rolling coverage | Shortfall |
| --- | --- | --- | --- |
| 2018-04 | 696 | 86.6% | 2.98% |
| 2018-05 | 720 | 89.3% | 1.69% |
| 2018-06 | 720 | 93.1% | 0.74% |
| 2018-07 | 744 | 96.6% | 0.23% |
| 2018-08 | 744 | 80.4% | 3.34% |
| 2018-09 | 624 | 84.0% | 2.36% |
| 2018-10 | 665 | 95.5% | 0.75% |
| 2018-11 | 648 | 96.9% | 0.15% |

| Slice | Hours | Coverage | Shortfall | Unused/hour |
| --- | --- | --- | --- | --- |
| Weekday | 3,960 | 90.8% | 1.21% | 373 |
| Weekend | 1,601 | 88.9% | 2.24% | 399 |
| Nonholiday | 5,369 | 90.6% | 1.44% | 375 |
| Holiday | 192 | 80.2% | 3.00% | 548 |
| Dry | 5,109 | 89.4% | 1.51% | 310 |
| Wet | 452 | 99.8% | 0.04% | 1,178 |
| 06:00–09:59 | 927 | 90.7% | 1.65% | 390 |

**Overall calibration hides material gaps:** August coverage is 80.4%, September 84.0%, and holiday coverage 80.2% across eight holiday dates. Wet-hour coverage is 99.8%, leaving 1,178 rentals/hour of unused headroom. The default therefore needs event and weather review; neither extra segmentation nor a historical 90% average is sufficient for autonomous resource allocation.

| Reopening slice | Hours | Coverage | Shortfall | Unused/hour |
| --- | --- | --- | --- | --- |
| Other operating hours | 5,273 | 90.2% | 1.52% | 373 |
| First 24 hours after reopening | 288 | 91.3% | 1.03% | 521 |

The reopening envelope covers 91.3% of hours but leaves 521 rentals/hour of unused headroom, compared with 373 otherwise. Its coverage does not remove the need to review reopening forecasts and resource allocation.

## Review reopening forecasts and enforce the actual data cutoff

There are **12 reopening events** in April–November, contributing **288 operating hours** in the first 24 hours after a closed-to-open transition. Calendar-aware baseline error is higher in these hours. Comparing with normal hours matched to the reopening mix shows how much of the gap can reflect the calendar and weather.

| Baseline comparison | Post-reopening hours | Post MAE | Matched normal MAE |
| --- | --- | --- | --- |
| Season + hour + day type | 288 | 319.8 | 242.7 |
| Also wet/dry | 283 | 311.9 | 287.7 |

Calendar matching gives 319.8 versus 242.7 rentals/hour of error. Adding wet/dry matching narrows this to **311.9 versus 287.7**, retaining 283 reopening hours. This does not isolate a causal closure effect or prove that missing history alone causes the errors. Flag reopening for manual review, retain older valid history, and monitor its errors separately; closure reasons and station inventories are needed to explain the residual.

Latency scenarios assume that an hour’s count is available only at the **end of the hour plus 1, 6 or 24 hours** of processing delay. Forecast issue stays at midnight. Both features and refit labels obey that cutoff. “Unadapted” fitted models learn from clean-history features but receive delayed features at scoring; “latency-trained” models use the same delayed feature construction during training and scoring.

| Extra delay | 7-day MAE | Day-type MAE | Fitted unadapted MAE | Latency-trained MAE |
| --- | --- | --- | --- | --- |
| 0 hours | 292.2 | 274.1 | 290.4 | 290.4 |
| 1 hours | 292.7 | 274.2 | 299.1 | 288.0 |
| 6 hours | 297.0 | 275.7 | 287.4 | 292.1 |
| 24 hours | 305.0 | 278.7 | 317.5 | 312.7 |

The calendar-aware baseline is relatively stable in these scenarios: MAE 274.1 with no extra delay and 278.7 with 24 hours. The expanding model moves from 290.4 to 317.5 unadapted, or 312.7 after latency-aware retraining. Shorter-delay effects are not monotonic, so this is not a universal degradation curve. Under a 24-hour delay, yesterday’s same-hour count and yesterday’s mean are unavailable throughout the forecast day; all-missing columns are removed when training that scenario. Baseline fallbacks remained finite in every tested case.

Intervention checks changed every target-day-and-later rental count and operating status and confirmed that the day’s feature values did not change at any tested latency. Availability assertions also verify every lag against its interval-end cutoff. **Actual ingestion timestamps are absent**: these tests establish code behavior under assumed delays, not the real pipeline’s latency or readiness.

## A historical next-day forecast separates Saturday demand from weekday demand

For **1 December 2018**, assuming an operating nonholiday Saturday, the calendar-aware baseline predicts **14,254** daily rentals. This is a historical illustration beyond the file endpoint; there is no observed outcome to score and no present-day prediction.

| Hours inclusive | 7-day mean/hour | Day-type mean/hour | Monthly model mean/hour |
| --- | --- | --- | --- |
| 00–05 | 265 | 348 | 307 |
| 06–09 | 656 | 296 | 481 |
| 10–16 | 627 | 820 | 678 |
| 17–20 | 958 | 837 | 885 |
| 21–23 | 635 | 632 | 582 |

The calendar-aware morning forecast is 296 rentals/hour versus 656 from the baseline that mixes weekdays and weekends. Fitted-model values use the month-start refit stated in the methodology. These are block averages of hourly point forecasts, not fleet counts or block-capacity guarantees.

## Fleet-planning recommendation

- **Pilot the calendar-aware baseline with the rolling 28-day workload buffer.** Keep monthly expanding forecasts as a challenger, monitor seasonal bias, and require human review for holidays, rain and reopening. Validate this fixed choice on newly acquired dates before promotion.

- **Rebalance before the demand arrives.** Pilot a pre-07:00 weekday readiness check and pre-17:00 replenishment in spring, summer and autumn; prioritize readiness before 08:00 in winter. Use station-level outbound and return patterns to decide truck routes and dock capacity. The citywide data establish timing, not origins and destinations.

- **Shift flexible staffing by season and day type.** Retain coverage into summer weekend evenings; winter weekends need an earlier afternoon emphasis. Allocate maintenance and repairs preferentially to 02:00–05:59, subject to safety and labor constraints, while preserving a core service.

- **Use weather and events for reviewed adjustments.** Prepare a wet-weather roster with reserve staff that can return when conditions change. Avoid a blanket holiday reduction; check event calendars and demand on comparable dates. Scheduled closures have a separate operations workflow, not a low-demand forecast.

- **Pilot service targets before expanding the fleet.** Use station stockout minutes, full-dock minutes, unserved requests, and rebalancing moves per staff-hour to judge availability and cost. Treat 90% hourly workload coverage only as a trial forecast target; choose a customer-availability target and budget with the operator.

- **Defer a numeric fleet purchase or crew count.** Hourly rentals are flows; the same bike can be rented repeatedly. Estimate bikes concurrently in use from departures and trip duration, then add idle bikes required at stations, imbalance reserves and maintenance stock. Crew sizing additionally needs relocation volumes, travel/loading time and measured productivity. None of those inputs is in this file. A 4.6× summer/winter rental ratio is not a 4.6× fleet requirement.

## Watch items that could change the decision

- **Demand censored by supply:** completed rentals miss failed attempts and empty/full stations. A low forecast can perpetuate shortages. Log unserved demand and station inventory alongside rentals; distinguish capacity restrictions from preference changes.

- **Drift:** store forecast issue time, input cutoff, model version and forecast as issued. Report rolling weekly and four-week MAE, WAPE and signed bias, plus peak-hour, wet/dry, holiday and station slices. Compare against the same calendar-aware baseline each time and track first-day-after-reopening performance separately. Avoid MAPE because closures are zeros and low-volume hours make percentage errors unstable.

- **Coverage and cost:** monitor envelope exceedance, shortfall proxy, and unused headroom together. Review both undercoverage and sustained overcoverage. Recalibrate with completed past dates and test the new rule on a fresh forward window; do not tune using the scored horizon.

- **Illustrative alert policy:** review a model after two consecutive weekly WAPE readings above 35%, absolute bias above 10%, or four-week envelope coverage outside 85–95%. These are proposed starting thresholds, not estimated optima; require adequate sample size and separate holiday/event review. Alerts should trigger diagnosis, not automatic fleet cuts.

- **Changing inputs:** watch late rental logs, missing lags, closure frequency, weather missingness and out-of-range readings, holidays, station additions and pricing changes. Use a measured ingestion cutoff. If counts are late, remove unavailable lags and use the tested past-only baseline fallback; repeat calibration under that actual latency. Check the 17 zero-humidity readings before adopting weather features.

- **Generalization:** only one historical annual cycle is observed; forward evaluation covers April–November and has already been used to compare candidates. No fresh confirmation period, independent winter or year-to-year test establishes that these accuracy figures transfer to another season or to today. Revalidate on current operations before using the recommendations for procurement.

## More data is still needed for operational validation and fleet sizing

All four requested checks were completed with the supplied file. The following gaps cannot be resolved by more modeling of the same completed-rental counts.

| Additional data needed | What it would let us check | Current limit |
| --- | --- | --- |
| Newer rentals and additional full years | Confirm the selected model/buffer on untouched dates, including winter and changing station coverage. | Current model selection and sensitivity intervals are retrospective; no validated present-day accuracy. |
| Weather forecasts archived as issued, with issue time and horizon | Measure forecast-weather error and test a deployable weather-aware model. | Realized weather associations cannot be used as tested day-ahead inputs. |
| Station inventory, dock capacity, departures/returns, trip durations, rejected attempts | Estimate bikes concurrently in use, unmet demand, station stockouts and rebalancing routes. | Hourly completed rentals do not identify fleet stock or availability. |
| Holiday/event identities over multiple years; closure cause and schedule | Separate individual events, scheduled downtime and unexpected outages. | 17 operating holiday dates and 12 evaluation reopening events support limited generalization. |
| Record arrival/finalization times and weather-sensor quality metadata | Verify midnight availability, actual latency and zero-humidity coding. | 1/6/24-hour delays are simulations; sensor anomalies remain unexplained. |
| Relocation volumes, truck travel/loading times, repair workload and staff productivity | Convert workload forecasts into crew shifts, reserve costs and procurement decisions. | No defensible numeric fleet purchase or crew count can be inferred from this file. |

## Methodology and reproducibility

Source: supplied `examples/seoul-bike-sharing-demand/question/data.csv`; attribution: [Seoul Bike Sharing Demand (2020), UCI Machine Learning Repository](https://doi.org/10.24432/C5F62R), CC BY 4.0. Metadata was opened on 5 November 2026 UTC for definitions; every empirical number comes from the local CSV. Source records are processed only in memory; saved outputs are aggregates.

Dates parse as day/month/year. Weekends are Saturday/Sunday, wet means rainfall &gt; 0, and all demand/error tables exclude nonfunctioning hours unless explicitly stated. Standardized weather/holiday means weight each retained common-support cell by its combined exposed/reference count. Five-degree temperature and 20-percentage-point humidity bins are defined in the saved instrument. Leave-one-holiday-date-out ranges recompute comparisons; fixed-support checks distinguish changes in cell coverage. These remain observational associations.

Forward predictions start in March; April–November evaluation uses 5,561 operating hours. Monthly model fits use earlier operating observations beginning 29 December 2017, or the most recent 90 days for the rolling candidate. Hyperparameters are fixed: 180 iterations, 15 leaves, learning rate 0.06, L2 10, leaf minimum 25, no early stopping, seed 42. Seven-day moving-block resampling uses 2,000 replicates. The baseline and buffer recommendations were selected from this retrospective comparison; no new untouched test is claimed.

Upper buffers use sorted residual rank min(n, ceil((n+1) × 0.90)); cells require at least 30 earlier out-of-sample errors, otherwise fall back to the same time block and then the broader past window. The 56-day recipe initially uses available history since March. All rows share the same scored hours. Coverage, positive shortfall, excess headroom and 90% pinball loss expose both undercapacity and overcapacity. Averages of hourly envelopes are not quantiles of multi-hour totals.

Reopening means the first 24 hours after a nonfunctioning-to-functioning transition. Calendar and wet/dry matched normal-hour error means are weighted to the reopening-hour mix. Delay scenarios enforce count-interval end plus processing delay ≤ forecast issue, including refit-label availability. They assume uniform delays and do not establish real arrival timing.

Instruments: `analyse/diagnostics/scratch/diagnose.py`, `analyse/forecast-stress/scratch/forecast_stress.py`, `analyse/weather-sensitivity/scratch/sensitivity.py`, and `scratch/closure_latency.py`; shared feature construction is in `scratch/forecast_common.py`. The original frozen-model comparison remains reproducible in `scratch/model.py`. Full commands, checks and missing-data requirements are in `methodology.md`. Charts and styling are embedded; no network or JavaScript is required.

## Question &amp; Framing

**As asked:** advise a city bike-share operator on fleet availability; diagnose demand by hour, season, weather, holiday and functioning-day status; build a rental-count forecast with clear deployment-time predictors; recommend service-level, staffing or rebalancing actions; explain planning pitfalls and drift monitoring.

| Framing decision | Resolved as |
| --- | --- |
| Period | Full supplied year for diagnosis; monthly forward predictions from March, April–November retrospective comparison; original October/November split retained as a same-period reference. |
| Target | Systemwide hourly completed rentals conditional on operation; workload envelope and shortfall proxy, not unconstrained requests or concurrent bike stock. |
| Deployment | Midnight issue with available past counts and calendar; test 1/6/24-hour processing delays. Known schedules only; actual weather remains diagnostic. |
| Deliverable | Report with forecasts and operational proxies, stronger model comparisons, sequential calibration, weather/holiday sensitivity, closure/latency checks, recommendations and explicit additional-data needs. |

**Additional requested scope:** complete the four robustness checks described above and state what still needs more data.

---

*Historical observational evidence • limited holiday samples • no station inventory or trip durations*
