SELECT functioning dimension, count(*) hour_count,sum(y) rentals,avg(y) mean,quantile_cont(y,.9) p90 FROM hours  GROUP BY 1 ORDER BY 1;
