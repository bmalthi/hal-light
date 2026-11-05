CREATE OR REPLACE TEMP VIEW main.fit_complaint AS SELECT complaints,count(*) n,sum(churn) y,
 (sum(churn)+20*(SELECT avg(churn) FROM main.features WHERE bucket<6))/(count(*)+20) probability
 FROM main.features WHERE bucket<6 GROUP BY complaints