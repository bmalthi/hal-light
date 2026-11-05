SELECT CASE WHEN snow>0 THEN 'Snow' ELSE 'No snow' END dimension,count(*) n,avg(y) mean FROM hours WHERE functioning GROUP BY 1 ORDER BY 1;
