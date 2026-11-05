CREATE TEMP VIEW main.features AS SELECT *,
 hash(failures,complaints,tenure,charge,usage_seconds,calls,sms,contacts,age_group,tariff,status,age,customer_value)%10 bucket,
 CASE WHEN usage_seconds=0 THEN '0' WHEN usage_seconds<1500 THEN '1–1499' WHEN usage_seconds<4000 THEN '1500–3999' ELSE '4000+' END usage_bin,
 CASE WHEN failures=0 THEN '0' WHEN failures<10 THEN '1–9' ELSE '10+' END failure_bin,
 CASE WHEN tenure<24 THEN '<24' WHEN tenure<36 THEN '24–35' ELSE '36+' END tenure_bin,
 CASE WHEN age<30 THEN '<30' WHEN age<40 THEN '30–39' ELSE '40+' END age_bin,
 CASE WHEN customer_value<200 THEN '<200' WHEN customer_value<500 THEN '200–499' ELSE '500+' END value_bin
FROM main.source