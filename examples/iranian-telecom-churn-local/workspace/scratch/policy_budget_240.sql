WITH g AS (SELECT priority,action,cost,count(*) n,sum(churn) y,sum(churn*customer_value) yv FROM main.policy WHERE cost>0 GROUP BY 1,2,3),
 a AS(SELECT *,coalesce(sum(n*cost) OVER(ORDER BY priority DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) prev_cost FROM g),
 w AS(SELECT *,greatest(0,least(1.0,(240-prev_cost)/(n*cost))) weight FROM a)
 SELECT 240 budget_units,action,sum(n*weight) selected,sum(n*cost*weight) spend,
 sum(y*weight) caught,sum((n-y)*weight) false_positives,sum(yv*weight) churn_value
 FROM w GROUP BY 1,2 ORDER BY 2