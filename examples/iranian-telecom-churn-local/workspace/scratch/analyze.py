from pathlib import Path
import json, subprocess
from decimal import Decimal
import duckdb
ROOT=Path(__file__).resolve().parent
con=duckdb.connect()
SOURCE='/hal-light/examples/iranian-telecom-churn-local/question/data.csv'
def q(name, sql):
    (ROOT/f'{name}.sql').write_text(sql)
    r=con.execute(sql)
    if r.description:return [dict(zip([x[0] for x in r.description], [float(v) if isinstance(v, Decimal) else v for v in row])) for row in r.fetchall()]
def log(s):
    stamp=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
    with (ROOT.parent/'run_log.md').open('a') as f:f.write(f'\n## {stamp}\n{s}\n')
q('source',f'''CREATE TEMP VIEW main.source AS SELECT
"Call  Failure" failures, "Complains" complaints, "Subscription  Length" tenure,
"Charge  Amount" charge, "Seconds of Use" usage_seconds, "Frequency of use" calls,
"Frequency of SMS" sms, "Distinct Called Numbers" contacts,
"Age Group" age_group, "Tariff Plan" tariff, "Status" status, "Age" age,
"Customer Value" customer_value, "Churn" churn
FROM read_csv_auto('{SOURCE}');''')
q('features','''CREATE TEMP VIEW main.features AS SELECT *,
 hash(failures,complaints,tenure,charge,usage_seconds,calls,sms,contacts,age_group,tariff,status,age,customer_value)%10 bucket,
 CASE WHEN usage_seconds=0 THEN '0' WHEN usage_seconds<1500 THEN '1–1499' WHEN usage_seconds<4000 THEN '1500–3999' ELSE '4000+' END usage_bin,
 CASE WHEN failures=0 THEN '0' WHEN failures<10 THEN '1–9' ELSE '10+' END failure_bin,
 CASE WHEN tenure<24 THEN '<24' WHEN tenure<36 THEN '24–35' ELSE '36+' END tenure_bin,
 CASE WHEN age<30 THEN '<30' WHEN age<40 THEN '30–39' ELSE '40+' END age_bin,
 CASE WHEN customer_value<200 THEN '<200' WHEN customer_value<500 THEN '200–499' ELSE '500+' END value_bin
FROM main.source''')
out={}
out['quality']=q('quality','''SELECT count(*) n,sum(churn) churners,avg(churn) churn_rate,
 count(*)-count(DISTINCT (failures,complaints,tenure,charge,usage_seconds,calls,sms,contacts,age_group,tariff,status,age,customer_value,churn)) exact_duplicate_excess,
 count(*) FILTER (WHERE failures IS NULL OR complaints IS NULL OR tenure IS NULL OR charge IS NULL OR usage_seconds IS NULL OR calls IS NULL OR sms IS NULL OR contacts IS NULL OR age_group IS NULL OR tariff IS NULL OR status IS NULL OR age IS NULL OR customer_value IS NULL OR churn IS NULL) missing_rows,
 min(customer_value) min_value,max(customer_value) max_value,min(tenure) min_tenure,max(tenure) max_tenure
FROM main.source''')
out['split']=q('split',"SELECT CASE WHEN bucket<6 THEN 'train' WHEN bucket<8 THEN 'validation' ELSE 'test' END split,count(*) n,sum(churn) churners FROM main.features GROUP BY 1")
profile=[]
for col in ['complaints','failure_bin','tenure_bin','usage_bin','tariff','status','age_bin','value_bin','age_group']:
    rows=q('profile_'+col,f"SELECT '{col}' dimension,cast({col} as varchar) bin_label,count(*) n,sum(churn) churners,avg(churn) rate,avg(customer_value) mean_value FROM main.features GROUP BY 1,2 HAVING count(*)>=10 ORDER BY 2")
    profile+=rows
out['profiles']=profile
out['status_complaints']=q('status_complaints','SELECT status,complaints,count(*) n,sum(churn) churners,avg(churn) rate FROM main.features GROUP BY 1,2 HAVING count(*)>=10 ORDER BY 1,2')
log('Source profile, split and all eight diagnostic dimensions computed; instruments scratch/source.sql, features.sql, quality.sql, split.sql, profile_*.sql. No field dictionary or timestamps provided: retain status code labels rather than asserting active/inactive semantics. Exact duplicate profiles kept as possibly distinct customers but split together by predictor fingerprint, preventing identical X crossing partitions. No raw rows leave DuckDB.')
# Candidate lookup scorecards; low-count cells shrink to global prior, with minimum support.
candidates={'complaint':'complaints','complaint_usage':'complaints,usage_bin','complaint_usage_failures':'complaints,usage_bin,failure_bin','complaint_usage_tenure':'complaints,usage_bin,tenure_bin'}
def scoring(name,cols,training='bucket<6'):
    joins=' AND '.join(f'f.{x}=c.{x}' for x in cols.split(','))
    q('fit_'+name,f'''CREATE OR REPLACE TEMP VIEW main.fit_{name} AS SELECT {cols},count(*) n,sum(churn) y,
 (sum(churn)+20*(SELECT avg(churn) FROM main.features WHERE {training}))/(count(*)+20) probability
 FROM main.features WHERE {training} GROUP BY {cols}''')
    q('score_'+name,f'''CREATE OR REPLACE TEMP VIEW main.score_{name} AS SELECT f.*,
 CASE WHEN c.n>=20 THEN c.probability ELSE (SELECT avg(churn) FROM main.features WHERE {training}) END p
 FROM main.features f LEFT JOIN main.fit_{name} c ON {joins}''')
for name,cols in candidates.items():scoring(name,cols)
def evaluate(name,view,pop,rank='p',budgets=(.05,.1,.2,.3),label=''):
    base=f'SELECT *,{rank} score FROM {view} WHERE {pop}'
    metrics=q('metrics_'+name+label,f'''WITH d AS ({base}),g AS (SELECT p,count(*) n,sum(churn) y FROM d GROUP BY p),
 a AS (SELECT *,sum(n-y) OVER(ORDER BY p ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) lower_negative FROM g)
 SELECT (SELECT count(*) FROM d) n,(SELECT sum(churn) FROM d) churners,
 (SELECT avg((churn-p)^2) FROM d) brier,
 sum(y*(coalesce(lower_negative,0)+(n-y)/2.0))/(sum(y)*sum(n-y)) auc FROM a''')[0]
    curves=[]
    for frac in budgets:
        sql=f'''WITH d AS ({base}),g AS (SELECT score,count(*) n,sum(churn) y,sum(customer_value) v,sum(churn*customer_value) yv,sum(CASE WHEN complaints=1 THEN 1 ELSE 0 END) complainants FROM d GROUP BY score),
 a AS (SELECT *,coalesce(sum(n) OVER(ORDER BY score DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) preceding_n FROM g),
 w AS (SELECT *,greatest(0,least(1.0,({frac}*(SELECT count(*) FROM d)-preceding_n)/n)) weight FROM a)
 SELECT {frac} capacity,sum(n*weight) selected,sum(y*weight) caught,sum((n-y)*weight) false_positives,
 sum(y*weight)/sum(n*weight) AS precision,sum(y*weight)/(SELECT sum(churn) FROM d) recall,
 sum(v*weight) selected_value,sum(yv*weight) churn_value,sum(yv*weight)/(SELECT sum(churn*customer_value) FROM d) value_recall,
 sum(complainants*weight) selected_complainants FROM w'''
        curves+=q('budget_'+name+label+'_'+str(frac).replace('.','_'),sql)
    return {'metrics':metrics,'curves':curves}
out['validation']={name:evaluate(name,'main.score_'+name,'bucket>=6 AND bucket<8') for name in candidates}
chosen=max(candidates,key=lambda x:out['validation'][x]['curves'][2]['precision'])
out['selected']=chosen
log('Four predeclared scorecards fitted using train only; 20-observation prior shrinkage and fallback for cells with <20 train records. Selected by validation precision at 20% capacity: '+chosen+'. Validation is used for model choice only; test unopened until selection. Instruments fit_*.sql, score_*.sql, metrics_*.sql and budget_*.sql.')
out['test']=evaluate(chosen+'_test','main.score_'+chosen,'bucket>=8')
out['test_value']=evaluate(chosen+'_value','main.score_'+chosen,'bucket>=8',rank='p*customer_value')
out['test_complaint']=evaluate('complaint_test','main.score_complaint','bucket>=8')
# Every status code shown without assuming semantics. This is eligibility sensitivity.
out['status_test']={str(status):evaluate(chosen+'_status'+str(status),'main.score_'+chosen,f'bucket>=8 AND status={status}') for status in [1,2]}
out['scorecard']=q('scorecard_export',f'SELECT * FROM main.fit_{chosen} WHERE n>=20 ORDER BY probability DESC')
out['test_calibration']=q('calibration',f'''SELECT p,count(*) n,sum(churn) churners,avg(churn) rate FROM main.score_{chosen} WHERE bucket>=8 GROUP BY p HAVING count(*)>=10 ORDER BY p DESC''')
out['risk_value_mix']=q('risk_value_mix',f'''SELECT usage_bin,complaints,count(*) n,sum(churn) churners,avg(churn) rate,avg(customer_value) mean_value FROM main.features GROUP BY 1,2 HAVING count(*)>=10 ORDER BY 1,2''')
out['independent']=q('independent',f'''WITH grouped AS (SELECT complaints,status,count(*) n,sum(churn) y FROM main.source GROUP BY 1,2), testg AS (SELECT p,count(*) n,sum(churn) y FROM main.score_{chosen} WHERE bucket>=8 GROUP BY p)
SELECT (SELECT sum(n) FROM grouped) total_n,(SELECT sum(y) FROM grouped) total_churn,
(SELECT sum(n) FROM testg) test_n,(SELECT sum(y) FROM testg) test_churn''')
assert out['independent'][0]['total_n']==out['quality'][0]['n']
assert out['independent'][0]['total_churn']==out['quality'][0]['churners']
assert out['independent'][0]['test_churn']==out['test']['metrics']['churners']
for group in [out['test'],out['test_value'],out['test_complaint'],*out['status_test'].values()]:
    for row in group['curves']:
        assert abs(row['selected']-row['caught']-row['false_positives'])<1e-8
        assert abs(row['selected']-group['metrics']['n']*row['capacity'])<1e-8
log('Final test and flip cuts computed. Status-code-specific targeting and risk × customer_value ranking expose the operational trade-off. Independent grouped recomputation agrees with total and test churn counts; every targeting confusion decomposition and capacity total reconciles within 1e-8. Instruments metrics_*_test.sql, budget_*.sql, independent.sql. Test results are retrospective classification, not estimated treatment benefit.')

q('unique_test_view',f'CREATE TEMP VIEW main.unique_scores AS SELECT DISTINCT * FROM main.score_{chosen}')
out['dedup_test']=evaluate('dedup_test','main.unique_scores','bucket>=8')
for col,expr in [('call_frequency',"CASE WHEN calls<100 THEN '<100' WHEN calls<250 THEN '100–249' ELSE '250+' END"),('sms_frequency',"CASE WHEN sms=0 THEN '0' WHEN sms<100 THEN '1–99' ELSE '100+' END")]:
    out['profiles']+=q('profile_'+col,f"SELECT '{col}' dimension,{expr} bin_label,count(*) n,sum(churn) churners,avg(churn) rate,avg(customer_value) mean_value FROM main.features GROUP BY 1,2 HAVING count(*)>=10 ORDER BY 2")
out['validation_selection']=[{'name':name,'precision20':v['curves'][2]['precision'],'auc':v['metrics']['auc']} for name,v in out['validation'].items()]
# Independent capacity calculation sums every score's higher-score peers without a window.
out['budget_independent']=q('budget_independent',f'''WITH g AS (SELECT p,count(*) n,sum(churn) y FROM main.score_{chosen} WHERE bucket>=8 GROUP BY p),
w AS (SELECT a.*,greatest(0,least(1.0,(120-coalesce((SELECT sum(b.n) FROM g b WHERE b.p>a.p),0))/a.n)) weight FROM g a)
SELECT sum(n*weight) selected,sum(y*weight) caught FROM w''')
assert abs(out['budget_independent'][0]['caught']-out['test']['curves'][2]['caught'])<1e-8
log('Independent capacity computation using correlated higher-score sums agrees with 20% test capture. Deduplicated-test weight sensitivity added without model refit; all usage proxies (seconds, call frequency, SMS) profiled. Earlier parser errors from reserved aliases seconds/value/level/precision were resolved by safe aliases; a Decimal/float assertion error was fixed with numeric normalization. Failed runs did not imply missing data. All final outputs regenerated successfully.')

(ROOT/'results.json').write_text(json.dumps(out,indent=2,default=str))
print(json.dumps({k:out[k] for k in ['quality','split','selected','test','test_value','status_test']},indent=2))
