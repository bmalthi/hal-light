CREATE TEMP TABLE source AS SELECT row_number() OVER () AS rid,
 "Call  Failure" AS failures, Complains AS complaint,
 "Subscription  Length" AS tenure, "Charge  Amount" AS charge,
 "Seconds of Use" AS seconds, "Frequency of use" AS calls,
 "Frequency of SMS" AS sms, "Distinct Called Numbers" AS distinct_calls,
 "Age Group" AS age_group, "Tariff Plan" AS tariff, Status AS status,
 Age AS age, "Customer Value" AS value, Churn AS churn
 FROM read_csv_auto('/hal-light/examples/iranian-telecom-churn-local/question/data.csv');

CREATE TEMP TABLE base AS SELECT *, hash(failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value) AS profile,
 CASE WHEN hash(failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value,20261104)%100 <60 THEN 'train'
 WHEN hash(failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value,20261104)%100 <80 THEN 'validation' ELSE 'test' END AS split
 FROM source;

SELECT split,count(*) AS n,sum(churn) AS churners,avg(churn) AS rate,count(DISTINCT profile) AS profiles FROM base GROUP BY split ORDER BY split;

SELECT median(seconds) FROM base WHERE split='train' AND seconds>0;

CREATE TEMP TABLE data AS SELECT *, CASE WHEN seconds=0 THEN 0 WHEN seconds<=3100.0 THEN 1 ELSE 2 END AS usage FROM base;

SELECT avg(churn) FROM data WHERE split='train';

CREATE TEMP TABLE fit_complaint AS SELECT complaint,count(*) AS n,sum(churn) AS events,(sum(churn)+20*0.15889830508474576)/(count(*)+20) AS risk FROM data WHERE split='train' GROUP BY complaint;

CREATE TEMP TABLE pred_complaint AS SELECT d.*,coalesce(f.risk,0.15889830508474576) AS risk FROM data d LEFT JOIN fit_complaint f USING (complaint);

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint WHERE split='validation' GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_complaint WHERE split='validation';

SELECT count(*) FROM pred_complaint WHERE split='validation';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint WHERE split='validation' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=121)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint WHERE split='validation';

CREATE TEMP TABLE fit_complaint_usage AS SELECT complaint,usage,count(*) AS n,sum(churn) AS events,(sum(churn)+20*0.15889830508474576)/(count(*)+20) AS risk FROM data WHERE split='train' GROUP BY complaint,usage;

CREATE TEMP TABLE pred_complaint_usage AS SELECT d.*,coalesce(f.risk,0.15889830508474576) AS risk FROM data d LEFT JOIN fit_complaint_usage f USING (complaint,usage);

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint_usage WHERE split='validation' GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_complaint_usage WHERE split='validation';

SELECT count(*) FROM pred_complaint_usage WHERE split='validation';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage WHERE split='validation' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=121)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage WHERE split='validation';

CREATE TEMP TABLE fit_complaint_usage_status AS SELECT complaint,usage,status,count(*) AS n,sum(churn) AS events,(sum(churn)+20*0.15889830508474576)/(count(*)+20) AS risk FROM data WHERE split='train' GROUP BY complaint,usage,status;

CREATE TEMP TABLE pred_complaint_usage_status AS SELECT d.*,coalesce(f.risk,0.15889830508474576) AS risk FROM data d LEFT JOIN fit_complaint_usage_status f USING (complaint,usage,status);

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint_usage_status WHERE split='validation' GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_complaint_usage_status WHERE split='validation';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='validation';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='validation' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=121)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='validation';

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint_usage_status WHERE split='test' GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=32)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=65)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=195)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk*value DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY value DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY complaint DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (status=1)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk*value DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (status=1)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint_usage WHERE split='test' GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_complaint_usage WHERE split='test';

SELECT count(*) FROM pred_complaint_usage WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage WHERE split='test';

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint_usage_status WHERE split='test' AND status=1 GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_complaint_usage_status WHERE split='test' AND status=1;

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test' AND status=1;

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND status=1 AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=98)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test' AND status=1;

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,0),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,1),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,2),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,3),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,4),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,5),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,6),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,7),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,8),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,9),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,10),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,11),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,12),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,13),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,14),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,15),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,16),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,17),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,18),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT count(*) FROM pred_complaint_usage_status WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_complaint_usage_status WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=130)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_complaint_usage_status WHERE split='test';

SELECT CASE WHEN risk<.1 THEN '<10%' WHEN risk<.3 THEN '10–<30%' WHEN risk<.6 THEN '30–<60%' ELSE '60%+' END AS band,
 count(*) AS n,sum(churn) AS events,avg(risk) AS predicted,avg(churn) AS observed
 FROM pred_complaint_usage_status WHERE split='test' GROUP BY band ORDER BY predicted;

SELECT * FROM fit_complaint_usage_status ORDER BY risk DESC;

SELECT median(value) FROM data WHERE split='train';

CREATE TEMP TABLE triage AS SELECT *, CASE
 WHEN complaint=1 AND status=1 THEN 'service'
 WHEN status=1 AND complaint=0 AND risk>=0.2 AND value>=222.815 THEN 'offer'
 ELSE 'none' END AS action FROM pred_complaint_usage_status WHERE split='test';

SELECT action,count(*) AS n,sum(churn) AS churners,avg(churn) AS rate,avg(value) AS mean_value,sum(value*churn) AS churn_value FROM triage GROUP BY action ORDER BY action;

SELECT count(*) AS n,sum(churn) AS churners,avg(value) AS mean_value FROM triage WHERE status=1 AND complaint=1 AND value>=222.815;

WITH r AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank FROM pred_complaint_usage_status WHERE split='test')
 SELECT status,count(*) AS n,sum(churn) AS churners FROM r WHERE rank<=130 GROUP BY status;

WITH cells AS (SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_complaint_usage_status WHERE split='test' GROUP BY risk),
 ordered AS (SELECT *,coalesce(sum(n) OVER (ORDER BY risk DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) AS above FROM cells)
 SELECT sum(least(n,greatest(0,130-above))*events/n) AS expected_caught FROM ordered;

CREATE TEMP TABLE original_data AS SELECT * FROM data;

DELETE FROM data;

INSERT INTO data BY NAME SELECT * REPLACE(CASE WHEN hash(rid,20261104)%100<60 THEN 'train' WHEN hash(rid,20261104)%100<80 THEN 'validation' ELSE 'test' END AS split) FROM original_data;

SELECT median(seconds) FROM data WHERE split='train' AND seconds>0;

UPDATE data SET usage=CASE WHEN seconds=0 THEN 0 WHEN seconds<=3180.0 THEN 1 ELSE 2 END;

SELECT avg(churn) FROM data WHERE split='train';

CREATE TEMP TABLE fit_row_split AS SELECT complaint,usage,status,count(*) AS n,sum(churn) AS events,(sum(churn)+20*0.1597444089456869)/(count(*)+20) AS risk FROM data WHERE split='train' GROUP BY complaint,usage,status;

CREATE TEMP TABLE pred_row_split AS SELECT d.*,coalesce(f.risk,0.1597444089456869) AS risk FROM data d LEFT JOIN fit_row_split f USING (complaint,usage,status);

SELECT risk,count(*) AS n,sum(churn) AS events FROM pred_row_split WHERE split='test' GROUP BY risk ORDER BY risk;

SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM pred_row_split WHERE split='test';

SELECT count(*) FROM pred_row_split WHERE split='test';

WITH ranked AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank
      FROM pred_row_split WHERE split='test' AND (true)),
      selected AS (SELECT * FROM ranked WHERE rank<=125)
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected;

SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM pred_row_split WHERE split='test';

SELECT count(DISTINCT profile) FROM data WHERE split='test' AND profile IN (SELECT profile FROM data WHERE split='train');

SELECT count(*) AS n,sum(churn) AS churners FROM source;

SELECT sum(n) AS n,sum(events) AS churners FROM (SELECT complaint,status,count(*) AS n,sum(churn) AS events FROM source GROUP BY complaint,status);

SELECT count(*) FROM (SELECT profile,count(DISTINCT split) AS ns FROM original_data GROUP BY profile HAVING ns>1);