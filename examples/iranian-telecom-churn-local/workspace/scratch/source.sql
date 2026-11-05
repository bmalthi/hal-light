CREATE TEMP VIEW main.source AS SELECT
"Call  Failure" failures, "Complains" complaints, "Subscription  Length" tenure,
"Charge  Amount" charge, "Seconds of Use" usage_seconds, "Frequency of use" calls,
"Frequency of SMS" sms, "Distinct Called Numbers" contacts,
"Age Group" age_group, "Tariff Plan" tariff, "Status" status, "Age" age,
"Customer Value" customer_value, "Churn" churn
FROM read_csv_auto('/hal-light/examples/iranian-telecom-churn-local/question/data.csv');