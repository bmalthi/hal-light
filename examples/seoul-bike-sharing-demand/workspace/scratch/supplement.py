from pathlib import Path
import duckdb,json,subprocess
S=Path(__file__).resolve().parent; R=S.parent
c=duckdb.connect(); c.execute((S/'setup.sql').read_text()); c.execute((S/'forecast.sql').read_text())
a=json.loads((S/'results.json').read_text())
def q(name,sql):
 (S/(name+'.sql')).write_text(sql+';\n');r=c.execute(sql);v=[dict(zip([x[0] for x in r.description],row)) for row in r.fetchall()];a[name]=v;return v
buf=q('calibration',"SELECT quantile_cont(y-q28,.9) buffer,count(*) n FROM forecasts WHERE functioning AND d<DATE '2018-09-01'")[0]['buffer']
q('calibrated_envelope',f"SELECT count(*) n,avg((y<=q28+{buf})::INT) coverage,avg(greatest(y-q28-{buf},0)) unmet_proxy,avg(greatest(q28+{buf}-y,0)) slack FROM forecasts WHERE functioning AND d>=DATE '2018-09-01'")
q('calibrated_by_daytype',f"SELECT daytype,count(*) n,avg((y<=q28+{buf})::INT) coverage FROM forecasts WHERE functioning AND d>=DATE '2018-09-01' GROUP BY 1")
q('closed_by_month',"SELECT strftime(d,'%Y-%m') period,count(*) n FROM hours WHERE NOT functioning GROUP BY 1 ORDER BY 1")
q('quality_all',"SELECT count(*) n,sum(CASE WHEN humidity IS NULL OR wind IS NULL OR visibility IS NULL OR dew IS NULL OR solar IS NULL OR snow IS NULL OR season IS NULL OR holiday IS NULL THEN 1 ELSE 0 END) other_nulls, min(y) min_rental,max(y) max_rental FROM hours")
q('operating_summary','SELECT count(*) n,avg(y) mean,sum(y) total FROM hours WHERE functioning')
q('night',"SELECT CASE WHEN h BETWEEN 1 AND 5 THEN '01–05' WHEN h BETWEEN 7 AND 9 THEN '07–09' WHEN h BETWEEN 16 AND 20 THEN '16–20' ELSE 'Other hours' END band,count(*) n,avg(y) mean,sum(y) total FROM hours WHERE functioning GROUP BY 1")
q('winter_hours',"SELECT h,daytype,count(*) n,avg(y) mean FROM hours WHERE functioning AND season='Winter' AND h IN (5,8,18) GROUP BY 1,2 ORDER BY 1,2")
a['service_buffer']=buf
(S/'results.json').write_text(json.dumps(a,indent=2))
print(json.dumps({k:a[k] for k in ['calibration','calibrated_envelope','calibrated_by_daytype','selected_rain','selected_months','night','hour','next_day']},indent=2))
stamp=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
with (R/'run_log.md').open('a') as f:f.write('\n## '+stamp+'\nRival resolved: rolling calendar forecasts use no realized weather or future seasonal outcomes; final 28d forecast MAE 227.95 vs 293.20 last-week baseline. Peak flip test reverses a year-round evening rule: winter workday peak is 08:00, other seasons 18:00. Uncalibrated historical p90 only covers 83.47% validation and 87.92% test; calibration adds validation-only 90th percentile excess and is tested once on final period. Instruments supplement.py, calibration.sql, calibrated_envelope.sql. Early query errors were SQL reserved aliases (Parser Error: syntax error at or near "temp", "start", "days", "month", "target") and ambiguous joined d (Binder Error: Ambiguous reference to column name "d"); renamed/qualified and reran successfully, never interpreted failures as data gaps.\n')
