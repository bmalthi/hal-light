WITH g AS (SELECT p,count(*) n,sum(churn) y FROM main.score_complaint_usage WHERE bucket>=8 GROUP BY p),
w AS (SELECT a.*,greatest(0,least(1.0,(120-coalesce((SELECT sum(b.n) FROM g b WHERE b.p>a.p),0))/a.n)) weight FROM g a)
SELECT sum(n*weight) selected,sum(y*weight) caught FROM w