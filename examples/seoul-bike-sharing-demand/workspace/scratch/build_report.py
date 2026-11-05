"""Assemble the report from aggregate instruments and the repository shell."""
from pathlib import Path
import html
import importlib.util
import json

RUN = Path(__file__).resolve().parents[1]
REPO = RUN.parents[2]
D = json.loads((RUN/'analyse/diagnostics/scratch/diagnostics.json').read_text())
M = json.loads((RUN/'scratch/model_results.json').read_text())
e = html.escape
def n(x, digits=0):
    return f'{x:,.{digits}f}'
def table(headers, rows):
    return '<table class="bridge"><thead><tr>'+''.join(f'<th>{e(str(h))}</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{e(str(v))}</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
def details(title, body):
    return f'<details><summary>{e(title)}</summary>{body}</details>'

specs = [
    {'id':'hourly','form':'line','title':'Weekdays have two pronounced rental peaks',
     'subtitle':'Mean completed rentals per operating hour; all seasons',
     'width':760,'height':350,'x':[f'{h:02d}' for h in range(24)],
     'y_domain':[0,2000], 'y_ticks':4,'value_format':'{:,.0f}',
     'series':[{'name':day,'color':color,'label':'none','values':[r['mean'] for r in D['hour_daytype'] if r['daytype']==day]} for day,color in [('Weekday','blue'),('Weekend','aqua')]]},
    {'id':'seasons','form':'hbar','title':'Summer rental throughput is 4.6 times winter',
     'subtitle':'Completed rentals per operating hour; closures excluded',
     'width':760,'value_format':'{:,.0f}',
     'rows':[{'label':r['season'],'value':r['mean'],'color':'blue'} for r in D['season']]}
]
(RUN/'scratch/chart_specs.json').write_text(json.dumps(specs,indent=2))
spec = importlib.util.spec_from_file_location('renderer', REPO/'.claude/skills/dataviz/scripts/render.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
(RUN/'scratch/charts').mkdir(exist_ok=True)
charts={}
for s in specs:
    s['single_mode']='light'
    charts[s['id']]=renderer.render_chart(s)
    (RUN/f"scratch/charts/{s['id']}.svg").write_text(charts[s['id']])

body = '''
<div class="kicker">Fleet availability • historical planning study</div>
<h1>Staff the seasonal peaks; keep the forecast simple until weather is usable</h1>
<div class="byline">Seoul bike sharing · 1 December 2017–30 November 2018 · prepared 4 November 2026</div>
<section class="bottomline"><b>Prioritize weekday commute coverage, with stronger evening operations outside winter and an earlier winter focus.</b>
Summer operating-hour rentals average 1,034 versus 226 in winter, but demand patterns alone cannot determine fleet size.
Use recent hourly demand as the initial planning benchmark: its final-test error is 234 rentals/hour, slightly better than the fitted model’s 239; both need weather-aware review before operational use.</section>
<p>This report diagnoses completed rentals, tests a midnight-issued forecast for the coming day, and translates the results into staffing and rebalancing decisions. It is a historical assignment, not a forecast for present-day Seoul.</p>
<section class="finding" data-claim="analyse/diagnostics/scratch/diagnose.py">
<h2>Operating hours reveal the demand pattern; closures conceal it</h2>
<p>The file contains <span class="num">6,172,314 rentals across 8,760 hours</span>, with a complete hourly grid over 365 days. There are no duplicate date/hour keys, missing values, negative rental counts, or zero-rental operating hours. All 295 nonfunctioning hours have zero rentals: 12 entire days and one partial day. Those zeros describe service status, not proof that nobody wanted a bike.</p>
'''
body += table(['Service status','Hours','Rentals','Mean/hour'],[[r['functioning'],n(r['hours']),n(r['rentals']),n(r['mean'],1)] for r in D['status']])
body += '<p>All demand summaries below exclude closed hours. Across the full file, counting closures lowers the average from 729 to 705 rentals/hour. In autumn, the same denominator change lowers 924 to 820. The dataset does not identify closure causes or whether each closure was scheduled.</p></section>'
body += '<section class="finding" data-claim="analyse/diagnostics/scratch/diagnose.py"><h2>Peak timing changes with season and day of week</h2><figure class="fig" style="--weekday:#2a78d6;--weekend:#1baf7a">'+charts['hourly']+'<figcaption><span aria-hidden="true" style="display:inline-block;width:16px;height:4px;background:var(--weekday);vertical-align:middle"></span> Weekday &nbsp; <span aria-hidden="true" style="display:inline-block;width:16px;height:4px;background:var(--weekend);vertical-align:middle"></span> Weekend<br>Hour labels use the dataset’s local clock. Weekday means include weekday holidays; holiday effects are examined separately below.</figcaption></figure>'
body += '<p>Weekday 08:00 averages <b>1,306 rentals/hour</b>, versus 421 on weekends; weekday 18:00 averages <b>1,724</b>. Weekday 02:00–05:59 averages only <b>182</b>. Weekend demand builds later, so a weekday-only staffing schedule would allocate effort at the wrong time.</p>'
hour_rows=[]
for h in range(24):
    a,b=[next(r for r in D['hour_daytype'] if r['hour']==h and r['daytype']==day) for day in ['Weekday','Weekend']]
    hour_rows.append([f'{h:02d}:00',n(a['mean'],1),n(a['hours']),n(b['mean'],1),n(b['hours'])])
body += details('Hourly chart data: means and operating-hour sample sizes',table(['Hour','Weekday mean','n','Weekend mean','n'],hour_rows))
body += '<figure class="fig">'+charts['seasons']+'<figcaption>Each season is observed once. Temperature, daylight, calendar and any fleet changes are not separable causal effects here.</figcaption></figure>'
body += table(['Season','Open hours','Mean/hour','90th percentile'],[[r['season'],n(r['hours']),n(r['mean'],1),n(r['p90'],1)] for r in D['season']])
body += table(['Season','Day type','Peak hour','Mean at peak','n'],[[r['season'],r['daytype'],f"{r['hour']:02d}:00",n(r['mean']),n(r['hours'])] for r in D['hourly_peaks_by_season_daytype']])
body += '<p><b>The staffing flip test matters:</b> winter weekdays peak at 08:00, while spring, summer and autumn peak at 18:00. Summer weekends peak at 20:00, versus 15:00 in winter. These are average peak hours, not guaranteed daily maxima.</p></section>'

body += '<section class="finding" data-claim="analyse/diagnostics/scratch/diagnose.py"><h2>Rain matters strongly; the raw holiday discount is misleading</h2>'
body += table(['Condition','Open hours','Mean rentals/hour'],[[r['wet'],n(r['hours']),n(r['mean'],1)] for r in D['rain']]+[[r['snow_status'],n(r['hours']),n(r['mean'],1)] for r in D['snow']]+[[r['holiday'],n(r['hours']),n(r['mean'],1)] for r in D['holiday']])
body += '<p>Wet hours average <b>167</b> rentals versus <b>766</b> in dry hours. Standardizing within season × hour × weekday/weekend cells gives <b>153.6 versus 884.4</b>, an 82.6% gap; matching by month instead gives an 84.0% gap. This remains an association: rain timing, temperature and other factors are not randomized.</p><p>The evening peak also weakens in rain. On summer weekdays, 17:00–19:59 averages <b>2,120 in dry hours versus 569 in wet hours</b> (174 and 24 hours); in autumn it is 1,868 versus 63 (164 and only 7 hours). Keep reserve crews flexible and avoid applying a universal rain multiplier.</p>'
body += '<p>Holidays average 529 rentals/hour versus 739 otherwise, a raw <b>28.4% discount</b>. After matching season, hour and weekend status, the comparison is 661 versus 713, only <b>7.3% lower</b>; month matching gives 13.3% lower. There are only 17 operating holiday dates. A blanket 28% holiday fleet reduction would overstate the evidence.</p>'
body += table(['Temperature','Open hours','Mean/hour'],[[r['temperature'],n(r['hours']),n(r['mean'],1)] for r in D['temperature']])
weather_names={'temperature':'Temperature (°C)','humidity':'Humidity (%)','wind_speed':'Wind (m/s)','visibility':'Visibility (10 m)','dew_point':'Dew point (°C)','solar_radiation':'Solar radiation (MJ/m²)','rainfall':'Rainfall (mm)','snowfall':'Snowfall (cm)'}
body += details('Other weather signals and interpretation',table(['Measured variable','Pearson correlation with rentals'],[[weather_names[k],f'{v:+.3f}'] for k,v in D['weather_correlations'].items()])+'<p>All correlations use 8,465 operating hours and are descriptive, unadjusted associations. Positive wind and solar correlations can reflect time-of-day and season; they do not justify increasing supply when wind rises. Rainfall’s weak linear correlation does not contradict the large wet/dry difference: most hours have zero rain. Temperature and dew point overlap; avoid interpreting correlated predictors as independent drivers. Seventeen observations record zero humidity and need a sensor/coding check before weather deployment. The deployable models do not use those weather readings.</p>')
body += '</section>'

body += '''<section class="finding" data-claim="scratch/model.py"><h2>The fitted model has no clear advantage over recent demand</h2>
<p><b>Forecast contract:</b> at 00:00 local time, forecast every hour of that day using records finalized through the prior day. This assumes the previous day’s final hour is available at issue time; a real pipeline with delay must shift the cutoff and repeat the backtest. No target-day rentals enter that day’s features.</p>'''
body += table(['Predictors / rule','Known at issue time?','Treatment'],[
 ['Hour, weekday, month, annual sine/cosine, holiday calendar','Yes, assuming published calendar','Calendar/history model'],
 ['Same-hour rentals 1, 2 and 7 days ago; prior 7-day hourly mean/std; prior 4-week weekday mean; previous-day mean','Yes, after data finalization','Closed past hours treated as unavailable; missing lags handled by model'],
 ['Recent-seven-day mean at the same hour','Yes','Simple benchmark; exclude closed past hours'],
 ['Same hour one week ago','Yes','Baseline; fall back to recent-seven-day mean if previous week was closed'],
 ['Planned operating status','Only if schedule is genuinely known','Override to zero only for confirmed closures; historical status is not a forecast'],
 ['Target-hour temperature, humidity, wind, visibility, dew point, solar, rain, snow','No','Only in observed-weather diagnostic comparator; archived issued forecasts are absent']])
body += '<p>The fitted model is histogram gradient boosting with squared-error loss, 180 iterations, 15 leaves, learning rate 0.06 and regularization. Expanding training windows predict July and August separately. Pooled validation MAE selects the calendar/history model at <b>261.0</b> versus <b>266.8</b> for recent demand. It is then fit through August and frozen; September calibrates upper buffers and October–November remain the final test. History features still refresh daily. This is a sequence of midnight forecasts, not a two-month forecast issued in September.</p>'
labels={'prior_week':'Prior week, same hour','recent_7_days':'Recent 7-day hourly mean','calendar_history':'Calendar + history model','observed_weather_oracle':'Observed-weather comparator'}
body += table(['Final test: open hours','MAE','RMSE','WAPE','Bias'],[[labels[k],n(v['mae'],1),n(v['rmse'],1),f"{v['wape_pct']:.1f}%",f"{v['bias_pct']:+.1f}%"] for k,v in M['test'].items()])
body += '<p>All models face the same <b>1,313 operating test hours</b>, with 1,116,390 completed rentals. Errors are rentals/hour; WAPE is total absolute error divided by total rentals, and bias is total forecast minus actual divided by actual. The recent-demand baseline wins MAE (233.8 versus 238.5), while the fitted model wins RMSE (349.3 versus 377.0), meaning it reduces some larger errors. A seven-day-block bootstrap puts fitted-model MAE improvement over the baseline at <b>−4.7 rentals/hour</b>, with an approximate 95% interval of <b>−61.5 to +51.6</b>; superiority is not established.</p>'
body += '<p><b>Recommendation:</b> keep recent demand as the transparent planning benchmark and the fitted model in shadow evaluation. Do not switch models based on this small difference or call the test a second tuning set. Before promotion, collect a fresh period and agree whether average error, severe shortfalls or staffing cost is the objective.</p><p>The observed-weather comparator reaches MAE 182.5, but uses weather measured during the target hour and has +15.6% bias. It demonstrates a potentially useful signal, not deployable accuracy or a guaranteed performance bound. A weather model must be trained and tested on forecasts archived at the actual issue time.</p>'
body += details('Chronological validation by month',table(['Month','Model','MAE','WAPE'],[[r['month'],labels[r['model']],n(r['mae'],1),f"{r['wape_pct']:.1f}%"] for r in M['validation']]))
body += '</section>'

body += '<section class="finding" data-claim="scratch/model.py"><h2>High envelope coverage comes with costly excess headroom</h2><p>For each of five time blocks, take the September 90th-percentile upper residual using rank ceil((n + 1) × 0.90), then add it to each hourly point forecast, never going below that point. These are <b>trial hourly workload envelopes</b>. Temporal dependence and seasonal drift mean they do not carry a guaranteed 90% future coverage claim, and neither forecast coverage nor the shortfall proxy measures customer bike availability.</p>'
body += table(['Test envelope','Mean point','Mean upper','Hours covered','Shortfall proxy','Unused/hour'],[[label,n(v['predicted_mean']),n(v['upper_mean']),f"{v['coverage_pct']:.1f}%",f"{v['shortfall_pct']:.2f}%",n(v['unused_headroom_mean'])] for label,v in [('Recent demand',M['baseline_envelope']['all']),('Calendar/history',M['planning_all'])]])
body += '<p>Coverage = fraction of hours with observed rentals at or below the envelope. Shortfall proxy = sum of positive (rentals − envelope) divided by observed rentals. Unused headroom = average positive (envelope − rentals), not measured idle bicycles. The recent-demand envelope covers <b>97.4%</b> of hours but leaves <b>598 rentals/hour</b> of unused headroom. Fixed September buffers overcover the cooler final period; copying them into staffing or procurement would be wasteful.</p>'
body += table(['Time block','n','Actual mean','Recent-demand point','Trial upper','Coverage'],[[r['block'],n(r['n']),n(r['actual_mean']),n(r['predicted_mean']),n(r['upper_mean']),f"{r['coverage_pct']:.1f}%"] for r in M['baseline_envelope']['blocks']])
body += '<p>Values in this table average separate hourly forecasts within each block; they are not a constant block capacity or a quantile of the block’s total. For the fitted model, October bias is −14.9% and November bias +9.7%; rainy-hour MAE is 660 across 50 hours. Its holiday envelope covers just 66.7% of 24 holiday hours (one date), despite high overall coverage. Review event days individually and recalibrate using only already completed dates.</p>'
body += '</section>'

body += '<section class="finding" data-claim="scratch/model.py"><h2>A historical next-day example makes the forecast usable</h2><p>Issued at midnight on <b>1 December 2018</b>, assuming normal operation and a nonholiday Saturday, the recent-demand forecast totals <b>'+n(M['next_day_scenario']['baseline_total'])+'</b> rentals; the frozen fitted model totals <b>'+n(M['next_day_scenario']['total_point'])+'</b>. These are illustrative forecasts beyond the file endpoint, with no observed outcome available for scoring.</p>'
body += table(['Hours inclusive','Recent-demand mean/hour','Fitted mean/hour','Trial baseline upper/hour'],[[r['block'],n(r['baseline_per_hour']),n(r['point_per_hour']),n(r['baseline_upper_per_hour'])] for r in M['next_day_scenario']['blocks']])
body += '<p>The last column averages provisional September-calibrated hourly envelopes; it is not a 90th-percentile total or a recommended number of bikes. The baseline mixes weekdays and weekends, a limitation most visible in the morning. Review Saturday demand shape and weather before allocating staff; a weekday-aware replacement needs fresh validation.</p></section>'

body += '''<section class="rec"><h2>Fleet-planning recommendation</h2>
<ul>
<li><b>Rebalance before the demand arrives.</b> Pilot a pre-07:00 weekday readiness check and pre-17:00 replenishment in spring, summer and autumn; prioritize readiness before 08:00 in winter. Use station-level outbound and return patterns to decide truck routes and dock capacity. The citywide data establish timing, not origins and destinations.</li>
<li><b>Shift flexible staffing by season and day type.</b> Retain coverage into summer weekend evenings; winter weekends need an earlier afternoon emphasis. Allocate maintenance and repairs preferentially to 02:00–05:59, subject to safety and labor constraints, while preserving a core service.</li>
<li><b>Use weather and events for reviewed adjustments.</b> Prepare a wet-weather roster with reserve staff that can return when conditions change. Avoid a blanket holiday reduction; check event calendars and demand on comparable dates. Scheduled closures have a separate operations workflow, not a low-demand forecast.</li>
<li><b>Pilot service targets before expanding the fleet.</b> Use station stockout minutes, full-dock minutes, unserved requests, and rebalancing moves per staff-hour to judge availability and cost. Treat 90% hourly workload coverage only as a trial forecast target; choose a customer-availability target and budget with the operator.</li>
<li><b>Defer a numeric fleet purchase or crew count.</b> Hourly rentals are flows; the same bike can be rented repeatedly. Estimate bikes concurrently in use from departures and trip duration, then add idle bikes required at stations, imbalance reserves and maintenance stock. Crew sizing additionally needs relocation volumes, travel/loading time and measured productivity. None of those inputs is in this file. A 4.6× summer/winter rental ratio is not a 4.6× fleet requirement.</li>
</ul></section>
<h2>Watch items that could change the decision</h2>
<ul>
<li><b>Demand censored by supply:</b> completed rentals miss failed attempts and empty/full stations. A low forecast can perpetuate shortages. Log unserved demand and station inventory alongside rentals; distinguish capacity restrictions from preference changes.</li>
<li><b>Drift:</b> store forecast issue time, input cutoff, model version and forecast as issued. Report rolling weekly and four-week MAE, WAPE and signed bias, plus peak-hour, wet/dry, holiday and station slices. Compare against the same recent-demand baseline each time. Avoid MAPE because closures are zeros and low-volume hours make percentage errors unstable.</li>
<li><b>Coverage and cost:</b> monitor envelope exceedance, shortfall proxy, and unused headroom together. Review both undercoverage and sustained overcoverage. Recalibrate with completed past dates and test the new rule on a fresh forward window; do not tune using the scored horizon.</li>
<li><b>Illustrative alert policy:</b> review a model after two consecutive weekly WAPE readings above 35%, absolute bias above 10%, or four-week envelope coverage outside 85–95%. These are proposed starting thresholds, not estimated optima; require adequate sample size and separate holiday/event review. Alerts should trigger diagnosis, not automatic fleet cuts.</li>
<li><b>Changing inputs:</b> watch late rental logs, missing lags, closure frequency, weather missingness and out-of-range readings, holidays, station additions and pricing changes. If prior-day data are incomplete, delay issue or use an explicitly older cutoff and validated fallback. Check the 17 zero-humidity readings before adopting weather features.</li>
<li><b>Generalization:</b> only one historical annual cycle is observed, and the final test is autumn. No independent winter or year-to-year test establishes that these accuracy figures transfer to another season or to today. Revalidate on current operations before using the recommendations for procurement.</li>
</ul>
<h2>Methodology and reproducibility</h2>
<div class="method"><p>Input: the supplied <code>examples/seoul-bike-sharing-demand/question/data.csv</code>. Source attribution: <a href="https://doi.org/10.24432/C5F62R">Seoul Bike Sharing Demand (2020), UCI Machine Learning Repository</a>, CC BY 4.0. Canonical metadata was opened on 5 November 2026 UTC for definitions and units; all reported empirical numbers were recomputed from the local file. No external benchmark was substituted.</p>
<p>Dates parse as day/month/year. Weekends are Saturday and Sunday. Wet means rainfall &gt; 0; snow means recorded snowfall &gt; 0. Means and quantiles weight each operating hour equally. Weather/holiday standardization retains only cells containing both categories and weights both cell means by the combined cell count: 144 season/hour/day-type common cells for rain (516 wet and 6,087 dry hours) and 144 for holidays (408 holiday and 6,809 nonholiday hours). These reduce calendar confounding but do not identify causal effects. Month-level alternatives are sensitivity checks.</p>
<p>Training drops the first 28 days to initialize history; the final fit uses 5,856 operating hours from 29 December 2017 through 31 August 2018. September has 624 operating calibration hours. Test dates contain 1,464 total hours, including 151 nonfunctioning hours. A known-closure override reduces all-hour MAE for the fitted model to 213.9, but that easier scenario is not the headline score. The all-operating evaluation avoids credit for hindsight closure labels.</p>
<p>Seven-day moving-block resampling uses 2,000 replicates of the final-test daily error differences; its interval is conditional on these fitted models and this limited period. No random train/test split or target-hour weather enters the deployable forecast. Hourly target counts are processed only in memory; saved results are aggregate tables. Seasonal/daily totals and independently regrouped forecast errors reconcile.</p>
<p>Reproduction instructions, exact hyperparameters and checks are in <code>methodology.md</code>; executable instruments are <code>scratch/model.py</code> and <code>analyse/diagnostics/scratch/diagnose.py</code>. This HTML embeds its charts and styling and requires no network or JavaScript to read.</p></div>
<h2>Question &amp; Framing</h2>
<div class="method"><p><b>As asked:</b> advise a city bike-share operator on fleet availability; diagnose demand by hour, season, weather, holiday and functioning-day status; build a rental-count forecast with clear deployment-time predictors; recommend service-level, staffing or rebalancing actions; explain planning pitfalls and drift monitoring.</p>'''
body += table(['Framing decision','Resolved as'],[
 ['Period','All supplied observations for diagnosis; July/August forward validation, September calibration, October/November final test.'],
 ['Target','Systemwide hourly completed rentals conditional on operation; workload envelope and shortfall proxy, not unconstrained requests or concurrent bike stock.'],
 ['Deployment','Midnight issue using finalized prior-day records, calendar and known schedule only; actual weather is diagnostic.'],
 ['Deliverable','Report with forecasts, forecast and operational proxy metrics, staffing/rebalancing recommendations, fleet-sizing requirements and drift plan.']])
body += '</div><div class="foot">Historical observational evidence • limited holiday samples • no station inventory or trip durations</div>'

from followup_sections import revise
body=revise(body,RUN,table,details,n)
shell=(REPO/'.claude/skills/analyse/assets/brief_template.html').read_text()
head=shell[shell.index('<html lang='):shell.index('<body>')]
head=head.replace('<!-- SUBJECT --> - brief','Seoul bike demand — fleet planning report')
# Preserve shell CSS, with small native details/table additions for long support tables.
head=head.replace('</style>','details { margin: 12px 0; } summary { cursor: pointer; color: var(--accent); font-size: 14px; } td { font-variant-numeric: tabular-nums; } @media print { details > * { display: block; } }\n</style>')
(RUN/'brief.html').write_text('<!DOCTYPE html>\n'+head+'<body><main class="page">'+body+'</main></body></html>')
print('Built brief.html with two embedded charts and aggregate evidence tables.')
