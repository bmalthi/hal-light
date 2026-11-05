SELECT count(*) n,sum(churn) churners,avg(churn) churn_rate,
 count(*)-count(DISTINCT (failures,complaints,tenure,charge,usage_seconds,calls,sms,contacts,age_group,tariff,status,age,customer_value,churn)) exact_duplicate_excess,
 count(*) FILTER (WHERE failures IS NULL OR complaints IS NULL OR tenure IS NULL OR charge IS NULL OR usage_seconds IS NULL OR calls IS NULL OR sms IS NULL OR contacts IS NULL OR age_group IS NULL OR tariff IS NULL OR status IS NULL OR age IS NULL OR customer_value IS NULL OR churn IS NULL) missing_rows,
 min(customer_value) min_value,max(customer_value) max_value,min(tenure) min_tenure,max(tenure) max_tenure
FROM main.source