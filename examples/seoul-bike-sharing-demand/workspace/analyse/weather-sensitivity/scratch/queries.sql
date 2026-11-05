-- source
CREATE TEMP VIEW obs AS SELECT
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
    FROM read_csv('/hal-light/examples/seoul-bike-sharing-demand/question/data.csv', all_varchar=true)
    WHERE "Functioning Day"='Yes' ;

-- rain_season_hour_daytype
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- rain_season_hour_daytype_temp5
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend, temp5,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- rain_month_hour_daytype_temp5
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE true),
        cells AS (SELECT month, hour, weekend, temp5,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend, temp5),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend, temp5))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- rain_season_hour_daytype_temp5_min3
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend, temp5,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=3 AND n0>=3),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- rain_month_hour_daytype_temp5_min3
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE true),
        cells AS (SELECT month, hour, weekend, temp5,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend, temp5),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=3 AND n0>=3),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend, temp5))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- rain_season_hour_daytype_temp5_humid20
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend, temp5, humid20,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5, humid20),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5, humid20))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- rain_season_hour_daytype_temp5_humid20_nozero
WITH base AS (SELECT *, wet AS exposed FROM obs WHERE humidity>0),
        cells AS (SELECT season, hour, weekend, temp5, humid20,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5, humid20),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5, humid20))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- holiday_season_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- holiday_month_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT month, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- holiday_season_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- holiday_month_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT month, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_season_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT season, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- fixed_season_hour_daytype
CREATE TEMP VIEW fixed_season_hour_daytype AS
        SELECT season, hour, weekend FROM obs GROUP BY season, hour, weekend
        HAVING count(*) FILTER(WHERE holiday)>=2 AND count(*) FILTER(WHERE NOT holiday)>=1;

-- fixed_full_season_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (season, hour, weekend) IN (SELECT season, hour, weekend FROM fixed_season_hour_daytype)),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_fixed_season_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT season, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (season, hour, weekend) IN (SELECT season, hour, weekend FROM fixed_season_hour_daytype)),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_month_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT month, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- fixed_month_hour_daytype
CREATE TEMP VIEW fixed_month_hour_daytype AS
        SELECT month, hour, weekend FROM obs GROUP BY month, hour, weekend
        HAVING count(*) FILTER(WHERE holiday)>=2 AND count(*) FILTER(WHERE NOT holiday)>=1;

-- fixed_full_month_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT month, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (month, hour, weekend) IN (SELECT month, hour, weekend FROM fixed_month_hour_daytype)),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_fixed_month_hour_daytype
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT month, hour, weekend,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (month, hour, weekend) IN (SELECT month, hour, weekend FROM fixed_month_hour_daytype)),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_season_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT season, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- fixed_season_hour_daytype_temp5_wet
CREATE TEMP VIEW fixed_season_hour_daytype_temp5_wet AS
        SELECT season, hour, weekend, temp5, wet FROM obs GROUP BY season, hour, weekend, temp5, wet
        HAVING count(*) FILTER(WHERE holiday)>=2 AND count(*) FILTER(WHERE NOT holiday)>=1;

-- fixed_full_season_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT season, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (season, hour, weekend, temp5, wet) IN (SELECT season, hour, weekend, temp5, wet FROM fixed_season_hour_daytype_temp5_wet)),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_fixed_season_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT season, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY season, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (season, hour, weekend, temp5, wet) IN (SELECT season, hour, weekend, temp5, wet FROM fixed_season_hour_daytype_temp5_wet)),
        kept AS (SELECT b.* FROM base b JOIN support USING (season, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_month_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT month, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- fixed_month_hour_daytype_temp5_wet
CREATE TEMP VIEW fixed_month_hour_daytype_temp5_wet AS
        SELECT month, hour, weekend, temp5, wet FROM obs GROUP BY month, hour, weekend, temp5, wet
        HAVING count(*) FILTER(WHERE holiday)>=2 AND count(*) FILTER(WHERE NOT holiday)>=1;

-- fixed_full_month_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true),
        cells AS (SELECT month, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (month, hour, weekend, temp5, wet) IN (SELECT month, hour, weekend, temp5, wet FROM fixed_month_hour_daytype_temp5_wet)),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- leave_one_out_fixed_month_hour_daytype_temp5_wet
WITH base AS (SELECT *, holiday AS exposed FROM obs WHERE true AND day<>?),
        cells AS (SELECT month, hour, weekend, temp5, wet,
          count(*) FILTER(WHERE exposed) AS n1,
          count(*) FILTER(WHERE NOT exposed) AS n0,
          avg(y) FILTER(WHERE exposed) AS y1,
          avg(y) FILTER(WHERE NOT exposed) AS y0
          FROM base GROUP BY month, hour, weekend, temp5, wet),
        support AS (SELECT *, n1+n0 AS w FROM cells WHERE n1>=1 AND n0>=1 AND (month, hour, weekend, temp5, wet) IN (SELECT month, hour, weekend, temp5, wet FROM fixed_month_hour_daytype_temp5_wet)),
        kept AS (SELECT b.* FROM base b JOIN support USING (month, hour, weekend, temp5, wet))
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
          (SELECT 100*(sum(n1*y1)/sum(n1*y0)-1) FROM support) AS exposed_mix_difference_pct;

-- independent_rain_rebuild
WITH c AS (
    SELECT season,hour,weekend,temp5,
       sum(y) FILTER(WHERE wet) s1,count(*) FILTER(WHERE wet) n1,
       sum(y) FILTER(WHERE NOT wet) s0,count(*) FILTER(WHERE NOT wet) n0
    FROM obs GROUP BY ALL)
    SELECT sum((n1+n0)*s1/n1)/sum(n1+n0) AS wet_mean,
           sum((n1+n0)*s0/n0)/sum(n1+n0) AS dry_mean
    FROM c WHERE n1>0 AND n0>0;
