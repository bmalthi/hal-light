CREATE TEMP TABLE raw AS SELECT
 "Call  Failure" AS failures, Complains AS complaint,
 "Subscription  Length" AS tenure,"Charge  Amount" AS charge,
 "Seconds of Use" AS seconds,"Frequency of use" AS calls,
 "Frequency of SMS" AS sms,"Distinct Called Numbers" AS distinct_calls,
 "Age Group" AS age_group,"Tariff Plan" AS tariff,Status AS status,
 Age AS age,"Customer Value" AS value,Churn AS churn
 FROM read_csv_auto('/hal-light/examples/iranian-telecom-churn-local/question/data.csv');
-- Split expression: hash(failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value, <seed>) % 100.
-- Full and SELECT DISTINCT * variants are temporary, in-memory only.
