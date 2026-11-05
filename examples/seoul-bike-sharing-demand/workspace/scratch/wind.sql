SELECT CASE WHEN wind<2 THEN '<2 m/s' WHEN wind<4 THEN '2–<4 m/s' ELSE '4+ m/s' END dimension,count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY 1 ORDER BY 1;
