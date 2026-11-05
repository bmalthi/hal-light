SELECT h,count(*) n,avg(y) forecast,quantile_cont(y,.9) historical_p90 FROM hours WHERE functioning AND d>=DATE '2018-11-03' AND d<DATE '2018-12-01' AND daytype='Off day' GROUP BY h ORDER BY h;
