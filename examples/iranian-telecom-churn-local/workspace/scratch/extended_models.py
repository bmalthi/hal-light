"""User-requested local modeling checks; only aggregate metrics are persisted."""
import json
from pathlib import Path
from collections import Counter

import duckdb
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT.parent/'question/data.csv'
SEEDS=range(20261105,20261135)
con=duckdb.connect()
source_sql=f'''CREATE TEMP TABLE raw AS SELECT
 "Call  Failure" AS failures, Complains AS complaint,
 "Subscription  Length" AS tenure,"Charge  Amount" AS charge,
 "Seconds of Use" AS seconds,"Frequency of use" AS calls,
 "Frequency of SMS" AS sms,"Distinct Called Numbers" AS distinct_calls,
 "Age Group" AS age_group,"Tariff Plan" AS tariff,Status AS status,
 Age AS age,"Customer Value" AS value,Churn AS churn
 FROM read_csv_auto('{SOURCE}')'''
con.execute(source_sql)
features='failures,complaint,tenure,charge,seconds,calls,sms,distinct_calls,age_group,tariff,status,age,value'
# The only unit-level objects are these in-memory arrays. Nothing serializes them.
fields=['failures','complaint','tenure','charge','seconds','calls','sms','distinct_calls','tariff','status','value','churn']
core=['complaint','status','seconds']
expanded=['complaint','status','seconds','failures','tenure','charge','calls','sms','distinct_calls','tariff']


def campaign(y,p,v,rate=.2):
    n=len(y); k=int(n*rate)
    if k==0 or y.sum()==0:
        raise ValueError('Evaluation population too small')
    # Outcome-blind uniform selection within tied prediction cells at boundary.
    _,inv,count=np.unique(-p,return_inverse=True,return_counts=True)
    above=np.r_[0,np.cumsum(count)[:-1]]
    fraction=np.minimum(count,np.maximum(0,k-above))/count
    w=fraction[inv]
    assert abs(w.sum()-k)<1e-7
    caught=float(w@y); churn_value=float(y@v)
    return {'population':n,'churners':int(y.sum()),'contacts':k,
            'caught':caught,'false_positives':k-caught,'precision':caught/k,
            'recall':caught/y.sum(),'value_recall':float(w@(y*v)/churn_value),
            'mean_prediction':float(w@p/k),'lift':caught/k/(y.sum()/n)}


def evaluate(y,p,v):
    return {'n':len(y),'churners':int(y.sum()),'prevalence':float(y.mean()),
            'auc':float(roc_auc_score(y,p)),'ap':float(average_precision_score(y,p)),
            'brier':float(brier_score_loss(y,p)),
            'bias':float(np.mean(p-y)),
            'campaign':campaign(y,p,v)}


def pick(preds,y,v):
    return max(range(len(preds)),key=lambda i:(campaign(y,preds[i],v)['precision'],roc_auc_score(y,preds[i])))


def cell_scores(x,y,train,val,test):
    cut=float(np.median(x['seconds'][train & (x['seconds']>0)]))
    use=np.where(x['seconds']==0,0,np.where(x['seconds']<=cut,1,2))
    keys=[x['complaint'].astype(int),x['complaint'].astype(int)*3+use,
          (x['complaint'].astype(int)*3+use)*2+(x['status']==2)]
    prior=float(y[train].mean()); candidates=[]
    for key in keys:
        sums=np.bincount(key[train],weights=y[train],minlength=12)
        counts=np.bincount(key[train],minlength=12)
        rates=(sums+20*prior)/(counts+20)
        candidates.append(rates[key])
    i=pick([p[val] for p in candidates],y[val],x['value'][val])
    return candidates[i][val],candidates[i][test],{'variant':i,'seconds_cut':cut},None


def matrix(x,cols,logarithms=False):
    arrays=[]
    for f in cols:
        a=x[f].copy()
        if f in ['status','tariff']: a=(a==2).astype(float)
        elif logarithms and f in ['seconds','failures','calls','sms','distinct_calls']: a=np.log1p(a)
        arrays.append(a)
    return np.column_stack(arrays)


def fit_family(family,x,y,train,val,test):
    if family=='scorecard':return cell_scores(x,y,train,val,test)
    cols=core if family.endswith('core') else expanded
    is_log=family.startswith('logistic')
    a=matrix(x,cols,is_log)
    candidates=[]; validation=[]; configs=[]
    if is_log:
        for c in [.01,.1,1,10]:
            model=make_pipeline(StandardScaler(),LogisticRegression(C=c,max_iter=2000,solver='lbfgs'))
            model.fit(a[train],y[train]); candidates.append(model)
            validation.append(model.predict_proba(a[val])[:,1]); configs.append({'C':c})
    else:
        for depth in [2,3,4,5]:
            for leaf in [20,50]:
                model=DecisionTreeClassifier(max_depth=depth,min_samples_leaf=leaf,random_state=901)
                model.fit(a[train],y[train]); candidates.append(model)
                validation.append(model.predict_proba(a[val])[:,1]); configs.append({'depth':depth,'leaf':leaf})
    i=pick(validation,y[val],x['value'][val])
    return validation[i],candidates[i].predict_proba(a[test])[:,1],configs[i],candidates[i]


def logit(p):
    p=np.clip(p,1e-6,1-1e-6)
    return np.log(p/(1-p)).reshape(-1,1)


runs=[]; calibration_bins=[]; checks=[]
for version in ['full','deduplicated']:
    con.execute('CREATE OR REPLACE TEMP TABLE data AS SELECT '+('DISTINCT ' if version=='deduplicated' else '')+'* FROM raw')
    # Source-dependent split labels are assigned inside DuckDB, never inferred from outcomes.
    x=con.execute('SELECT '+','.join(fields)+f',hash({features}) AS profile FROM data').fetchnumpy()
    y=x['churn'].astype(int); v=x['value'].astype(float)
    checks.append({'version':version,'n':len(y),'churners':int(y.sum()),'profiles':len(np.unique(x['profile']))})
    for seed in SEEDS:
        split=con.execute(f'SELECT hash({features},{seed})%100 AS split FROM data').fetchnumpy()['split']
        train=split<60; val=(split>=60)&(split<80); test=split>=80
        assert not set(x['profile'][train]) & set(x['profile'][test])
        assert not set(x['profile'][val]) & set(x['profile'][test])
        active=x['status'][test]==1
        for family in ['scorecard','logistic_core','tree_core','logistic_expanded','tree_expanded']:
            pv,pt,config,model=fit_family(family,x,y,train,val,test)
            calibrator=LogisticRegression(C=1e6,max_iter=2000)
            calibrator.fit(logit(pv),y[val])
            pc=calibrator.predict_proba(logit(pt))[:,1]
            out={'version':version,'seed':seed,'family':family,'config':config,
                 'train_n':int(train.sum()),'validation_n':int(val.sum()),'test_n':int(test.sum()),
                 'validation_precision':campaign(y[val],pv,v[val])['precision'],
                 'calibration_slope':float(calibrator.coef_[0,0]),
                 'raw':evaluate(y[test],pt,v[test]),'calibrated':evaluate(y[test],pc,v[test]),
                 'active_raw':evaluate(y[test][active],pt[active],v[test][active]),
                 'active_calibrated':evaluate(y[test][active],pc[active],v[test][active])}
            runs.append(out)
            # Aggregate fixed probability bands; no individual scores leave memory.
            for stage,p in [('raw',pt),('calibrated',pc)]:
                for lo,hi in [(0,.1),(.1,.3),(.3,.6),(.6,1.000001)]:
                    mask=(p>=lo)&(p<hi)
                    if mask.any():
                        calibration_bins.append({'version':version,'seed':seed,'family':family,'stage':stage,'lo':lo,'hi':min(1,hi),'n':int(mask.sum()),'events':int(y[test][mask].sum()),'sum_prediction':float(p[mask].sum())})
        print(f'{version} seed {seed}: completed',flush=True)


def distribution(a):
    a=np.asarray(a,dtype=float)
    return {k:float(v) for k,v in zip(['mean','median','min','p10','p90','max'],[a.mean(),np.median(a),a.min(),*np.quantile(a,[.1,.9]),a.max()])}


def get_metric(r,stage,metric):
    return r[stage]['campaign'][metric] if metric in ['precision','recall','value_recall','false_positives','caught'] else r[stage][metric]


summaries=[]
metrics=['auc','ap','brier','bias','precision','recall','value_recall','false_positives','caught']
for version in ['full','deduplicated']:
    for family in ['scorecard','logistic_core','tree_core','logistic_expanded','tree_expanded']:
        group=[r for r in runs if r['version']==version and r['family']==family]
        summaries.append({'version':version,'family':family,
          'selected_configs':dict(Counter(json.dumps(r['config'],sort_keys=True) for r in group)),
          'stages':{stage:{metric:distribution([get_metric(r,stage,metric) for r in group]) for metric in metrics} for stage in ['raw','calibrated','active_raw','active_calibrated']}})
paired=[]
for family in ['scorecard','logistic_core','tree_core','logistic_expanded','tree_expanded']:
    full=[r for r in runs if r['version']=='full' and r['family']==family]
    dedup=[r for r in runs if r['version']=='deduplicated' and r['family']==family]
    baseline=[r for r in runs if r['version']=='full' and r['family']=='scorecard']
    for comparison,a,b,s1,s2 in [('dedup_minus_full',dedup,full,'raw','raw'),('calibrated_minus_raw',full,full,'calibrated','raw'),('active_calibrated_minus_raw',full,full,'active_calibrated','active_raw'),('minus_scorecard',full,baseline,'raw','raw'),('active_minus_scorecard',full,baseline,'active_raw','active_raw')]:
        for metric in ['auc','brier','bias','precision','recall','value_recall']:
            delta=[get_metric(ra,s1,metric)-get_metric(rb,s2,metric) for ra,rb in zip(a,b)]
            assert all(ra['seed']==rb['seed'] for ra,rb in zip(a,b))
            paired.append({'family':family,'comparison':comparison,'metric':metric,'distribution':distribution(delta),'positive_splits':int(np.sum(np.array(delta)>1e-10)),'negative_splits':int(np.sum(np.array(delta)<-1e-10))})
# Independent direct totals versus SQL aggregate; no record outputs.
assert checks[0]['n']==con.execute('SELECT count(*) FROM raw').fetchone()[0]
assert checks[0]['churners']==con.execute('SELECT sum(churn) FROM raw').fetchone()[0]
results={'design':{'seeds':list(SEEDS),'split_percentages':[60,20,20],'tie_method':'uniform random boundary expectation','core_features':core,'expanded_features':expanded,'calibration':'logistic of clipped prediction logit, fit on validation only'},'checks':checks,'runs':runs,'summary':summaries,'paired':paired,'calibration_bins':calibration_bins}
(ROOT/'scratch/extended_results.json').write_text(json.dumps(results,indent=2))
(ROOT/'scratch/extended_source.sql').write_text(source_sql+';\n-- Split expression: hash('+features+', <seed>) % 100.\n-- Full and SELECT DISTINCT * variants are temporary, in-memory only.\n')
print('Saved aggregate extended_results.json; no row-level files created.')
