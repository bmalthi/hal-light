SELECT h,daytype,count(*) n,avg(y) mean FROM hours WHERE functioning AND season='Winter' AND h IN (5,8,18) GROUP BY 1,2 ORDER BY 1,2;
