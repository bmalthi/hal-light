SELECT strftime(d,'%Y-%m') period,count(*) n FROM hours WHERE NOT functioning GROUP BY 1 ORDER BY 1;
