SELECT h,daytype,count(*) n,avg(y) mean,quantile_cont(y,.9) p90 FROM hours WHERE functioning GROUP BY 1,2 ORDER BY 1,2;
