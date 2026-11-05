SELECT CASE WHEN humidity<40 THEN '<40%' WHEN humidity<70 THEN '40–<70%' ELSE '70+%' END dimension,count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY 1 ORDER BY 1;
