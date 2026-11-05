"""Current report sections for the four user-requested empirical sensitivity checks."""
import json

def revise(body, run, table, details, n):
    f=json.loads((run/'analyse/forecast-stress/scratch/results.json').read_text())
    w=json.loads((run/'analyse/weather-sensitivity/scratch/findings.json').read_text())
    c=json.loads((run/'scratch/closure_latency_results.json').read_text())
    names={'recent7':'Recent 7 days','daytype28':'28-day weekday/weekend','weekday4':'Previous 4 same weekdays',
        'hgb_expanding':'Monthly expanding model','hgb_rolling90':'Monthly 90-day model'}
    env=next(r for r in f['envelopes'] if r['model']=='daytype28' and r['recipe']=='rolling28_block')
    body=body.replace('Staff the seasonal peaks; keep the forecast simple until weather is usable',
        'Staff seasonal peaks with a calendar-aware forecast and a reviewed reserve')
    start=body.index('<section class="bottomline">')
    end=body.index('</section>',start)+len('</section>')
    body=body[:start]+'''<section class="bottomline"><b>Pilot a 28-day same-hour forecast that separates weekdays from weekends, with a rolling workload buffer and human review for holidays, rain and reopening.</b>
It has the lowest April–November average error among the five tested candidates (274 rentals/hour), while the rolling buffer covers 90.3% of hours overall but only 80.2% on holidays.
These are retrospective results from one historical year; fresh rental data, issued weather forecasts and station-level inventory/trip information are still required before production validation or numeric fleet sizing.</section>'''+body[end:]

    weather='''<h3>Temperature matching confirms the rain signal; holiday size depends on the comparison</h3>
<p>Matching wet and dry observations on temperature as well as calendar leaves a large negative association. Each specification below also matches hour and weekday/weekend; 5°C bins group similar temperatures. Shares refer to retained operating wet/dry hours.</p>'''
    rain_keys=[('season_hour_daytype','Season'),('season_hour_daytype_temp5','Season + temperature'),
        ('month_hour_daytype_temp5','Month + temperature'),('season_hour_daytype_temp5_humid20','Season + temperature + humidity')]
    weather+=table(['Matched variables','Wet / dry hours','Wet / dry retained','Wet / dry mean','Difference'],[
        [label,f"{n(w['rain'][k]['exposed_hours'])} / {n(w['rain'][k]['reference_hours'])}",
        f"{w['rain'][k]['exposed_retained_pct']:.1f}% / {w['rain'][k]['reference_retained_pct']:.1f}%",
        f"{w['rain'][k]['standardized_exposed_mean']:.1f} / {w['rain'][k]['standardized_reference_mean']:.1f}",
        f"{w['rain'][k]['relative_difference_pct']:.1f}%"] for k,label in rain_keys])
    weather+='''<p>The season/temperature comparison contains 100 wet dates and 332 dry dates, with possible overlap; hours and dates are not independent experiments. Requiring at least three observations per arm in each cell gives a −83.1% rain gap but retains only 171 wet and 613 dry hours. Adding humidity narrows support sharply and may adjust away part of the weather pathway. Excluding the zero-humidity readings leaves that matched result unchanged. <b>The direction is consistent; none of these percentages is a causal rain effect or a ready-to-use forecast multiplier.</b> Different specifications retain different populations, so differences between estimates cannot be attributed entirely to the added matching variable.</p>
<p>Holiday stability is assessed by omitting each of the 17 operating holiday dates and recomputing the matched comparison. The ranges below are sensitivity ranges, not confidence intervals.</p>'''
    holiday_labels={'season_hour_daytype':'Season + hour + day type','month_hour_daytype':'Month + hour + day type',
        'season_hour_daytype_temp5_wet':'Season + calendar + temperature + rain',
        'month_hour_daytype_temp5_wet':'Month + calendar + temperature + rain'}
    weather+=table(['Matching','Full difference','Leave-one-date-out range','Negative omissions'],[
        [label,f"{w['holiday'][k]['relative_difference_pct']:.1f}%",
         f"{w['holiday_leave_one_date_out'][k]['recomputed_support']['difference_min_pct']:.1f}% to {w['holiday_leave_one_date_out'][k]['recomputed_support']['difference_max_pct']:+.1f}%",
         f"{w['holiday_leave_one_date_out'][k]['recomputed_support']['negative_count']} / 17"] for k,label in holiday_labels.items()])
    weather+='''<p>The season-only holiday result can change sign when one date is removed; the sign flip persists when common-support cells are fixed (−16.0% to +0.7%). Month-and-weather matching remains negative, but retains only 372 of 408 holiday hours and 1,677 of 8,057 nonholiday hours. Holding support fixed across every weather-matched omission leaves just 130 holiday hours from 10 dates; its range is −16.7% to −7.4%. This supports event-specific review and additional years of holiday data, rather than a single fleet-reduction percentage.</p>'''
    forecast_start=body.index('<section class="finding" data-claim="scratch/model.py"><h2>The fitted model')
    body=body[:forecast_start]+weather+body[forecast_start:]

    model='''<section class="finding" data-claim="analyse/forecast-stress/scratch/forecast_stress.py"><h2>Calendar-aware recent demand is the strongest overall pilot candidate</h2>
<p><b>Forecast contract:</b> issue at 00:00 local time for hours 00–23 using only information already available. All counts through the preceding day are assumed finalized for the main comparison; reporting-delay scenarios are tested below. Target-day rentals and realized target-hour weather never enter deployable forecasts. Planned closures may override the forecast only when genuinely known in advance.</p>
<p>Five fixed candidates are evaluated on the same <b>5,561 operating hours from April through November</b>. Forecasts are generated forward from March; each fitted model trains only before its forecast month. All of these dates have already been examined during this assignment, so this is an exploratory retrospective comparison, not a new untouched holdout.</p>'''
    model+=table(['Candidate','Construction / update'],[
        ['Recent 7 days','Mean of the same hour over the preceding 7 calendar days, excluding closed observations.'],
        ['28-day weekday/weekend','Mean of the same hour and same weekday/weekend type over the preceding 28 calendar days.'],
        ['Previous 4 same weekdays','Mean of the same hour on the preceding 4 occurrences of the weekday.'],
        ['Monthly expanding model','Fixed histogram gradient boosting settings; refit on all eligible earlier history at each month start.'],
        ['Monthly 90-day model','Same settings/features; refit using eligible operating observations within the preceding 90 calendar days.']])
    model+='''<p>The fitted models use hour, weekday, month, annual sine/cosine and the holiday calendar, plus lagged counts: 24/48/168-hour lags, prior seven-day same-hour mean/standard deviation, prior four-week same-weekday/hour mean, and prior-day mean. Closed past hours are unavailable, not demand zeros. Empty baseline strata fall back to a past-only 28-day same-hour mean. No holiday-specific baseline reduction is fitted from these sparse holidays.</p>'''
    model+=table(['April–November','MAE','RMSE','WAPE','Bias','Month wins'],[
        [names[k],n(v['mae'],1),n(v['rmse'],1),f"{v['wape_pct']:.1f}%",f"{v['bias_pct']:+.1f}%",f"{f['monthly_wins'][k]}/8"] for k,v in f['pooled'].items()])
    model+='''<p>Errors are rentals/hour. The calendar-aware baseline has MAE <b>274.1</b>, compared with 292.2 for the seven-day baseline and 290.4 for monthly expanding training. The morning 06:00–09:59 error improves from 380.1 to 255.9 relative to the seven-day baseline. However, it wins only three of eight months; the seven-day baseline also wins three, and the expanding model wins two. In April–May, expanding training has lower MAE (331.2 versus 353.4). Keep both alternatives visible in shadow evaluation.</p>'''
    monthly_rows=[]
    for month in sorted({r['month'] for r in f['monthly']}):
        rows={r['model']:r for r in f['monthly'] if r['month']==month}
        monthly_rows.append([month]+[n(rows[k]['mae'],1) for k in names])
    model+=details('Monthly MAE for every candidate',table(['Month','7 days','Day type 28','Same weekday 4','Expanding','Rolling 90'],monthly_rows))
    model+='''<p>On the common October–November slice, monthly retraining yields MAE <b>191.1</b>, compared with 238.5 when the same model is frozen after August. The calendar-aware baseline scores <b>189.2</b>, but its +10.8% bias is less favorable than the retrained model’s +2.5%. Thus stale model weights explain part of the earlier comparison; the baseline’s small autumn error advantage does not establish a universal winner.</p>'''
    model+=table(['October–November','MAE','RMSE','Bias'],[[names[k],n(v['mae'],1),n(v['rmse'],1),f"{v['bias_pct']:+.1f}%"] for k,v in f['oct_nov'].items()])
    model+='''<p>Across April–November, the calendar-aware baseline’s paired MAE advantage is 18.2 rentals/hour over recent seven days and 16.3 over expanding training. Approximate seven-day-block bootstrap intervals are 0.8–39.6 and 0.05–37.6, respectively. Because the reference was selected on these scored dates, these intervals are conditional, exploratory and not adjusted for selection; the second barely excludes zero. <b>Recommend a pilot candidate, not proven statistical or operational superiority.</b></p>
<p>Realized-weather readings remain a diagnostic only: the original October–November comparator scored MAE 182.5 using weather from the rental hour. Archived forecasts issued at planning time are needed to establish achievable weather-aware accuracy.</p></section>'''

    model+='''<section class="finding" data-claim="analyse/forecast-stress/scratch/forecast_stress.py"><h2>Rolling buffers improve the trade-off, but miss some months and holidays</h2>
<p>Each hourly upper workload estimate adds a nonnegative 90th-percentile residual buffer to its point forecast. Residuals come from <b>earlier out-of-sample forecasts</b> whose outcomes are available before the current day. Compare three fixed recipes: March-only buffers by time block; preceding 28 days by block; and preceding 56 days by block × weekday/weekend. Sparse cells fall back to broader past-only groups. No buffer is tuned to hit 90% on the scored period.</p>'''
    recipes={'fixed_march_block':'Fixed March / block','rolling28_block':'Rolling 28 days / block','rolling56_block_daytype':'Rolling 56 days / block + day type'}
    model+=table(['28-day calendar baseline buffer','Coverage','Shortfall','Unused/hour','90% loss'],[
        [recipes[r['recipe']],f"{r['overall']['coverage_pct']:.2f}%",f"{r['overall']['shortfall_pct']:.2f}%",n(r['overall']['unused_headroom_mean']),n(r['overall']['pinball90'],1)]
        for r in f['envelopes'] if r['model']=='daytype28'])
    model+='''<p>The rolling 28-day recipe covers <b>90.3%</b> of operating hours, with a <b>1.49%</b> shortfall proxy and <b>381 rentals/hour</b> of unused headroom. It has the lowest 90th-percentile loss among the tested model/recipe combinations. This loss weights each unit of underprediction nine times each unit of overprediction; it is an illustrative loss function, not measured operator cost. Splitting buffers further by weekday/weekend over 56 days does not improve the pooled trade-off.</p>
<p>Coverage is the fraction of hours with rentals ≤ upper estimate. Shortfall is total positive (rentals − upper) divided by total rentals; unused headroom is mean positive (upper − rentals). These remain workload proxies, not stockouts, unused bicycles or a guaranteed customer-availability level.</p>'''
    model+=table(['Month','Hours','Rolling coverage','Shortfall'],[[r['month'],n(r['n']),f"{r['coverage_pct']:.1f}%",f"{r['shortfall_pct']:.2f}%"] for r in env['monthly']])
    group_rows=[]
    for label,key in [('Weekend','daytype'),('Holiday','holiday'),('Wet','rain')]:
        field={'daytype':'weekend','holiday':'holiday','rain':'wet'}[key]
        for r in env[key]:
            group_rows.append([label if r[field] else {'Weekend':'Weekday','Holiday':'Nonholiday','Wet':'Dry'}[label],n(r['n']),f"{r['coverage_pct']:.1f}%",f"{r['shortfall_pct']:.2f}%",n(r['unused_headroom_mean'])])
    morning=next(r for r in env['blocks'] if r['block']=='06–09')
    group_rows.append(['06:00–09:59',n(morning['n']),f"{morning['coverage_pct']:.1f}%",f"{morning['shortfall_pct']:.2f}%",n(morning['unused_headroom_mean'])])
    model+=table(['Slice','Hours','Coverage','Shortfall','Unused/hour'],group_rows)
    model+='''<p><b>Overall calibration hides material gaps:</b> August coverage is 80.4%, September 84.0%, and holiday coverage 80.2% across eight holiday dates. Wet-hour coverage is 99.8%, leaving 1,178 rentals/hour of unused headroom. The default therefore needs event and weather review; neither extra segmentation nor a historical 90% average is sufficient for autonomous resource allocation.</p>'''
    if 'post_closure' in env:
        model+=table(['Reopening slice','Hours','Coverage','Shortfall','Unused/hour'],[[('First 24 hours after reopening' if r['post_closure24'] else 'Other operating hours'),n(r['n']),f"{r['coverage_pct']:.1f}%",f"{r['shortfall_pct']:.2f}%",n(r['unused_headroom_mean'])] for r in env['post_closure']])
        model+='<p>The reopening envelope covers 91.3% of hours but leaves 521 rentals/hour of unused headroom, compared with 373 otherwise. Its coverage does not remove the need to review reopening forecasts and resource allocation.</p>'
    model+='</section>'

    model+='''<section class="finding" data-claim="scratch/closure_latency.py"><h2>Review reopening forecasts and enforce the actual data cutoff</h2>
<p>There are <b>12 reopening events</b> in April–November, contributing <b>288 operating hours</b> in the first 24 hours after a closed-to-open transition. Calendar-aware baseline error is higher in these hours. Comparing with normal hours matched to the reopening mix shows how much of the gap can reflect the calendar and weather.</p>'''
    model+=table(['Baseline comparison','Post-reopening hours','Post MAE','Matched normal MAE'],[
        [('Season + hour + day type' if r['matching']=='season+hour+weekend' else 'Also wet/dry'),n(r['matched_post_hours']),n(r['post_mae'],1),n(r['normal_mae_at_post_mix'],1)]
        for r in c['matched_closure'] if r['model']=='daytype28'])
    model+='''<p>Calendar matching gives 319.8 versus 242.7 rentals/hour of error. Adding wet/dry matching narrows this to <b>311.9 versus 287.7</b>, retaining 283 reopening hours. This does not isolate a causal closure effect or prove that missing history alone causes the errors. Flag reopening for manual review, retain older valid history, and monitor its errors separately; closure reasons and station inventories are needed to explain the residual.</p>
<p>Latency scenarios assume that an hour’s count is available only at the <b>end of the hour plus 1, 6 or 24 hours</b> of processing delay. Forecast issue stays at midnight. Both features and refit labels obey that cutoff. “Unadapted” fitted models learn from clean-history features but receive delayed features at scoring; “latency-trained” models use the same delayed feature construction during training and scoring.</p>'''
    latency_rows=[]
    for L in [0,1,6,24]:
        rows={r['model']:r for r in c['overall'] if r['delay_hours']==L}
        latency_rows.append([f'{L} hours',n(rows['recent7']['mae'],1),n(rows['daytype28']['mae'],1),n(rows['hgb_unadapted']['mae'],1),n(rows['hgb_latency_trained']['mae'],1)])
    model+=table(['Extra delay','7-day MAE','Day-type MAE','Fitted unadapted MAE','Latency-trained MAE'],latency_rows)
    model+='''<p>The calendar-aware baseline is relatively stable in these scenarios: MAE 274.1 with no extra delay and 278.7 with 24 hours. The expanding model moves from 290.4 to 317.5 unadapted, or 312.7 after latency-aware retraining. Shorter-delay effects are not monotonic, so this is not a universal degradation curve. Under a 24-hour delay, yesterday’s same-hour count and yesterday’s mean are unavailable throughout the forecast day; all-missing columns are removed when training that scenario. Baseline fallbacks remained finite in every tested case.</p>
<p>Intervention checks changed every target-day-and-later rental count and operating status and confirmed that the day’s feature values did not change at any tested latency. Availability assertions also verify every lag against its interval-end cutoff. <b>Actual ingestion timestamps are absent</b>: these tests establish code behavior under assumed delays, not the real pipeline’s latency or readiness.</p></section>'''

    scenario=f['dec1_scenario']
    model+='<section class="finding" data-claim="analyse/forecast-stress/scratch/forecast_stress.py"><h2>A historical next-day forecast separates Saturday demand from weekday demand</h2><p>For <b>1 December 2018</b>, assuming an operating nonholiday Saturday, the calendar-aware baseline predicts <b>'+n(scenario['daily_totals']['daytype28'])+'</b> daily rentals. This is a historical illustration beyond the file endpoint; there is no observed outcome to score and no present-day prediction.</p>'
    model+=table(['Hours inclusive','7-day mean/hour','Day-type mean/hour','Monthly model mean/hour'],[[r['block'],n(r['recent7']),n(r['daytype28']),n(r['hgb_expanding'])] for r in scenario['blocks']])
    model+='<p>The calendar-aware morning forecast is '+n(next(r['daytype28'] for r in scenario['blocks'] if r['block']=='06–09'))+' rentals/hour versus '+n(next(r['recent7'] for r in scenario['blocks'] if r['block']=='06–09'))+' from the baseline that mixes weekdays and weekends. Fitted-model values use the month-start refit stated in the methodology. These are block averages of hourly point forecasts, not fleet counts or block-capacity guarantees.</p></section>'

    start=body.index('<section class="finding" data-claim="scratch/model.py"><h2>The fitted model')
    end=body.index('<section class="rec">',start)
    body=body[:start]+model+body[end:]
    body=body.replace('<section class="rec"><h2>Fleet-planning recommendation</h2>\n<ul>',
        '<section class="rec"><h2>Fleet-planning recommendation</h2>\n<ul><li><b>Pilot the calendar-aware baseline with the rolling 28-day workload buffer.</b> Keep monthly expanding forecasts as a challenger, monitor seasonal bias, and require human review for holidays, rain and reopening. Validate this fixed choice on newly acquired dates before promotion.</li>')
    body=body.replace('Compare against the same recent-demand baseline each time.',
        'Compare against the same calendar-aware baseline each time and track first-day-after-reopening performance separately.')
    body=body.replace('If prior-day data are incomplete, delay issue or use an explicitly older cutoff and validated fallback.',
        'Use a measured ingestion cutoff. If counts are late, remove unavailable lags and use the tested past-only baseline fallback; repeat calibration under that actual latency.')
    body=body.replace('only one historical annual cycle is observed, and the final test is autumn.',
        'only one historical annual cycle is observed; forward evaluation covers April–November and has already been used to compare candidates.')
    body=body.replace('No independent winter or year-to-year test establishes',
        'No fresh confirmation period, independent winter or year-to-year test establishes')

    needs='''<h2>More data is still needed for operational validation and fleet sizing</h2>
<p>All four requested checks were completed with the supplied file. The following gaps cannot be resolved by more modeling of the same completed-rental counts.</p>'''
    needs+=table(['Additional data needed','What it would let us check','Current limit'],[
        ['Newer rentals and additional full years','Confirm the selected model/buffer on untouched dates, including winter and changing station coverage.','Current model selection and sensitivity intervals are retrospective; no validated present-day accuracy.'],
        ['Weather forecasts archived as issued, with issue time and horizon','Measure forecast-weather error and test a deployable weather-aware model.','Realized weather associations cannot be used as tested day-ahead inputs.'],
        ['Station inventory, dock capacity, departures/returns, trip durations, rejected attempts','Estimate bikes concurrently in use, unmet demand, station stockouts and rebalancing routes.','Hourly completed rentals do not identify fleet stock or availability.'],
        ['Holiday/event identities over multiple years; closure cause and schedule','Separate individual events, scheduled downtime and unexpected outages.','17 operating holiday dates and 12 evaluation reopening events support limited generalization.'],
        ['Record arrival/finalization times and weather-sensor quality metadata','Verify midnight availability, actual latency and zero-humidity coding.','1/6/24-hour delays are simulations; sensor anomalies remain unexplained.'],
        ['Relocation volumes, truck travel/loading times, repair workload and staff productivity','Convert workload forecasts into crew shifts, reserve costs and procurement decisions.','No defensible numeric fleet purchase or crew count can be inferred from this file.']])
    body=body.replace('<h2>Methodology and reproducibility</h2>',needs+'<h2>Methodology and reproducibility</h2>')
    start=body.index('<h2>Methodology and reproducibility</h2>')
    end=body.index('<h2>Question &amp; Framing</h2>',start)
    methods='''<h2>Methodology and reproducibility</h2><div class="method">
<p>Source: supplied <code>examples/seoul-bike-sharing-demand/question/data.csv</code>; attribution: <a href="https://doi.org/10.24432/C5F62R">Seoul Bike Sharing Demand (2020), UCI Machine Learning Repository</a>, CC BY 4.0. Metadata was opened on 5 November 2026 UTC for definitions; every empirical number comes from the local CSV. Source records are processed only in memory; saved outputs are aggregates.</p>
<p>Dates parse as day/month/year. Weekends are Saturday/Sunday, wet means rainfall &gt; 0, and all demand/error tables exclude nonfunctioning hours unless explicitly stated. Standardized weather/holiday means weight each retained common-support cell by its combined exposed/reference count. Five-degree temperature and 20-percentage-point humidity bins are defined in the saved instrument. Leave-one-holiday-date-out ranges recompute comparisons; fixed-support checks distinguish changes in cell coverage. These remain observational associations.</p>
<p>Forward predictions start in March; April–November evaluation uses 5,561 operating hours. Monthly model fits use earlier operating observations beginning 29 December 2017, or the most recent 90 days for the rolling candidate. Hyperparameters are fixed: 180 iterations, 15 leaves, learning rate 0.06, L2 10, leaf minimum 25, no early stopping, seed 42. Seven-day moving-block resampling uses 2,000 replicates. The baseline and buffer recommendations were selected from this retrospective comparison; no new untouched test is claimed.</p>
<p>Upper buffers use sorted residual rank min(n, ceil((n+1) × 0.90)); cells require at least 30 earlier out-of-sample errors, otherwise fall back to the same time block and then the broader past window. The 56-day recipe initially uses available history since March. All rows share the same scored hours. Coverage, positive shortfall, excess headroom and 90% pinball loss expose both undercapacity and overcapacity. Averages of hourly envelopes are not quantiles of multi-hour totals.</p>
<p>Reopening means the first 24 hours after a nonfunctioning-to-functioning transition. Calendar and wet/dry matched normal-hour error means are weighted to the reopening-hour mix. Delay scenarios enforce count-interval end plus processing delay ≤ forecast issue, including refit-label availability. They assume uniform delays and do not establish real arrival timing.</p>
<p>Instruments: <code>analyse/diagnostics/scratch/diagnose.py</code>, <code>analyse/forecast-stress/scratch/forecast_stress.py</code>, <code>analyse/weather-sensitivity/scratch/sensitivity.py</code>, and <code>scratch/closure_latency.py</code>; shared feature construction is in <code>scratch/forecast_common.py</code>. The original frozen-model comparison remains reproducible in <code>scratch/model.py</code>. Full commands, checks and missing-data requirements are in <code>methodology.md</code>. Charts and styling are embedded; no network or JavaScript is required.</p></div>'''
    body=body[:start]+methods+body[end:]
    body=body.replace('All supplied observations for diagnosis; July/August forward validation, September calibration, October/November final test.',
        'Full supplied year for diagnosis; monthly forward predictions from March, April–November retrospective comparison; original October/November split retained as a same-period reference.')
    body=body.replace('Midnight issue using finalized prior-day records, calendar and known schedule only; actual weather is diagnostic.',
        'Midnight issue with available past counts and calendar; test 1/6/24-hour processing delays. Known schedules only; actual weather remains diagnostic.')
    body=body.replace('Report with forecasts, forecast and operational proxy metrics, staffing/rebalancing recommendations, fleet-sizing requirements and drift plan.',
        'Report with forecasts and operational proxies, stronger model comparisons, sequential calibration, weather/holiday sensitivity, closure/latency checks, recommendations and explicit additional-data needs.')
    body=body.replace('</div><div class="foot">',
        '<p><b>Additional requested scope:</b> complete the four robustness checks described above and state what still needs more data.</p></div><div class="foot">')
    return body
