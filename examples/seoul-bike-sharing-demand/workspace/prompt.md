# Seoul Bike Sharing Demand

You are advising a city bike-share operator on fleet availability.

## Questions

- Diagnose demand by hour, season, weather, holiday, and functioning-day status.
- Build a forecast or decision model for rented bike count, making clear what predictors are known before deployment.
- Recommend service-level, staffing, or rebalancing actions for peak and low-demand periods.
- Explain where a demand model could mislead operational planning and how to monitor drift.

## Expected Deliverable

A notebook or report with demand forecasts, operational metrics, and a fleet-planning recommendation.

## User instruction — 2026-11-04

Complete this assignment examples/seoul-bike-sharing-demand/question

The assignment above is reproduced verbatim from question/BRIEF.md. No subsequent scope changes.

## Follow-up — 2026-11-05 UTC

User: "what would you check if you had more time / what (if anything) was uncertain about the analysis that we could possible check"

Agreed checks: (1) weekday-aware baselines and routinely retrained models across chronological windows; (2) rolling, weekday/weekend-aware calibration with shortage/excess metrics; (3) tighter weather comparisons and leave-one-holiday-date-out sensitivity; (4) post-closure error and delayed-reporting simulations. Additional-data needs: station inventories/durations/flows/unserved requests; archived issued weather forecasts; newer/multi-year rentals.

User: "do 1-4 and make sure the (need more data is noted)"

## 2026-11-05T03:21:18Z — relocation request

User: "move this workspace into the examples folder"
