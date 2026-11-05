SELECT h,count(*) n,avg((y<=q28)::INT) coverage28,avg(q28) planning_bound,avg(y) mean FROM forecasts WHERE functioning AND d>=DATE '2018-09-01' GROUP BY 1 ORDER BY 1;
