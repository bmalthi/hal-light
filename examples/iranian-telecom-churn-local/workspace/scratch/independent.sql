WITH grouped AS (SELECT complaints,status,count(*) n,sum(churn) y FROM main.source GROUP BY 1,2), testg AS (SELECT p,count(*) n,sum(churn) y FROM main.score_complaint_usage WHERE bucket>=8 GROUP BY p)
SELECT (SELECT sum(n) FROM grouped) total_n,(SELECT sum(y) FROM grouped) total_churn,
(SELECT sum(n) FROM testg) test_n,(SELECT sum(y) FROM testg) test_churn