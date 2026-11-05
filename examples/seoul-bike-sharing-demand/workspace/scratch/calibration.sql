SELECT quantile_cont(y-q28,.9) buffer,count(*) n FROM forecasts WHERE functioning AND d<DATE '2018-09-01';
