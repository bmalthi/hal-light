SELECT CASE WHEN rain>0 THEN 'Rain' ELSE 'Dry' END dimension,count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY 1 ORDER BY 1;
