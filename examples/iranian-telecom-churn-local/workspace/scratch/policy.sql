CREATE TEMP VIEW main.policy AS SELECT *,
 CASE WHEN complaints=1 THEN 'Service investigation' WHEN p>=0.2 AND customer_value>=200 THEN 'Offer experiment' ELSE 'No paid action' END AS action,
 CASE WHEN complaints=1 THEN 1 WHEN p>=0.2 AND customer_value>=200 THEN 4 ELSE 0 END AS cost,
 CASE WHEN complaints=1 THEN 100000+p ELSE p*customer_value END AS priority
FROM main.score_complaint_usage WHERE bucket>=8