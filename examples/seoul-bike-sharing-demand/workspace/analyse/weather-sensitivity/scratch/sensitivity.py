"""Aggregate-only weather/holiday sensitivity from the authorized local source."""
from pathlib import Path
import json
import numpy as np
import duckdb

HERE = Path(__file__).resolve().parent
SOURCE = '/hal-light/examples/seoul-bike-sharing-demand/question/data.csv'
con = duckdb.connect()
SOURCE_SQL = f'''CREATE TEMP VIEW obs AS SELECT
    strptime("Date", '%d/%m/%Y')::DATE AS day,
    "Hour"::INTEGER AS hour, "Rented Bike Count"::DOUBLE AS y,
    "Seasons" AS season,
    date_part('month', strptime("Date", '%d/%m/%Y'))::INTEGER AS month,
    (isodow(strptime("Date", '%d/%m/%Y')) IN (6,7)) AS weekend,
    "Holiday"='Holiday' AS holiday,
    "Rainfall"::DOUBLE>0 AS wet,
    "Temperature"::DOUBLE AS temperature,
    floor("Temperature"::DOUBLE/5)::INTEGER AS temp5,
    "Humidity"::DOUBLE AS humidity,
    floor("Humidity"::DOUBLE/20)::INTEGER AS humid20
    FROM read_csv('{SOURCE}', all_varchar=true)
    WHERE "Functioning Day"='Yes' '''
con.execute(SOURCE_SQL)
queries = {'source': SOURCE_SQL}

def query(sql, params=None):
    result = con.execute(sql, params or [])
    names = [v[0] for v in result.description]
    return [dict(zip(names, row)) for row in result.fetchall()]

def standardize(name, arm, axes, minimum=1, omit=None, no_zero_humidity=False, fixed_keys=None):
    """Common support with pooled count weights, including retained date counts."""
    keys = ', '.join(axes)
    where = 'humidity>0' if no_zero_humidity else 'true'
    params = []
    if omit is not None:
        where += ' AND day<>?'
        params.append(omit)
    fixed_clause = ''
    if fixed_keys is not None:
        fixed_clause = f' AND ({keys}) IN (SELECT {keys} FROM {fixed_keys})'
    sql = f'''WITH base AS (SELECT *, {arm} AS exposed FROM obs WHERE {where}),
        cells AS (SELECT {keys},
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY {keys}),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>={minimum} AND n0>={minimum}{fixed_clause}),
        kept AS (SELECT b.* FROM base b JOIN support USING ({keys}))
        SELECT (SELECT count(*) FROM support) AS common_cells,
          (SELECT count(*) FILTER(WHERE exposed) FROM base) AS total_exposed_hours,
          (SELECT count(*) FILTER(WHERE NOT exposed) FROM base) AS total_reference_hours,
          (SELECT count(DISTINCT day) FILTER(WHERE exposed) FROM base) AS total_exposed_dates,
          (SELECT count(DISTINCT day) FILTER(WHERE NOT exposed) FROM base) AS total_reference_dates,
          (SELECT count(*) FILTER(WHERE exposed) FROM kept) AS exposed_hours,
          (SELECT count(*) FILTER(WHERE NOT exposed) FROM kept) AS reference_hours,
          (SELECT count(DISTINCT day) FILTER(WHERE exposed) FROM kept) AS exposed_dates,
          (SELECT count(DISTINCT day) FILTER(WHERE NOT exposed) FROM kept) AS reference_dates,
          (SELECT sum(w*y1)/sum(w) FROM support) AS standardized_exposed_mean,
          (SELECT sum(w*y0)/sum(w) FROM support) AS standardized_reference_mean,
          (SELECT 100*(sum(w*y1)/sum(w*y0)-1) FROM support) AS relative_difference_pct,
          (SELECT sum(n1*y1)/sum(n1) FROM support) AS exposed_mean_at_exposed_mix,
          (SELECT sum(n1*y0)/sum(n1) FROM support) AS reference_mean_at_exposed_mix,
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct'''
    queries[name] = sql
    result = query(sql, params)[0]
    for arm_name in ['exposed', 'reference']:
        result[f'{arm_name}_retained_pct'] = 100 * result[f'{arm_name}_hours'] / result[f'total_{arm_name}_hours']
    result['axes'] = axes
    result['minimum_hours_per_arm'] = minimum
    result['zero_humidity_excluded'] = no_zero_humidity
    return result

rain_configs = [
    ('season_hour_daytype', ['season','hour','weekend'], 1, False),
    ('season_hour_daytype_temp5', ['season','hour','weekend','temp5'], 1, False),
    ('month_hour_daytype_temp5', ['month','hour','weekend','temp5'], 1, False),
    ('season_hour_daytype_temp5_min3', ['season','hour','weekend','temp5'], 3, False),
    ('month_hour_daytype_temp5_min3', ['month','hour','weekend','temp5'], 3, False),
    ('season_hour_daytype_temp5_humid20', ['season','hour','weekend','temp5','humid20'], 1, False),
    ('season_hour_daytype_temp5_humid20_nozero', ['season','hour','weekend','temp5','humid20'], 1, True),
]
rain = {name: standardize('rain_'+name,'wet', axes, minimum, no_zero_humidity=nozero)
        for name,axes,minimum,nozero in rain_configs}

holiday_configs = [
    ('season_hour_daytype', ['season','hour','weekend']),
    ('month_hour_daytype', ['month','hour','weekend']),
    ('season_hour_daytype_temp5_wet', ['season','hour','weekend','temp5','wet']),
    ('month_hour_daytype_temp5_wet', ['month','hour','weekend','temp5','wet']),
]
holiday = {name: standardize('holiday_'+name,'holiday',axes) for name,axes in holiday_configs}
# Holiday-date identities are used only as in-memory loop keys, never printed/saved.
holiday_days = [row[0] for row in con.execute('SELECT DISTINCT day FROM obs WHERE holiday ORDER BY day').fetchall()]

def loo_summary(records):
    vals=np.array([r['relative_difference_pct'] for r in records if r['relative_difference_pct'] is not None])
    return {'omissions':len(records), 'runnable':len(vals),
        'difference_min_pct':float(vals.min()), 'difference_median_pct':float(np.median(vals)),
        'difference_max_pct':float(vals.max()),'negative_count':int((vals<0).sum()),
        'positive_count':int((vals>0).sum()),
        'common_cells_range':[min(r['common_cells'] for r in records),max(r['common_cells'] for r in records)],
        'exposed_hours_range':[min(r['exposed_hours'] for r in records),max(r['exposed_hours'] for r in records)],
        'reference_hours_range':[min(r['reference_hours'] for r in records),max(r['reference_hours'] for r in records)]}

loo = {}
for name,axes in holiday_configs:
    records=[standardize('leave_one_out_'+name, 'holiday', axes, omit=day) for day in holiday_days]
    loo[name]={'recomputed_support':loo_summary(records)}
    # Fixed-support subset: cells retain at least one holiday observation after any
    # one holiday date is removed. A date supplies at most one observation/cell.
    keys=', '.join(axes)
    fixed_name='fixed_'+name
    fixed_sql=f'''CREATE TEMP VIEW {fixed_name} AS
        SELECT {keys} FROM obs GROUP BY {keys}
        HAVING count(*) FILTER(WHERE holiday)>=2 AND count(*) FILTER(WHERE NOT holiday)>=1'''
    con.execute(fixed_sql)
    queries[fixed_name]=fixed_sql
    fixed_full=standardize('fixed_full_'+name,'holiday',axes,fixed_keys=fixed_name)
    fixed_records=[standardize('leave_one_out_fixed_'+name,'holiday',axes,omit=day,fixed_keys=fixed_name) for day in holiday_days]
    loo[name]['fixed_common_support_full']=fixed_full
    loo[name]['fixed_common_support_omissions']=loo_summary(fixed_records)

# Independent path: rebuild the standardized headline as explicit aggregate cells.
independent_sql='''WITH c AS (
    SELECT season,hour,weekend,temp5,
       sum(y) FILTER(WHERE wet) s1,count(*) FILTER(WHERE wet) n1,
       sum(y) FILTER(WHERE NOT wet) s0,count(*) FILTER(WHERE NOT wet) n0
    FROM obs GROUP BY ALL)
    SELECT sum((n1+n0)*s1/n1)/sum(n1+n0) AS wet_mean,
           sum((n1+n0)*s0/n0)/sum(n1+n0) AS dry_mean
    FROM c WHERE n1>0 AND n0>0'''
queries['independent_rain_rebuild']=independent_sql
independent=query(independent_sql)[0]
expected=rain['season_hour_daytype_temp5']
assert abs(independent['wet_mean']-expected['standardized_exposed_mean'])<1e-9
assert abs(independent['dry_mean']-expected['standardized_reference_mean'])<1e-9

out={'rain':rain,'holiday':holiday,'holiday_leave_one_date_out':loo,
    'holiday_dates':len(holiday_days),'independent_rain_rebuild':independent,
    'interpretation':{
      'support':'Conditional matched associations on retained common support, not all operating hours.',
      'dependence':'Distinct dates are counts, not proof of independent observations; rain and holidays cluster.',
      'humidity':'Humidity adjustment can absorb weather pathways; it is a descriptive sensitivity, not a causal identification improvement.',
      'leave_one_out':'Ranges reflect dropping one holiday date and reweighting. Fixed common support removes cell disappearance but pooled weights can still change.',
      'missing_data':['Multiple years and event-specific holiday calendars','Archived weather forecasts as issued before each rental day','Station inventories, trip duration/flows and unsuccessful rental attempts','Sensor-quality metadata for zero humidity readings']}}
(HERE/'findings.json').write_text(json.dumps(out,indent=2)+'\n')
(HERE/'queries.sql').write_text('\n\n'.join(f'-- {name}\n{sql};' for name,sql in queries.items())+'\n')
print(json.dumps({'rain':{k:{v:r[v] for v in ['relative_difference_pct','exposed_hours','reference_hours','exposed_dates','reference_dates','exposed_retained_pct','reference_retained_pct']} for k,r in rain.items()},'holiday':{k:r['relative_difference_pct'] for k,r in holiday.items()},'loo':{k:v['recomputed_support'] for k,v in loo.items()}},indent=2))
