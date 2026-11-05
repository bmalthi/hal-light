-- quality
SELECT count(*) AS rows, count(distinct date) AS days,
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
    FROM obs;

-- categories
SELECT season, holiday, functioning, count(*) AS hours FROM obs GROUP BY ALL ORDER BY ALL;

-- status
SELECT functioning, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM obs GROUP BY ALL ORDER BY functioning;

-- closure_dates
WITH d AS (SELECT date, count(*) n,
    count(*) FILTER (WHERE functioning='No') AS closed FROM obs GROUP BY date)
    SELECT count(*) FILTER (WHERE n<>24) AS incomplete_days,
    count(*) FILTER (WHERE closed=24) AS fully_closed_days,
    count(*) FILTER (WHERE closed BETWEEN 1 AND 23) AS partially_closed_days,
    sum(closed) AS closed_hours FROM d;

-- season_all
SELECT season, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90, count(*) FILTER(WHERE functioning='No') closed_hours FROM obs GROUP BY ALL ORDER BY mean DESC;

-- season
SELECT season, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY mean DESC;

-- month
SELECT strftime(date,'%Y-%m') AS month, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY month;

-- hour
SELECT hour, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY hour;

-- hour_daytype
SELECT daytype, hour, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY daytype, hour;

-- holiday
SELECT holiday, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90, count(distinct date) AS days FROM operating GROUP BY ALL ORDER BY holiday;

-- rain
SELECT wet, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY wet;

-- temperature
SELECT CASE WHEN temp<0 THEN '<0°C' WHEN temp<10 THEN '0–<10°C'
    WHEN temp<20 THEN '10–<20°C' WHEN temp<30 THEN '20–<30°C' ELSE '≥30°C' END AS temperature,
    min(temp) min_temp, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY min_temp;

-- snow
SELECT CASE WHEN snow>0 THEN 'Snow recorded' ELSE 'No snow' END AS snow_status, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY snow_status;

-- weather_correlations
SELECT
    corr(y,temp) AS temperature, corr(y,humidity) AS humidity, corr(y,wind) AS wind_speed,
    corr(y,visibility) AS visibility, corr(y,dew) AS dew_point,
    corr(y,solar) AS solar_radiation, corr(y,rain) AS rainfall, corr(y,snow) AS snowfall FROM operating;

-- weather_quality
SELECT
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
    FROM obs;

-- window_daytype
SELECT daytype, time_window, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90 FROM operating GROUP BY ALL ORDER BY daytype, time_window;

-- window_season_wet
SELECT season, daytype, wet, time_window, count(*) AS hours, sum(y) AS rentals, avg(y) AS mean, quantile_cont(y, 0.9) AS p90
    FROM operating GROUP BY ALL HAVING count(*)>=5 ORDER BY season, daytype, wet, time_window;

-- hourly_peaks_by_season_daytype
WITH h AS (
    SELECT season, daytype, hour, count(*) AS hours, avg(y) mean FROM operating GROUP BY ALL)
    SELECT * FROM h QUALIFY row_number() OVER(PARTITION BY season,daytype ORDER BY mean DESC)=1 ORDER BY season, daytype;

-- rain_standardized
WITH cells AS (SELECT season,hour,daytype,
        count(*) FILTER (WHERE rain>0) AS n1, count(*) FILTER (WHERE rain=0) AS n0,
        avg(y) FILTER (WHERE rain>0) AS y1, avg(y) FILTER (WHERE rain=0) AS y0
        FROM operating GROUP BY season,hour,daytype), support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>0 AND n0>0)
        SELECT count(*) AS common_cells, sum(n1) AS exposed_hours, sum(n0) AS reference_hours,
        sum(w*y1)/sum(w) AS standardized_exposed_mean, sum(w*y0)/sum(w) AS standardized_reference_mean,
        (sum(w*y1)/sum(w*y0)-1)*100 AS relative_difference_pct,
        sum(n1*y1)/sum(n1) AS exposed_observed_mean,
        sum(n1*y0)/sum(n1) AS reference_at_exposed_mix,
        (sum(n1*y1)/sum(n1*y0)-1)*100 AS exposed_mix_difference_pct FROM support;

-- rain_standardized_month
WITH cells AS (SELECT month,hour,daytype,
        count(*) FILTER (WHERE rain>0) AS n1, count(*) FILTER (WHERE rain=0) AS n0,
        avg(y) FILTER (WHERE rain>0) AS y1, avg(y) FILTER (WHERE rain=0) AS y0
        FROM operating GROUP BY month,hour,daytype), support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>0 AND n0>0)
        SELECT count(*) AS common_cells, sum(n1) AS exposed_hours, sum(n0) AS reference_hours,
        sum(w*y1)/sum(w) AS standardized_exposed_mean, sum(w*y0)/sum(w) AS standardized_reference_mean,
        (sum(w*y1)/sum(w*y0)-1)*100 AS relative_difference_pct,
        sum(n1*y1)/sum(n1) AS exposed_observed_mean,
        sum(n1*y0)/sum(n1) AS reference_at_exposed_mix,
        (sum(n1*y1)/sum(n1*y0)-1)*100 AS exposed_mix_difference_pct FROM support;

-- holiday_standardized
WITH cells AS (SELECT season,hour,daytype,
        count(*) FILTER (WHERE holiday='Holiday') AS n1, count(*) FILTER (WHERE holiday='No Holiday') AS n0,
        avg(y) FILTER (WHERE holiday='Holiday') AS y1, avg(y) FILTER (WHERE holiday='No Holiday') AS y0
        FROM operating GROUP BY season,hour,daytype), support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>0 AND n0>0)
        SELECT count(*) AS common_cells, sum(n1) AS exposed_hours, sum(n0) AS reference_hours,
        sum(w*y1)/sum(w) AS standardized_exposed_mean, sum(w*y0)/sum(w) AS standardized_reference_mean,
        (sum(w*y1)/sum(w*y0)-1)*100 AS relative_difference_pct,
        sum(n1*y1)/sum(n1) AS exposed_observed_mean,
        sum(n1*y0)/sum(n1) AS reference_at_exposed_mix,
        (sum(n1*y1)/sum(n1*y0)-1)*100 AS exposed_mix_difference_pct FROM support;

-- holiday_standardized_month
WITH cells AS (SELECT month,hour,daytype,
        count(*) FILTER (WHERE holiday='Holiday') AS n1, count(*) FILTER (WHERE holiday='No Holiday') AS n0,
        avg(y) FILTER (WHERE holiday='Holiday') AS y1, avg(y) FILTER (WHERE holiday='No Holiday') AS y0
        FROM operating GROUP BY month,hour,daytype), support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>0 AND n0>0)
        SELECT count(*) AS common_cells, sum(n1) AS exposed_hours, sum(n0) AS reference_hours,
        sum(w*y1)/sum(w) AS standardized_exposed_mean, sum(w*y0)/sum(w) AS standardized_reference_mean,
        (sum(w*y1)/sum(w*y0)-1)*100 AS relative_difference_pct,
        sum(n1*y1)/sum(n1) AS exposed_observed_mean,
        sum(n1*y0)/sum(n1) AS reference_at_exposed_mix,
        (sum(n1*y1)/sum(n1*y0)-1)*100 AS exposed_mix_difference_pct FROM support;

-- independent_reconciliation
WITH daily AS (
    SELECT date,sum(y) AS rentals FROM obs GROUP BY date)
    SELECT sum(rentals) AS total_from_daily, count(*) AS date_groups FROM daily;