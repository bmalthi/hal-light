CREATE OR REPLACE TEMP VIEW main.score_complaint_usage AS SELECT f.*,
 CASE WHEN c.n>=20 THEN c.probability ELSE (SELECT avg(churn) FROM main.features WHERE bucket<6) END p
 FROM main.features f LEFT JOIN main.fit_complaint_usage c ON f.complaints=c.complaints AND f.usage_bin=c.usage_bin