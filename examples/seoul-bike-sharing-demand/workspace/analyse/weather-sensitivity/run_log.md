# Weather/holiday sensitivity — run log

## 2026-11-05T03:01:26Z — framing contract

- Estimand: the conditional descriptive difference in completed rentals between wet/dry and holiday/nonholiday operating hours, and stability to closer matching and removal of one holiday date.
- Population: the same authorized hourly source, Functioning Day = Yes. Raw rows remain inside script memory; output is aggregate only.
- Comparison: common-support standardization, equal pooled weights for both arms within calendar cells; add 5°C temperature bins and optionally 20-percentage-point humidity bins. Repeat with at least three hours per arm to expose sparse-support sensitivity. Holiday leave-one-date-out repeats the entire standardization, with a fixed-support alternative to distinguish composition instability.
- Rival frame: the original rain gap could reflect season/temperature; holiday discount could be driven by a few dates or changed common support. Run the discriminating cuts rather than merely caveat them.
- Decision surface: reproducible aggregate JSON plus methodology and summary for parent brief, covering match support, distinct dates, leave-one-out range/sign, and specific missing data. These are retrospective associations, never causal weather/holiday effects or operational multipliers.
- Additional-data limits: multiple years/holiday events, archived issue-time weather forecasts, and station availability/unserved requests are absent. Matching observed weather cannot establish performance using forecast weather.

## 2026-11-05T03:03:15Z — results and rival verdict

- Instrument `scratch/sensitivity.py`, query record `scratch/queries.sql`, all aggregates `scratch/findings.json`. Original season-only estimates reproduce: rain −82.6274%; holiday −7.3295%.
- Temperature-matched rain: season/hour/daytype/temp5 −78.5796%, standardized means 200.9827 vs 938.2768; 509 wet and 3,400 dry hours, 100 vs 332 distinct dates. Month/hour/daytype/temp5 −80.6037%, 458 wet/1,882 dry hours. Rival verdict: temperature/calendar mix does not explain away the negative rain association, but matched support differs from all dry hours.
- Minimum-three-per-arm rain estimates stay negative (season −83.1133%; month −80.1092%), but wet-hour retention falls to 33.1% and 9.1%. They are narrow-support sensitivity checks, not preferred population estimates.
- Adding humidity20 produces −70.3475%, with 365 wet/735 dry hours. Excluding zero-humidity observations leaves both retained sample and estimate unchanged. Matched reference retention only 9.2%; explicitly flag support and possible overcontrol rather than claiming causality.
- Holiday LODO season/hour/daytype range −14.9218% to +0.2172%, 16/17 negative; fixed-cell variant −16.0416% to +0.7410%, also 16/17 negative. Rival verdict: the precise season-only discount and its sign are fragile to one holiday date, not solely due to lost support cells.
- Month matching full holiday difference −13.3123%, LODO −19.7363% to −9.3300%, all17 negative. Month+temp5+wet full −13.7233% (372 holiday/1,677 nonholiday hours; all17 holiday dates), LODO −16.7715% to −12.2080%, all17 negative. Fixed support weather/month subset retains only130 holiday hours, so no broad extrapolation.
- Independent sum/count reconstruction of temperature-matched rain means agrees to <1e-9 (asserted). All17 omissions runnable. Sensitivity ranges are not confidence intervals; dates/within-date hours may be dependent.
- Coverage: tighter weather matching and humidity/sensor sensitivity → `rain`; holiday deletion stability and support sensitivity → `holiday_leave_one_date_out`; retained hours/dates → every comparison; additional-data requirements → `interpretation.missing_data` and methodology. Parent receives aggregate findings only. No brief required by handoff.
