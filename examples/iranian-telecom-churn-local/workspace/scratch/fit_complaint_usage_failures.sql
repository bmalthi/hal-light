CREATE OR REPLACE TEMP VIEW main.fit_complaint_usage_failures AS SELECT complaints,usage_bin,failure_bin,count(*) n,sum(churn) y,
 (sum(churn)+20*(SELECT avg(churn) FROM main.features WHERE bucket<6))/(count(*)+20) probability
 FROM main.features WHERE bucket<6 GROUP BY complaints,usage_bin,failure_bin