from pathlib import Path
import json
import duckdb

HERE = Path(__file__).resolve().parent
SOURCE = '/hal-light/examples/seoul-bike-sharing-demand/question/data.csv'
con = duckdb.connect()
con.execute(f'''CREATE TEMP VIEW raw AS SELECT * FROM read_csv('{SOURCE}', header=true, all_varchar=true)''')
con.execute('''CREATE TEMP VIEW obs AS SELECT
    coalesce(try_strptime("Date", '%d/%m/%Y'), try_strptime("Date", '%Y-%m-%d'))::DATE AS date,
    "Rented Bike Count"::INTEGER AS y, "Hour"::INTEGER AS hour,
    "Temperature"::DOUBLE AS temp, "Humidity"::DOUBLE AS humidity,
    "Wind speed"::DOUBLE AS wind, "Visibility"::DOUBLE AS visibility,
    "Dew point temperature"::DOUBLE AS dew, "Solar Radiation"::DOUBLE AS solar,
    "Rainfall"::DOUBLE AS rain, "Snowfall"::DOUBLE AS snow,
    "Seasons" AS season, "Holiday" AS holiday, "Functioning Day" AS functioning,
    CASE WHEN isodow(coalesce(try_strptime("Date", '%d/%m/%Y'), try_strptime("Date", '%Y-%m-%d'))::DATE) IN (6,7) THEN 'Weekend' ELSE 'Weekday' END AS daytype,
    CASE WHEN rain>0 THEN 'Wet' ELSE 'Dry' END AS wet,
    month(coalesce(try_strptime("Date", '%d/%m/%Y'), try_strptime("Date", '%Y-%m-%d'))::DATE) AS month,
    CASE WHEN "Hour"::INTEGER BETWEEN 7 AND 9 THEN '07–09' WHEN "Hour"::INTEGER BETWEEN 17 AND 19 THEN '17–19'
         WHEN "Hour"::INTEGER BETWEEN 2 AND 5 THEN '02–05' WHEN "Hour"::INTEGER BETWEEN 10 AND 16 THEN '10–16'
         ELSE 'Other hours' END AS time_window
    FROM raw''')
con.execute("CREATE TEMP VIEW operating AS SELECT * FROM obs WHERE functioning='Yes'")

queries = {}
def query(name, sql):
    queries[name] = sql
    cursor = con.execute(sql)
    columns = [x[0] for x in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

metric = 'count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90'
out = {}
out['quality'] = query('quality', '''SELECT count(*) AS rows, count(distinct date) AS days,
    min(date) AS first_date, max(date) AS last_date, min(hour) AS min_hour, max(hour) AS max_hour,
    count(*) - count(distinct (date,hour)) AS duplicate_date_hours,
    count(*) FILTER (WHERE date IS NULL) AS bad_dates,
    sum(y) AS total_rentals, avg(y) AS all_hour_mean,
    count(*) FILTER (WHERE y<0) AS negative_targets,
    count(*) FILTER (WHERE functioning='No' AND y<>0) AS nonzero_closed_hours,
    count(*) FILTER (WHERE functioning='Yes' AND y=0) AS zero_open_hours,
    count(*) FILTER (WHERE temp IS NULL OR humidity IS NULL OR wind IS NULL OR visibility IS NULL
      OR dew IS NULL OR solar IS NULL OR rain IS NULL OR snow IS NULL OR season IS NULL
      OR holiday IS NULL OR functioning IS NULL OR y IS NULL OR hour IS NULL) AS incomplete_hours
    FROM obs''')[0]
out['categories'] = query('categories', '''SELECT season, holiday, functioning, count(*) AS hours FROM obs GROUP BY ALL ORDER BY ALL''')
out['status'] = query('status', f'SELECT functioning, {metric} FROM obs GROUP BY ALL ORDER BY functioning')
out['closure_dates'] = query('closure_dates', '''WITH d AS (SELECT date, count(*) n,
    count(*) FILTER (WHERE functioning='No') AS closed FROM obs GROUP BY date)
    SELECT count(*) FILTER (WHERE n<>24) AS incomplete_days,
    count(*) FILTER (WHERE closed=24) AS fully_closed_days,
    count(*) FILTER (WHERE closed BETWEEN 1 AND 23) AS partially_closed_days,
    sum(closed) AS closed_hours FROM d''')[0]
out['season_all'] = query('season_all', f'SELECT season, {metric}, count(*) FILTER(WHERE functioning=\'No\') closed_hours FROM obs GROUP BY ALL ORDER BY mean DESC')
out['season'] = query('season', f'SELECT season, {metric} FROM operating GROUP BY ALL ORDER BY mean DESC')
out['month'] = query('month', f"SELECT strftime(date,'%Y-%m') AS month, {metric} FROM operating GROUP BY ALL ORDER BY month")
out['hour'] = query('hour', f'SELECT hour, {metric} FROM operating GROUP BY ALL ORDER BY hour')
out['hour_daytype'] = query('hour_daytype', f'SELECT daytype, hour, {metric} FROM operating GROUP BY ALL ORDER BY daytype, hour')
out['holiday'] = query('holiday', f'SELECT holiday, {metric}, count(distinct date) AS days FROM operating GROUP BY ALL ORDER BY holiday')
out['rain'] = query('rain', f'SELECT wet, {metric} FROM operating GROUP BY ALL ORDER BY wet')
out['temperature'] = query('temperature', f'''SELECT CASE WHEN temp<0 THEN '<0°C' WHEN temp<10 THEN '0–<10°C'
    WHEN temp<20 THEN '10–<20°C' WHEN temp<30 THEN '20–<30°C' ELSE '≥30°C' END AS temperature,
    min(temp) min_temp, {metric} FROM operating GROUP BY ALL ORDER BY min_temp''')
out['snow'] = query('snow', f"SELECT CASE WHEN snow>0 THEN 'Snow recorded' ELSE 'No snow' END AS snow_status, {metric} FROM operating GROUP BY ALL ORDER BY snow_status")
out['weather_correlations'] = query('weather_correlations', '''SELECT
    corr(y,temp) AS temperature, corr(y,humidity) AS humidity, corr(y,wind) AS wind_speed,
    corr(y,visibility) AS visibility, corr(y,dew) AS dew_point,
    corr(y,solar) AS solar_radiation, corr(y,rain) AS rainfall, corr(y,snow) AS snowfall FROM operating''')[0]
out['weather_quality'] = query('weather_quality', '''SELECT
    min(temp) AS temp_min, max(temp) AS temp_max,
    min(humidity) AS humidity_min, max(humidity) AS humidity_max,
    count(*) FILTER(WHERE humidity=0) AS zero_humidity_hours,
    count(*) FILTER(WHERE humidity<0 OR humidity>100) AS outside_humidity_range,
    min(wind) AS wind_min, max(wind) AS wind_max,
    min(visibility) AS visibility_min, max(visibility) AS visibility_max,
    min(dew) AS dew_min, max(dew) AS dew_max,
    count(*) FILTER(WHERE dew>temp) AS dew_above_temperature_hours,
    min(solar) AS solar_min, max(solar) AS solar_max,
    min(rain) AS rain_min, max(rain) AS rain_max,
    min(snow) AS snow_min, max(snow) AS snow_max,
    count(*) FILTER(WHERE wind<0 OR visibility<0 OR solar<0 OR rain<0 OR snow<0) AS negative_nonnegative_weather_hours
    FROM obs''')[0]
out['holiday_raw_difference_pct'] = (out['holiday'][0]['mean']/out['holiday'][1]['mean']-1)*100
out['window_daytype'] = query('window_daytype', f'SELECT daytype, time_window, {metric} FROM operating GROUP BY ALL ORDER BY daytype, time_window')
out['window_season_wet'] = query('window_season_wet', f'''SELECT season, daytype, wet, time_window, {metric}
    FROM operating GROUP BY ALL HAVING count(*)>=5 ORDER BY season, daytype, wet, time_window''')
out['hourly_peaks_by_season_daytype'] = query('hourly_peaks_by_season_daytype', '''WITH h AS (
    SELECT season, daytype, hour, count(*) AS hours, avg(y) mean FROM operating GROUP BY ALL)
    SELECT * FROM h QUALIFY row_number() OVER(PARTITION BY season,daytype ORDER BY mean DESC)=1 ORDER BY season, daytype''')

def standardize(name, exposure, reference, axes):
    keys = ','.join(axes)
    sql = f'''WITH cells AS (SELECT {keys},
        count(*) FILTER (WHERE {exposure}) AS n1, count(*) FILTER (WHERE {reference}) AS n0,
        avg(y) FILTER (WHERE {exposure}) AS y1, avg(y) FILTER (WHERE {reference}) AS y0
        FROM operating GROUP BY {keys}), support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>0 AND n0>0)
        SELECT count(*) AS common_cells, sum(n1) AS exposed_hours, sum(n0) AS reference_hours,
        sum(w*y1)/sum(w) AS standardized_exposed_mean, sum(w*y0)/sum(w) AS standardized_reference_mean,
        (sum(w*y1)/sum(w*y0)-1)*100 AS relative_difference_pct,
        sum(n1*y1)/sum(n1) AS exposed_observed_mean,
        sum(n1*y0)/sum(n1) AS reference_at_exposed_mix,
        (sum(n1*y1)/sum(n1*y0)-1)*100 AS exposed_mix_difference_pct FROM support'''
    return query(name, sql)[0]

out['rain_standardized'] = standardize('rain_standardized', 'rain>0', 'rain=0', ['season','hour','daytype'])
out['rain_standardized_month'] = standardize('rain_standardized_month', 'rain>0', 'rain=0', ['month','hour','daytype'])
out['holiday_standardized'] = standardize('holiday_standardized', "holiday='Holiday'", "holiday='No Holiday'", ['season','hour','daytype'])
out['holiday_standardized_month'] = standardize('holiday_standardized_month', "holiday='Holiday'", "holiday='No Holiday'", ['month','hour','daytype'])
out['independent_reconciliation'] = query('independent_reconciliation', '''WITH daily AS (
    SELECT date,sum(y) AS rentals FROM obs GROUP BY date)
    SELECT sum(rentals) AS total_from_daily, count(*) AS date_groups FROM daily''')[0]
assert out['quality']['total_rentals'] == out['independent_reconciliation']['total_from_daily']
(HERE/'queries.sql').write_text('\n\n'.join(f'-- {name}\n{sql};' for name,sql in queries.items()))
(HERE/'diagnostics.json').write_text(json.dumps(out, indent=2, default=str)+'\n')
summary = {k:out[k] for k in ['quality','closure_dates','status','season','holiday','rain','rain_standardized','rain_standardized_month','holiday_standardized','holiday_standardized_month','window_daytype','hourly_peaks_by_season_daytype','independent_reconciliation']}
print(json.dumps(summary, indent=2, default=str))
