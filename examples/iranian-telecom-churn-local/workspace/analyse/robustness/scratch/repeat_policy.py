"""Repeated scorecards and active targeting; only aggregates leave DuckDB."""
from collections import Counter
from fractions import Fraction
import json
from pathlib import Path

import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parents[2] / 'question/data.csv'
SEEDS = list(range(20261105, 20261135))
FEATURES = 'failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value'
MODELS = {
    'complaint': ['complaint'],
    'complaint_usage': ['complaint', 'usage'],
    'complaint_usage_status': ['complaint', 'usage', 'status'],
}
con = duckdb.connect()
query_log = (ROOT / 'scratch/repeat_policy_queries.sql').open('w')


def query(sql):
    query_log.write(sql.strip() + ';\n\n')
    query_log.flush()
    return con.execute(sql)


def one(sql):
    result = query(sql)
    return dict(zip([d[0] for d in result.description], result.fetchone()))


def many(sql):
    result = query(sql)
    return [dict(zip([d[0] for d in result.description], r)) for r in result.fetchall()]


def divide(a, b):
    return a / b if b else None


def totals(table, subset):
    return one(f'''SELECT count(*) AS n, coalesce(sum(churn),0) AS churners,
        coalesce(sum(churn*value),0) AS churn_value, avg(churn) AS prevalence
        FROM temp.main.{table} WHERE {subset}''')


def model_metrics(table, subset):
    out = totals(table, subset)
    out.update(one(f'''WITH cells AS (
        SELECT risk, count(*) AS n, sum(churn) AS events
        FROM temp.main.{table} WHERE {subset} GROUP BY risk
      ), ordered AS (
        SELECT *, coalesce(sum(n-events) OVER (ORDER BY risk
          ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) AS neg_below
        FROM cells
      ) SELECT sum(events*(neg_below+0.5*(n-events))) /
          nullif(sum(events)*sum(n-events),0) AS auc,
        sum(events*pow(1-risk,2)+(n-events)*pow(risk,2))/sum(n) AS brier,
        sum(n*risk)/sum(n) AS mean_prediction
      FROM ordered'''))
    # Direct per-row probability-error computation is independent of the grouping.
    direct = one(f'''SELECT avg(pow(risk-churn,2)) AS brier
        FROM temp.main.{table} WHERE {subset}''')['brier']
    assert abs(out['brier'] - direct) < 1e-12
    return out


def campaign(table, subset, dims, order, eligible='true'):
    """Integrate all selections inside SQL; retain rational expected event count."""
    base = totals(table, subset)
    k = base['n'] // 5
    keys = ','.join(dims)
    result = one(f'''WITH cells AS (
        SELECT {keys}, count(*) AS n, sum(churn) AS events,
          sum(value*churn) AS event_value
        FROM temp.main.{table} WHERE ({subset}) AND ({eligible}) GROUP BY {keys}
      ), ordered AS (
        SELECT *, coalesce(sum(n) OVER (ORDER BY {order}
          ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) AS above
        FROM cells
      ) SELECT coalesce(sum(n),0) AS eligible_n,
        coalesce(sum(CASE WHEN above+n<={k} THEN n ELSE 0 END),0) AS full_n,
        coalesce(sum(CASE WHEN above+n<={k} THEN events ELSE 0 END),0) AS full_events,
        coalesce(sum(CASE WHEN above+n<={k} THEN event_value ELSE 0 END),0) AS full_value,
        coalesce(sum(CASE WHEN above<{k} AND above+n>{k} THEN n ELSE 0 END),0) AS boundary_n,
        coalesce(sum(CASE WHEN above<{k} AND above+n>{k} THEN events ELSE 0 END),0) AS boundary_events,
        coalesce(sum(CASE WHEN above<{k} AND above+n>{k} THEN event_value ELSE 0 END),0) AS boundary_value
      FROM ordered''')
    contacts = min(k, result['eligible_n'])
    remaining = contacts - result['full_n']
    caught_exact = Fraction(result['full_events'])
    caught_value = result['full_value']
    if result['boundary_n']:
        share = Fraction(remaining, result['boundary_n'])
        caught_exact += share * result['boundary_events']
        caught_value += float(share) * result['boundary_value']
    else:
        assert remaining == 0
    precision_exact = caught_exact / contacts if contacts else Fraction(0)
    out = dict(population=base['n'], active_or_overall_churners=base['churners'],
               active_or_overall_churn_value=base['churn_value'],
               baseline_prevalence=base['prevalence'], capacity=k, eligible_n=result['eligible_n'],
               contacts=contacts, contact_fraction=divide(contacts, base['n']),
               caught=float(caught_exact), caught_value=caught_value,
               precision=float(precision_exact), recall=divide(float(caught_exact),base['churners']),
               value_recall=divide(caught_value,base['churn_value']),
               lift=divide(float(precision_exact),base['prevalence']))
    assert contacts == min(k,result['eligible_n'])
    assert -1e-10 <= out['caught'] <= contacts+1e-10
    assert -1e-10 <= out['recall'] <= 1+1e-10
    assert -1e-10 <= out['value_recall'] <= 1+1e-10
    return out, precision_exact


def independent_capture_check(table, subset, expected):
    """Reconstruct using row rank/count windows, then aggregate by status."""
    k = expected['capacity']
    groups = many(f'''WITH ranked AS (
        SELECT status, churn, value,
          rank() OVER (ORDER BY risk DESC) AS first_rank,
          count(*) OVER (PARTITION BY risk) AS tie_n
        FROM temp.main.{table} WHERE {subset}
      ), weighted AS (
        SELECT *, least(1.0,greatest(0.0,({k}-first_rank+1)*1.0/tie_n)) AS w
        FROM ranked
      ) SELECT status, sum(w) AS contacts, sum(w*churn) AS caught,
        sum(w*churn*value) AS caught_value FROM weighted GROUP BY status''')
    for key in ['contacts','caught','caught_value']:
        assert abs(sum(r[key] for r in groups)-expected[key]) < 1e-8
    return groups


query(f'''CREATE TEMP TABLE source AS SELECT
    "Call  Failure" AS failures, Complains AS complaint,
    "Subscription  Length" AS tenure, "Charge  Amount" AS charge,
    "Seconds of Use" AS seconds, "Frequency of use" AS calls,
    "Frequency of SMS" AS sms, "Distinct Called Numbers" AS distinct_calls,
    "Age Group" AS age_group, "Tariff Plan" AS tariff, Status AS status,
    Age AS age, "Customer Value" AS value, Churn AS churn
    FROM read_csv_auto('{SOURCE}')''')
query('CREATE TEMP TABLE source_dedup AS SELECT DISTINCT * FROM temp.main.source')
input_checks = {}
for variant, src in [('full','source'),('dedup','source_dedup')]:
    direct = totals(src,'true')
    grouped = one(f'''SELECT sum(n) AS n, sum(events) AS churners,
        sum(event_value) AS churn_value FROM (
          SELECT complaint,status,count(*) AS n,sum(churn) AS events,
            sum(value*churn) AS event_value
          FROM temp.main.{src} GROUP BY complaint,status)''')
    assert direct['n'] == grouped['n']
    assert direct['churners'] == grouped['churners']
    assert abs(direct['churn_value']-grouped['churn_value']) < 1e-8
    input_checks[variant] = dict(direct=direct, grouped=grouped,
        active=totals(src,'status=1'))

runs = []
for seed in SEEDS:
    for variant, src in [('full','source'),('dedup','source_dedup')]:
        query(f'''CREATE OR REPLACE TEMP TABLE base AS SELECT *,hash({FEATURES}) AS profile,
          CASE WHEN hash({FEATURES},{seed})%100<60 THEN 'train'
               WHEN hash({FEATURES},{seed})%100<80 THEN 'validation'
               ELSE 'test' END AS split FROM temp.main.{src}''')
        split = many('''SELECT split,count(*) AS n,sum(churn) AS churners,
            avg(churn) AS prevalence,count(DISTINCT profile) AS profiles
            FROM temp.main.base GROUP BY split ORDER BY split''')
        assert sum(s['n'] for s in split) == input_checks[variant]['direct']['n']
        assert sum(s['churners'] for s in split) == input_checks[variant]['direct']['churners']
        assert one('''SELECT count(*) AS n FROM (
            SELECT profile FROM temp.main.base GROUP BY profile HAVING count(DISTINCT split)>1)''')['n'] == 0
        params = one('''SELECT median(seconds) FILTER (WHERE seconds>0) AS positive_seconds_median,
            avg(churn) AS prior FROM temp.main.base WHERE split='train' ''')
        query(f'''CREATE OR REPLACE TEMP TABLE data AS SELECT *,
            CASE WHEN seconds=0 THEN 0 WHEN seconds<={params['positive_seconds_median']} THEN 1
            ELSE 2 END AS usage FROM temp.main.base''')
        validation = {}
        selection_keys = {}
        for name,dims in MODELS.items():
            keys = ','.join(dims)
            query(f'''CREATE OR REPLACE TEMP TABLE fit_{name} AS
                SELECT {keys}, count(*) AS n, sum(churn) AS events,
                  (sum(churn)+20*{params['prior']})/(count(*)+20) AS risk
                FROM temp.main.data WHERE split='train' GROUP BY {keys}''')
            formula_check = one(f'''SELECT max(abs(risk*(n+20)-events-20*{params['prior']})) AS residual,
                sum(n) AS n,sum(events) AS events FROM temp.main.fit_{name}''')
            assert formula_check['residual'] < 1e-10
            assert formula_check['n'] == next(s['n'] for s in split if s['split']=='train')
            assert formula_check['events'] == next(s['churners'] for s in split if s['split']=='train')
            query(f'''CREATE OR REPLACE TEMP TABLE pred_{name} AS
                SELECT d.*,coalesce(f.risk,{params['prior']}) AS risk
                FROM temp.main.data AS d LEFT JOIN temp.main.fit_{name} AS f USING ({keys})''')
            val = model_metrics(f'pred_{name}',"split='validation'")
            val['campaign20'], exact_precision = campaign(f'pred_{name}',"split='validation'",['risk'],'risk DESC')
            val['precision_exact_fraction'] = str(exact_precision)
            validation[name] = val
            selection_keys[name] = (exact_precision,val['auc'])
        winner = max(MODELS,key=lambda name: selection_keys[name])
        table = f'pred_{winner}'
        test = model_metrics(table,"split='test'")
        test['campaign20'],_ = campaign(table,"split='test'",['risk'],'risk DESC')
        verification = independent_capture_check(table,"split='test'",test['campaign20'])
        active = model_metrics(table,"split='test' AND status=1")
        active_policies = {}
        for policy,dims,ordering in [
            ('complaint_first',['complaint'],'complaint DESC'),
            ('low_seconds',['seconds'],'seconds ASC'),
            ('scorecard',['risk'],'risk DESC'),
            ('complaint_then_low_seconds',['complaint','seconds'],'complaint DESC,seconds ASC'),
        ]:
            active_policies[policy],_ = campaign(table,"split='test' AND status=1",dims,ordering)
        independent_capture_check(table,"split='test' AND status=1",active_policies['scorecard'])
        active['campaign20'] = active_policies['scorecard']
        service_cohort = totals(table,"split='test' AND status=1 AND complaint=1")
        service_cohort.update(contact_fraction=divide(service_cohort['n'],active['n']),
            recall=divide(service_cohort['churners'],active['churners']),
            value_recall=divide(service_cohort['churn_value'],active['churn_value']))
        service_capped,_ = campaign(table,"split='test' AND status=1",['complaint'],'complaint DESC','complaint=1')
        service_capped['was_capped'] = service_cohort['n'] > service_capped['capacity']
        k = active['n']//5
        baseline = dict(population=active['n'],churners=active['churners'],churn_value=active['churn_value'],
            contacts=k,contact_fraction=k/active['n'],precision=active['prevalence'],
            caught=k*active['prevalence'],recall=k/active['n'],value_recall=k/active['n'],
            caught_value=k/active['n']*active['churn_value'],lift=1.0)
        no_status = model_metrics('pred_complaint_usage',"split='test'")
        no_status['campaign20'],_ = campaign('pred_complaint_usage',"split='test'",['risk'],'risk DESC')
        run = dict(seed=seed,variant=variant,split=split,parameters=params,winner=winner,
            validation=validation,test=test,active_scorecard=active,active_baseline=baseline,
            active_policies=active_policies,service_complaint_cohort=service_cohort,
            service_only_capped=service_capped,no_status_test=no_status,
            independent_test_capture_by_status=verification)
        runs.append(run)
    print(f'Completed paired full/dedup seed {seed}',flush=True)


def stats(values):
    vals = np.array([v for v in values if v is not None],dtype=float)
    return dict(n=len(vals),mean=float(np.mean(vals)),median=float(np.median(vals)),
        min=float(np.min(vals)),max=float(np.max(vals)),p10=float(np.quantile(vals,.1)),
        p90=float(np.quantile(vals,.9)))


def summarize(objects,keys):
    return {key:stats([o[key] for o in objects]) for key in keys}


CAMPAIGN_KEYS = ['population','contacts','contact_fraction','caught','caught_value','precision','recall','value_recall','lift']
MODEL_KEYS = ['n','churners','prevalence','auc','brier','mean_prediction']
summary = {}
for variant in ['full','dedup']:
    subset = [r for r in runs if r['variant']==variant]
    entry = dict(selection_counts=dict(Counter(r['winner'] for r in subset)),
        test=summarize([r['test'] for r in subset],MODEL_KEYS),
        test_campaign20=summarize([r['test']['campaign20'] for r in subset],CAMPAIGN_KEYS),
        active_scorecard=summarize([r['active_scorecard'] for r in subset],MODEL_KEYS),
        active_baseline=summarize([r['active_baseline'] for r in subset],['population','churners','precision','recall','value_recall']),
        active_policies={p:summarize([r['active_policies'][p] for r in subset],CAMPAIGN_KEYS)
            for p in subset[0]['active_policies']},
        service_complaint_cohort=summarize([r['service_complaint_cohort'] for r in subset],
            ['n','churners','prevalence','contact_fraction','recall','value_recall']),
        service_only_capped=summarize([r['service_only_capped'] for r in subset],CAMPAIGN_KEYS),
        service_cap_split_count=sum(r['service_only_capped']['was_capped'] for r in subset),
        no_status_test=summarize([r['no_status_test'] for r in subset],MODEL_KEYS),
        no_status_campaign20=summarize([r['no_status_test']['campaign20'] for r in subset],CAMPAIGN_KEYS))
    entry['paired_active_minus_scorecard'] = {}
    for policy in ['complaint_first','low_seconds','complaint_then_low_seconds']:
        paired = {}
        for metric in ['precision','recall','value_recall']:
            values=[r['active_policies'][policy][metric]-r['active_policies']['scorecard'][metric] for r in subset]
            paired[metric]=stats(values)
            paired[metric].update(positive_splits=sum(x>1e-12 for x in values),
                negative_splits=sum(x < -1e-12 for x in values),tie_splits=sum(abs(x)<=1e-12 for x in values))
        entry['paired_active_minus_scorecard'][policy]=paired
    summary[variant]=entry

paired=[]
for seed in SEEDS:
    full=next(r for r in runs if r['seed']==seed and r['variant']=='full')
    dedup=next(r for r in runs if r['seed']==seed and r['variant']=='dedup')
    delta=dict(seed=seed,test={m:dedup['test'][m]-full['test'][m] for m in ['auc','brier','prevalence']},
        test_campaign20={m:dedup['test']['campaign20'][m]-full['test']['campaign20'][m]
            for m in ['precision','recall','value_recall']},
        active_policies={p:{m:dedup['active_policies'][p][m]-full['active_policies'][p][m]
            for m in ['precision','recall','value_recall']} for p in full['active_policies']})
    paired.append(delta)
summary['paired_dedup_minus_full'] = dict(
    test=summarize([r['test'] for r in paired],['auc','brier','prevalence']),
    test_campaign20=summarize([r['test_campaign20'] for r in paired],['precision','recall','value_recall']),
    active_policies={p:summarize([r['active_policies'][p] for r in paired],['precision','recall','value_recall'])
        for p in paired[0]['active_policies']})
summary['input_checks']=input_checks
summary['design']=dict(seeds=SEEDS,number_of_splits_per_variant=30,variants=['full','dedup'],
    usage='zero; positive through training positive-seconds median; above that median',
    prior_pseudo_observations=20,selection='exact rational validation expected precision@20%, then AUC, then original candidate order',
    tie_rule='uniform-random tie expectation with fractional boundary inclusion',
    capacity='floor(0.20*evaluation_population_n)',
    active_population='status=1',dedup='SELECT DISTINCT across all 13 predictors plus churn',
    repeated_split_intervals='descriptive p10/p90 across overlapping repeated splits, not confidence intervals',
    duckdb_version=duckdb.__version__)
(ROOT/'scratch/per_split_metrics.json').write_text(json.dumps(runs,indent=2,allow_nan=False)+'\n')
(ROOT/'scratch/paired_dedup_minus_full.json').write_text(json.dumps(paired,indent=2,allow_nan=False)+'\n')
(ROOT/'scratch/summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
query_log.close()
print(json.dumps({v:dict(selection=summary[v]['selection_counts'],
    auc=summary[v]['test']['auc'],brier=summary[v]['test']['brier'],
    precision=summary[v]['test_campaign20']['precision'],
    active_precision={p:summary[v]['active_policies'][p]['precision']['mean'] for p in summary[v]['active_policies']},
    active_value_recall={p:summary[v]['active_policies'][p]['value_recall']['mean'] for p in summary[v]['active_policies']})
    for v in ['full','dedup']},indent=2))
