from pathlib import Path
import duckdb,json,subprocess
R=Path(__file__).resolve().parents[1]; S=R/'scratch'
SRC=Path('/hal-light/examples/seoul-bike-sharing-demand/question')
if not (R/'prompt.md').exists():
 (R/'prompt.md').write_text('# Original user request\n\nsequentially, run hal_light in a subagent for each of these assignments /hal-light/examples\n\n# Assignment\n\n'+(SRC/'BRIEF.md').read_text()+'\n# User steers — 2026-11-04\n\nyou can run 2 at a time I think\n\nno the idea is to do the homework from the data supplied, not lookup what actually happened\n')
def log(t):
 stamp=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
 with (R/'run_log.md').open('a') as f:f.write('\n## '+stamp+'\n'+t+'\n')
if not (R/'run_log.md').exists():
 log('Framing contract: estimand is network hourly observed rentals conditional on scheduled operation, forecast one day ahead using only information available before that day. Population: supplied Seoul hourly file, all dates; closure hours reported separately. Comparison: chronological walk-forward forecasts versus last-week and recent-hour baselines, tuning June–August and final September–November. Decision surface: hourly/season/weather/holiday/closure diagnostics; deployable prediction rule with aggregate held-out errors, service envelope validation, staffing/rebalancing recommendation, limits and drift monitoring. Rival: static seasonal averages may appear accurate only because future season/weather leaks into the model; use recent-history calendar-only forecasts and compare horizons. Flip test: test peak-hour prioritization separately by season and workday/weekend, and test whether a historical 90th-percentile envelope actually covers 90% of future hours. No KB configured; SOURCE and BRIEF read. All input records remain inside in-memory DuckDB, only aggregates exported. No external information fetched.')
c=duckdb.connect()
print(c.execute(f"DESCRIBE SELECT * FROM read_csv_auto('{SRC/'data.csv'}')").fetchall())
queries={}
def query(name,sql):
 (S/(name+'.sql')).write_text(sql+';\n')
 rel=c.execute(sql); cols=[x[0] for x in rel.description]; rows=[dict(zip(cols,r)) for r in rel.fetchall()]
 queries[name]=rows; return rows
setup=f'''CREATE TEMP VIEW raw AS SELECT * FROM read_csv_auto('{SRC/'data.csv'}', all_varchar=true);
CREATE TEMP VIEW hours AS SELECT strptime("Date",'%d/%m/%Y')::DATE d,"Hour"::INT h,"Rented Bike Count"::DOUBLE y,
"Temperature"::DOUBLE temperature,"Humidity"::DOUBLE humidity,"Wind speed"::DOUBLE wind,"Visibility"::DOUBLE visibility,
"Dew point temperature"::DOUBLE dew,"Solar Radiation"::DOUBLE solar,"Rainfall"::DOUBLE rain,"Snowfall"::DOUBLE snow,
"Seasons" season, "Holiday" holiday, "Functioning Day"='Yes' functioning,
CASE WHEN dayofweek(strptime("Date",'%d/%m/%Y')) IN (0,6) OR "Holiday"='Holiday' THEN 'Off day' ELSE 'Workday' END daytype
FROM raw;'''
(S/'setup.sql').write_text(setup);c.execute(setup)
query('quality',"""SELECT count(*) n,min(d) start_date,max(d) finish,count(distinct d) day_count,sum(y) rentals,
count(*)-count(distinct(d,h)) duplicate_hours,sum(CASE WHEN NOT functioning THEN 1 ELSE 0 END) closed_hours,
sum(CASE WHEN NOT functioning THEN y ELSE 0 END) closed_rentals,
sum(CASE WHEN y<0 OR h NOT BETWEEN 0 AND 23 THEN 1 ELSE 0 END) invalid,
sum(CASE WHEN d IS NULL OR h IS NULL OR y IS NULL OR temperature IS NULL OR rain IS NULL OR functioning IS NULL THEN 1 ELSE 0 END) core_nulls FROM hours""")
for name,dim in [('hour','h'),('season','season'),('holiday','holiday'),('functioning','functioning'),('month',"strftime(d,'%Y-%m')"),('daytype','daytype')]:
 query(name,f"SELECT {dim} dimension, count(*) hour_count,sum(y) rentals,avg(y) mean,quantile_cont(y,.9) p90 FROM hours {'WHERE functioning' if name!='functioning' else ''} GROUP BY 1 ORDER BY 1")
query('hour_by_daytype','SELECT h,daytype,count(*) n,avg(y) mean,quantile_cont(y,.9) p90 FROM hours WHERE functioning GROUP BY 1,2 ORDER BY 1,2')
query('season_peak',"""WITH g AS (SELECT season,daytype,h,avg(y) mean,count(*) n FROM hours WHERE functioning GROUP BY ALL), ranked AS (SELECT *,row_number() over(partition by season,daytype order by mean desc) r FROM g) SELECT season,daytype,h,mean,n FROM ranked WHERE r=1 ORDER BY 1,2""")
for name,dim in [('temperature',"CASE WHEN temperature<0 THEN '<0 C' WHEN temperature<10 THEN '0–<10 C' WHEN temperature<20 THEN '10–<20 C' WHEN temperature<30 THEN '20–<30 C' ELSE '30+ C' END"),('rain',"CASE WHEN rain>0 THEN 'Rain' ELSE 'Dry' END"),('snow',"CASE WHEN snow>0 THEN 'Snow' ELSE 'No snow' END"),('humidity',"CASE WHEN humidity<40 THEN '<40%' WHEN humidity<70 THEN '40–<70%' ELSE '70+%' END"),('wind',"CASE WHEN wind<2 THEN '<2 m/s' WHEN wind<4 THEN '2–<4 m/s' ELSE '4+ m/s' END")]:
 query(name,f"SELECT {dim} dimension,count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY 1 ORDER BY 1")
query('rain_standardized',"""WITH g AS (SELECT season,h,daytype, rain>0 wet, count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY ALL), cells AS(SELECT a.season,a.h,a.daytype,a.n dry_n,b.n wet_n,a.mean dry_mean,b.mean wet_mean FROM g a JOIN g b USING(season,h,daytype) WHERE NOT a.wet AND b.wet AND a.n>=3 AND b.n>=3) SELECT count(*) cells,sum(dry_n) dry_n,sum(wet_n) wet_n,sum(dry_mean*wet_n)/sum(wet_n) matched_dry,sum(wet_mean*wet_n)/sum(wet_n) wet FROM cells""")
query('holiday_standardized',"""WITH g AS (SELECT season,h,holiday='Holiday' hol,count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY ALL), cells AS(SELECT a.n normal_n,b.n holiday_n,a.mean normal_mean,b.mean holiday_mean FROM g a JOIN g b USING(season,h) WHERE NOT a.hol AND b.hol AND a.n>=3 AND b.n>=3) SELECT count(*) cells,sum(holiday_n) holiday_n,sum(normal_mean*holiday_n)/sum(holiday_n) matched_normal,sum(holiday_mean*holiday_n)/sum(holiday_n) holiday FROM cells""")
# Calendar-only forecasts computed solely from prior functioning days. Forecast fixed at midnight.
forecast='''CREATE TEMP VIEW forecasts AS
SELECT t.*, CASE WHEN t.d<DATE '2018-09-01' THEN 'Validation Jun–Aug' ELSE 'Test Sep–Nov' END split,
p.p7,p.p28,p.p56,p.q28,p.q56,p.n28,p.n56,
CASE WHEN l.functioning THEN l.y ELSE p.p28 END lag7
FROM hours t
LEFT JOIN LATERAL (SELECT
avg(y) FILTER(WHERE d>=t.d-7) p7,
avg(y) FILTER(WHERE d>=t.d-28 AND daytype=t.daytype) p28,
avg(y) FILTER(WHERE daytype=t.daytype) p56,
quantile_cont(y,.9) FILTER(WHERE d>=t.d-28 AND daytype=t.daytype) q28,
quantile_cont(y,.9) FILTER(WHERE daytype=t.daytype) q56,
count(*) FILTER(WHERE d>=t.d-28 AND daytype=t.daytype) n28,
count(*) FILTER(WHERE daytype=t.daytype) n56
FROM hours WHERE d<t.d AND d>=t.d-56 AND h=t.h AND functioning) p ON true
LEFT JOIN hours l ON l.d=t.d-7 AND l.h=t.h
WHERE t.d>=DATE '2018-06-01';
CREATE TEMP VIEW scored AS SELECT f.*,v.model,v.pred,
CASE WHEN NOT functioning THEN 0 ELSE v.pred END schedule_pred
FROM forecasts f,LATERAL (VALUES ('Last week',lag7),('Past 7d hour',p7),('Past 28d hour/daytype',p28),('Past 56d hour/daytype',p56)) v(model,pred);'''
(S/'forecast.sql').write_text(forecast);c.execute(forecast)
metrics="count(*) n,avg(abs(y-pred)) mae,sqrt(avg((y-pred)^2)) rmse,sum(abs(y-pred))/sum(y) wape,sum(pred-y)/sum(y) bias"
query('model_metrics',f'SELECT split,model,{metrics} FROM scored WHERE functioning GROUP BY 1,2 ORDER BY 1,mae')
query('schedule_metrics','SELECT split,model,count(*) n,avg(abs(y-schedule_pred)) mae,sqrt(avg((y-schedule_pred)^2)) rmse,sum(abs(y-schedule_pred))/sum(y) wape FROM scored GROUP BY 1,2 ORDER BY 1,mae')
# Selection only from validation data, before looking at final holdout model ranking.
validation=[r for r in queries['model_metrics'] if r['split'].startswith('Validation')]
best=min(validation,key=lambda r:r['mae'])['model']
query('selected_months',f"SELECT strftime(d,'%Y-%m') period,{metrics} FROM scored WHERE functioning AND model='{best}' GROUP BY 1 ORDER BY 1")
query('selected_hour',f"SELECT h,{metrics},avg(y) actual,avg(pred) predicted FROM scored WHERE functioning AND d>=DATE '2018-09-01' AND model='{best}' GROUP BY 1 ORDER BY 1")
query('selected_daytype',f"SELECT daytype,{metrics} FROM scored WHERE functioning AND d>=DATE '2018-09-01' AND model='{best}' GROUP BY 1 ORDER BY 1")
query('selected_rain',f"SELECT CASE WHEN rain>0 THEN 'Rain' ELSE 'Dry' END weather,{metrics} FROM scored WHERE functioning AND d>=DATE '2018-09-01' AND model='{best}' GROUP BY 1 ORDER BY 1")
query('envelope',"SELECT split,count(*) n,avg((y<=q28)::INT) coverage28,avg((y<=q56)::INT) coverage56,avg(greatest(y-q28,0)) exceedance28,avg(greatest(q28-y,0)) slack28,avg(n28) history28,min(n28) min_history28 FROM forecasts WHERE functioning GROUP BY 1 ORDER BY 1")
query('envelope_by_hour','SELECT h,count(*) n,avg((y<=q28)::INT) coverage28,avg(q28) planning_bound,avg(y) mean FROM forecasts WHERE functioning AND d>=DATE \'2018-09-01\' GROUP BY 1 ORDER BY 1')
# Prediction demonstration: the next day beyond source end, using last 28 days of available history.
query('next_day',"""SELECT h,count(*) n,avg(y) forecast,quantile_cont(y,.9) historical_p90 FROM hours WHERE functioning AND d>=DATE '2018-11-03' AND d<DATE '2018-12-01' AND daytype='Off day' GROUP BY h ORDER BY h""")
query('independent_total','SELECT sum(rentals) total,sum(n) n FROM (SELECT season,h,count(*) n,sum(y) rentals FROM hours GROUP BY 1,2)')
query('independent_mae',f"SELECT sum(ae)/sum(n) mae,sum(ae)/sum(rentals) wape FROM (SELECT h,count(*) n,sum(abs(y-pred)) ae,sum(y) rentals FROM scored WHERE functioning AND d>=DATE '2018-09-01' AND model='{best}' GROUP BY 1)")
assert queries['quality'][0]['rentals']==queries['independent_total'][0]['total']
final=next(r for r in queries['model_metrics'] if r['split'].startswith('Test') and r['model']==best)
assert abs(final['mae']-queries['independent_mae'][0]['mae'])<1e-9
queries['selection']={'best':best,'rule':'Lowest mean absolute error on June–August validation; September–November is final walk-forward test.'}
(S/'results.json').write_text(json.dumps(queries,indent=2,default=str))
print(json.dumps({k:queries[k] for k in ['quality','season','season_peak','model_metrics','envelope','rain_standardized','holiday_standardized','selection']},indent=2,default=str))
log('Computed diagnostics and calendar-only forecasts. Instruments: setup.sql; named diagnostic SQL; forecast.sql; model_metrics.sql and selected_* SQL. Selection based solely on June–August MAE: '+best+'. Final holdout metrics and service envelope saved results.json. Independent regrouping exactly reproduces total rentals and selected-model test MAE/WAPE. All results persisted are aggregates; row-level views are in-memory only.')
