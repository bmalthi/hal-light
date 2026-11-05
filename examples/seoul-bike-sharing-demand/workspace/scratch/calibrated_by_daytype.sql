SELECT daytype,count(*) n,avg((y<=q28+52.460000000000065)::INT) coverage FROM forecasts WHERE functioning AND d>=DATE '2018-09-01' GROUP BY 1;
