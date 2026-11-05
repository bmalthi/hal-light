CREATE TEMP VIEW forecasts AS
SELECT t.*, CASE WHEN t.d<DATE '2018-09-01' THEN 'Validation Jun–Aug' ELSE 'Test Sep–Nov' END split,
p.p7,p.p28,p.p56,p.q28,p.q56,p.n28,p.n56,
CASE WHEN l.functioning THEN l.y ELSE p.p28 END lag7
FROM hours t
LEFT JOIN LATERAL (SELECT
avg(y) FILTER(WHERE d>=t.d-7) p7,
avg(y) FILTER(WHERE d>=t.d-28 AND daytype=t.daytype) p28,
avg(y) FILTER(WHERE daytype=t.daytype) p56,
quantile_cont(y,.9) FILTER(WHERE d>=t.d-28 AND daytype=t.daytype) q28,
quantile_cont(y,.9) FILTER(WHERE daytype=t.daytype) q56,
count(*) FILTER(WHERE d>=t.d-28 AND daytype=t.daytype) n28,
count(*) FILTER(WHERE daytype=t.daytype) n56
FROM hours WHERE d<t.d AND d>=t.d-56 AND h=t.h AND functioning) p ON true
LEFT JOIN hours l ON l.d=t.d-7 AND l.h=t.h
WHERE t.d>=DATE '2018-06-01';
CREATE TEMP VIEW scored AS SELECT f.*,v.model,v.pred,
CASE WHEN NOT functioning THEN 0 ELSE v.pred END schedule_pred
FROM forecasts f,LATERAL (VALUES ('Last week',lag7),('Past 7d hour',p7),('Past 28d hour/daytype',p28),('Past 56d hour/daytype',p56)) v(model,pred);