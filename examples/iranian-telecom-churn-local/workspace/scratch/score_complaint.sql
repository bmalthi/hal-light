CREATE OR REPLACE TEMP VIEW main.score_complaint AS SELECT f.*,
 CASE WHEN c.n>=20 THEN c.probability ELSE (SELECT avg(churn) FROM main.features WHERE bucket<6) END p
 FROM main.features f LEFT JOIN main.fit_complaint c ON f.complaints=c.complaints