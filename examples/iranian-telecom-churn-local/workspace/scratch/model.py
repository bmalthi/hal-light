"""Aggregate-only scorecard: raw records never leave the in-memory DuckDB engine."""
import json
from pathlib import Path

import duckdb
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "question/data.csv"
con = duckdb.connect()
queries = []


def query(sql):
    queries.append(sql.strip() + ";")
    return con.execute(sql)


def rows(sql):
    result = query(sql)
    return [dict(zip([d[0] for d in result.description], row)) for row in result.fetchall()]


query(f"""CREATE TEMP TABLE source AS SELECT row_number() OVER () AS rid,
 "Call  Failure" AS failures, Complains AS complaint,
 "Subscription  Length" AS tenure, "Charge  Amount" AS charge,
 "Seconds of Use" AS seconds, "Frequency of use" AS calls,
 "Frequency of SMS" AS sms, "Distinct Called Numbers" AS distinct_calls,
 "Age Group" AS age_group, "Tariff Plan" AS tariff, Status AS status,
 Age AS age, "Customer Value" AS value, Churn AS churn
 FROM read_csv_auto('{SOURCE}')""")
features = "failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value"
query(f"""CREATE TEMP TABLE base AS SELECT *, hash({features}) AS profile,
 CASE WHEN hash({features},20261104)%100 <60 THEN 'train'
 WHEN hash({features},20261104)%100 <80 THEN 'validation' ELSE 'test' END AS split
 FROM source""")
split = rows("SELECT split,count(*) AS n,sum(churn) AS churners,avg(churn) AS rate,count(DISTINCT profile) AS profiles FROM base GROUP BY split ORDER BY split")
cut = query("SELECT median(seconds) FROM base WHERE split='train' AND seconds>0").fetchone()[0]
query(f"CREATE TEMP TABLE data AS SELECT *, CASE WHEN seconds=0 THEN 0 WHEN seconds<={cut} THEN 1 ELSE 2 END AS usage FROM base")
prior = query("SELECT avg(churn) FROM data WHERE split='train'").fetchone()[0]
models = {"complaint": ["complaint"], "complaint_usage": ["complaint", "usage"], "complaint_usage_status": ["complaint", "usage", "status"]}


def fit(name, dims):
    keys = ",".join(dims)
    query(f"CREATE TEMP TABLE fit_{name} AS SELECT {keys},count(*) AS n,sum(churn) AS events,(sum(churn)+20*{prior})/(count(*)+20) AS risk FROM data WHERE split='train' GROUP BY {keys}")
    query(f"CREATE TEMP TABLE pred_{name} AS SELECT d.*,coalesce(f.risk,{prior}) AS risk FROM data d LEFT JOIN fit_{name} f USING ({keys})")


def metrics(table, subset):
    aggregates = rows(f"SELECT risk,count(*) AS n,sum(churn) AS events FROM {table} WHERE {subset} GROUP BY risk ORDER BY risk")
    scores, labels, weights = [], [], []
    for r in aggregates:
        for y, w in [(0, r['n']-r['events']), (1, r['events'])]:
            if w:
                scores.append(r['risk']); labels.append(y); weights.append(w)
    result = rows(f"SELECT count(*) AS n,sum(churn) AS churners,avg(churn) AS prevalence,avg(risk) AS mean_prediction,avg(pow(risk-churn,2)) AS brier FROM {table} WHERE {subset}")[0]
    result['auc'] = roc_auc_score(labels, scores, sample_weight=weights)
    result['average_precision'] = average_precision_score(labels, scores, sample_weight=weights)
    return result


def campaign(table, subset, budget, order="risk DESC", seed=19, eligible="true"):
    # Capacity is floor(budget * all records in the evaluation population).
    n = query(f"SELECT count(*) FROM {table} WHERE {subset}").fetchone()[0]
    k = int(n*budget)
    out = rows(f"""WITH ranked AS (SELECT *,row_number() OVER (ORDER BY {order},hash(profile,{seed}),rid) AS rank
      FROM {table} WHERE {subset} AND ({eligible})),
      selected AS (SELECT * FROM ranked WHERE rank<={k})
      SELECT count(*) AS contacts,coalesce(sum(churn),0) AS caught,
      count(*)-coalesce(sum(churn),0) AS false_positives,
      coalesce(sum(value*churn),0) AS caught_value,avg(value) AS mean_value,
      coalesce(sum(CASE WHEN status=2 THEN 1 ELSE 0 END),0) AS inactive,
      coalesce(sum(complaint),0) AS complaints,
      avg(risk) AS predicted_risk FROM selected""")[0]
    totals = rows(f"SELECT sum(churn) AS churners,sum(value*churn) AS churn_value FROM {table} WHERE {subset}")[0]
    out.update(budget=budget, population=n, capacity=k)
    out['precision'] = out['caught']/out['contacts'] if out['contacts'] else 0
    out['recall'] = out['caught']/totals['churners']
    out['lift'] = out['precision']/(totals['churners']/n)
    out['value_recall'] = out['caught_value']/totals['churn_value']
    out['missed'] = totals['churners']-out['caught']
    out['true_negatives'] = n-totals['churners']-out['false_positives']
    return out


validation = {}
for name, dims in models.items():
    fit(name, dims)
    validation[name] = metrics(f"pred_{name}", "split='validation'")
    validation[name]['campaign20'] = campaign(f"pred_{name}", "split='validation'", .2)
# Predefined objective: precision at 20%; AUC only breaks a tie.
winner = max(models, key=lambda name:(validation[name]['campaign20']['precision'],validation[name]['auc']))
table = f"pred_{winner}"
test = metrics(table, "split='test'")
budgets = [campaign(table, "split='test'", b) for b in [.05,.1,.2,.3]]
policies = {}
for name, order, eligible in [
    ('risk', 'risk DESC', 'true'),
    ('risk_value', 'risk*value DESC', 'true'),
    ('value_only', 'value DESC', 'true'),
    ('complaint_first', 'complaint DESC', 'true'),
    ('active_risk', 'risk DESC', 'status=1'),
    ('active_risk_value', 'risk*value DESC', 'status=1'),
]:
    policies[name] = campaign(table, "split='test'", .2, order, eligible=eligible)
no_status = metrics('pred_complaint_usage', "split='test'")
no_status['campaign20'] = campaign('pred_complaint_usage', "split='test'", .2)
active = metrics(table, "split='test' AND status=1")
active['campaign20'] = campaign(table, "split='test' AND status=1", .2)
tie_checks = [campaign(table, "split='test'", .2, seed=s)['caught'] for s in range(20)]
calibration = rows(f"""SELECT CASE WHEN risk<.1 THEN '<10%' WHEN risk<.3 THEN '10–<30%' WHEN risk<.6 THEN '30–<60%' ELSE '60%+' END AS band,
 count(*) AS n,sum(churn) AS events,avg(risk) AS predicted,avg(churn) AS observed
 FROM {table} WHERE split='test' GROUP BY band ORDER BY predicted""")
scorecard = rows(f"SELECT * FROM fit_{winner} ORDER BY risk DESC")
# A fixed candidate policy for a small pilot. Prioritize service for complaints;
# discounts require high risk, above-training-median value and active eligibility.
vcut = query("SELECT median(value) FROM data WHERE split='train'").fetchone()[0]
query(f"""CREATE TEMP TABLE triage AS SELECT *, CASE
 WHEN complaint=1 AND status=1 THEN 'service'
 WHEN status=1 AND complaint=0 AND risk>=0.2 AND value>={vcut} THEN 'offer'
 ELSE 'none' END AS action FROM {table} WHERE split='test'""")
triage = rows("SELECT action,count(*) AS n,sum(churn) AS churners,avg(churn) AS rate,avg(value) AS mean_value,sum(value*churn) AS churn_value FROM triage GROUP BY action ORDER BY action")
offer_trial = rows(f"SELECT count(*) AS n,sum(churn) AS churners,avg(value) AS mean_value FROM triage WHERE status=1 AND complaint=1 AND value>={vcut}")[0]
# Independent reconstruction of headline through status groups.
headline_by_status = rows(f"""WITH r AS (SELECT *,row_number() OVER (ORDER BY risk DESC,hash(profile,19),rid) AS rank FROM {table} WHERE split='test')
 SELECT status,count(*) AS n,sum(churn) AS churners FROM r WHERE rank<=130 GROUP BY status""")
assert sum(r['churners'] for r in headline_by_status)==policies['risk']['caught']
assert sum(r['n'] for r in headline_by_status)==policies['risk']['contacts']
# Exact expectation over uniform random tie-breaking at the capacity boundary.
expected_ties = rows(f"""WITH cells AS (SELECT risk,count(*) AS n,sum(churn) AS events FROM {table} WHERE split='test' GROUP BY risk),
 ordered AS (SELECT *,coalesce(sum(n) OVER (ORDER BY risk DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) AS above FROM cells)
 SELECT sum(least(n,greatest(0,130-above))*events/n) AS expected_caught FROM ordered""")[0]
# Same scorecard on a conventional row split: a diagnostic, never model selection.
query("CREATE TEMP TABLE original_data AS SELECT * FROM data")
query("DELETE FROM data")
query("INSERT INTO data BY NAME SELECT * REPLACE(CASE WHEN hash(rid,20261104)%100<60 THEN 'train' WHEN hash(rid,20261104)%100<80 THEN 'validation' ELSE 'test' END AS split) FROM original_data")
row_cut = query("SELECT median(seconds) FROM data WHERE split='train' AND seconds>0").fetchone()[0]
query(f"UPDATE data SET usage=CASE WHEN seconds=0 THEN 0 WHEN seconds<={row_cut} THEN 1 ELSE 2 END")
prior = query("SELECT avg(churn) FROM data WHERE split='train'").fetchone()[0]
fit('row_split', models[winner])
row_split = metrics('pred_row_split', "split='test'")
row_split['campaign20'] = campaign('pred_row_split', "split='test'", .2)
row_split['profiles_shared_with_training'] = query("SELECT count(DISTINCT profile) FROM data WHERE split='test' AND profile IN (SELECT profile FROM data WHERE split='train')").fetchone()[0]
checks = rows("SELECT count(*) AS n,sum(churn) AS churners FROM source")
group_check = rows("SELECT sum(n) AS n,sum(events) AS churners FROM (SELECT complaint,status,count(*) AS n,sum(churn) AS events FROM source GROUP BY complaint,status)")
assert checks == group_check
assert not query("SELECT count(*) FROM (SELECT profile,count(DISTINCT split) AS ns FROM original_data GROUP BY profile HAVING ns>1)").fetchone()[0]
out = dict(split=split, usage_cut=cut, value_cut=vcut, smoothing=20, validation=validation,
           winner=winner, test=test, budgets=budgets, policies=policies,
           no_status=no_status, active=active, tie_caught_range=[min(tie_checks),max(tie_checks)],
           calibration=calibration, scorecard=scorecard, triage=triage,
           offer_trial=offer_trial, headline_by_status=headline_by_status, expected_ties=expected_ties,
           row_split=row_split, reconciliation=dict(direct=checks,grouped=group_check))
(ROOT/'scratch/model_results.json').write_text(json.dumps(out,indent=2))
(ROOT/'scratch/model_queries.sql').write_text('\n\n'.join(queries))
print(json.dumps({k:out[k] for k in ['split','usage_cut','value_cut','winner','test','budgets','policies','no_status','active','tie_caught_range','triage','row_split']},indent=2))
