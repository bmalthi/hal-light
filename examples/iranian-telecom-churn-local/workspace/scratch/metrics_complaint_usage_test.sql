WITH d AS (SELECT *,p score FROM main.score_complaint_usage WHERE bucket>=8),g AS (SELECT p,count(*) n,sum(churn) y FROM d GROUP BY p),
 a AS (SELECT *,sum(n-y) OVER(ORDER BY p ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) lower_negative FROM g)
 SELECT (SELECT count(*) FROM d) n,(SELECT sum(churn) FROM d) churners,
 (SELECT avg((churn-p)^2) FROM d) brier,
 sum(y*(coalesce(lower_negative,0)+(n-y)/2.0))/(sum(y)*sum(n-y)) auc FROM a