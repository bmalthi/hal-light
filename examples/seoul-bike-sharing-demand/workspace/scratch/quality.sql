SELECT count(*) n,min(d) start_date,max(d) finish,count(distinct d) day_count,sum(y) rentals,
count(*)-count(distinct(d,h)) duplicate_hours,sum(CASE WHEN NOT functioning THEN 1 ELSE 0 END) closed_hours,
sum(CASE WHEN NOT functioning THEN y ELSE 0 END) closed_rentals,
sum(CASE WHEN y<0 OR h NOT BETWEEN 0 AND 23 THEN 1 ELSE 0 END) invalid,
sum(CASE WHEN d IS NULL OR h IS NULL OR y IS NULL OR temperature IS NULL OR rain IS NULL OR functioning IS NULL THEN 1 ELSE 0 END) core_nulls FROM hours;
