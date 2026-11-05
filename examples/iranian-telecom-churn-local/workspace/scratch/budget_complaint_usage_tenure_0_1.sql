WITH d AS (SELECT *,p score FROM main.score_complaint_usage_tenure WHERE bucket>=6 AND bucket<8),g AS (SELECT score,count(*) n,sum(churn) y,sum(customer_value) v,sum(churn*customer_value) yv,sum(CASE WHEN complaints=1 THEN 1 ELSE 0 END) complainants FROM d GROUP BY score),
 a AS (SELECT *,coalesce(sum(n) OVER(ORDER BY score DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) preceding_n FROM g),
 w AS (SELECT *,greatest(0,least(1.0,(0.1*(SELECT count(*) FROM d)-preceding_n)/n)) weight FROM a)
 SELECT 0.1 capacity,sum(n*weight) selected,sum(y*weight) caught,sum((n-y)*weight) false_positives,
 sum(y*weight)/sum(n*weight) AS precision,sum(y*weight)/(SELECT sum(churn) FROM d) recall,
 sum(v*weight) selected_value,sum(yv*weight) churn_value,sum(yv*weight)/(SELECT sum(churn*customer_value) FROM d) value_recall,
 sum(complainants*weight) selected_complainants FROM w