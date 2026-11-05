"""Check 4: closure recovery and realistic midnight data-availability stress tests."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
from forecast_common import load_source, features, estimator, metrics

HERE=Path(__file__).resolve().parent
d=load_source()
eligible=d.operating & (d.day>='2017-12-29')
evaluation=d.operating & (d.day>='2018-04-01')
X0,B0=features(d)
matrices={0:(X0,B0)}
for latency in [1,6,24]:
    matrices[latency]=features(d,latency)

# Intervention test: a target day's unknown outcomes/status cannot change its forecasts.
invariance=[]
for origin in ['2018-04-15','2018-09-10','2018-11-15']:
    changed=d.copy()
    changed.loc[changed.day>=origin,'y']=99999
    changed.loc[changed.day>=origin,'operating']=False
    for latency in [0,1,6,24]:
        a,b=features(changed,latency)
        mask=d.day==origin
        pd.testing.assert_frame_equal(a.loc[mask],matrices[latency][0].loc[mask])
        pd.testing.assert_frame_equal(b.loc[mask],matrices[latency][1].loc[mask])
        invariance.append({'origin':origin,'delay_hours':latency,'passed':True})
# Explicit cutoff check for every same-hour lag, including last hour of yesterday.
for latency,(X,B) in matrices.items():
    for lag_hours in [24,48,168]:
        ready=d.index-pd.Timedelta(hours=lag_hours)+pd.Timedelta(hours=latency+1)
        forbidden=ready>d.day
        assert X.loc[forbidden,f'lag_{lag_hours}'].isna().all()

predictions={}
monthly=[]
removed_columns=[]
for latency,(X,B) in matrices.items():
    for baseline in B:
        predictions[(latency,baseline)]=B[baseline].copy()
    model_pred=pd.Series(np.nan,index=d.index)
    aware_pred=pd.Series(np.nan,index=d.index)
    for start in pd.date_range('2018-04-01','2018-11-01',freq='MS'):
        stop=start+pd.offsets.MonthBegin(1)
        test=evaluation & (d.day>=start)&(d.day<stop)
        # Only labels whose observation interval + processing delay has completed.
        train=eligible & ((d.index+pd.Timedelta(hours=latency+1))<=start)
        clean_model=estimator().fit(X0.loc[train],d.loc[train,'y'])
        model_pred.loc[test]=np.maximum(0,clean_model.predict(X.loc[test]))
        if latency:
            usable=X.columns[X.loc[train].notna().any()]
            removed_columns.append({'delay_hours':latency,'month':str(start.date())[:7],
                'dropped_all_missing':list(X.columns.difference(usable))})
            aware_model=estimator().fit(X.loc[train,usable],d.loc[train,'y'])
            aware_pred.loc[test]=np.maximum(0,aware_model.predict(X.loc[test,usable]))
        else:
            aware_pred.loc[test]=model_pred.loc[test]
        monthly.append({'delay_hours':latency,'month':str(start.date())[:7],
            'model':'hgb_unadapted',**metrics(d.loc[test,'y'],model_pred.loc[test])})
    predictions[(latency,'hgb_unadapted')]=model_pred
    predictions[(latency,'hgb_latency_trained')]=aware_pred

reopen=d.operating & ~d.operating.shift(1,fill_value=True)
event=reopen.cumsum()
last_closed=pd.Series(d.index,index=d.index).where(~d.operating).ffill()
hours_since=(pd.Series(d.index,index=d.index)-last_closed).dt.total_seconds()/3600
after=d.operating & hours_since.between(1,24)

overall=[]
groups=[]
closure=[]
for (latency,name),p in predictions.items():
    overall.append({'delay_hours':latency,'model':name,**metrics(d.loc[evaluation,'y'],p.loc[evaluation])})
    for label,group in [('00–17',d.hour<18),('18–23',d.hour>=18),('after_closure24',after),('other_operating',~after)]:
        mask=evaluation&group
        groups.append({'delay_hours':latency,'model':name,'group':label,**metrics(d.loc[mask,'y'],p.loc[mask])})
    if latency==0:
        g=d.loc[evaluation,['day','hour','weekend','season','rain','y']].copy()
        g['after']=after.loc[evaluation]
        g['ae']=(g.y-p.loc[evaluation]).abs()
        g['prediction']=p.loc[evaluation]
        for axes in [['season','hour','weekend'],['season','hour','weekend','wet']]:
            g['wet']=g.rain>0
            cells=g.groupby(axes+['after']).agg(n=('ae','size'),ae=('ae','mean'),y=('y','mean')).unstack('after')
            cells=cells.dropna()
            w=cells[('n',True)]
            closure.append({'model':name,'matching':'+'.join(axes),
                'matched_post_hours':int(w.sum()),'matched_normal_hours':int(cells[('n',False)].sum()),
                'post_mae':float((w*cells[('ae',True)]).sum()/w.sum()),
                'normal_mae_at_post_mix':float((w*cells[('ae',False)]).sum()/w.sum()),
                'post_rentals_mean':float((w*cells[('y',True)]).sum()/w.sum()),
                'normal_rentals_at_post_mix':float((w*cells[('y',False)]).sum()/w.sum())})

masked=[]
for latency,(X,B) in matrices.items():
    masked.append({'delay_hours':latency,'lag24_missing_pct':float(100*X.loc[evaluation,'lag_24'].isna().mean()),
        'lag48_missing_pct':float(100*X.loc[evaluation,'lag_48'].isna().mean()),
        'prior_day_mean_missing_pct':float(100*X.loc[evaluation,'prior_day_mean'].isna().mean()),
        'all_baseline_predictions_finite':bool(np.isfinite(B.loc[evaluation]).all().all())})

out={'scope':{'start':'2018-04-01','end':'2018-11-30','n':int(evaluation.sum()),
        'post_closure_n':int((evaluation&after).sum()),'normal_n':int((evaluation&~after).sum()),
        'reopening_events_in_evaluation':int(reopen.loc[evaluation].sum()),
        'post_closure_dates':int(d.loc[evaluation&after,'day'].nunique()),
        'normal_dates':int(d.loc[evaluation&~after,'day'].nunique())},
    'overall':overall,'subgroups':groups,'matched_closure':closure,'monthly_hgb':monthly,
    'missing_history':masked,'leakage_checks':invariance,'removed_training_columns':removed_columns,
    'assumptions':'Delay L means hourly interval available at interval end+L hours. Issue00:00. Labels for refits obey same cutoff. Unadapted trains clean-history features but receives delayed features at scoring; latency-trained uses delayed features in train and score. Both monthly expanding, fixed hyperparameters. Delays are scenarios, not measured actual latency.'}
# Independent pooled error check using monthly group sums for default model.
p=predictions[(0,'hgb_unadapted')]
check=d.loc[evaluation,['day','y']].assign(ae=(d.loc[evaluation,'y']-p.loc[evaluation]).abs())
monthly_sums=check.groupby(check.day.dt.to_period('M')).agg(ae=('ae','sum'),n=('ae','size'),y=('y','sum'))
out['independent_check']={'mae':float(monthly_sums.ae.sum()/monthly_sums.n.sum()),'wape_pct':float(100*monthly_sums.ae.sum()/monthly_sums.y.sum())}
assert abs(out['independent_check']['mae']-next(x['mae'] for x in overall if x['delay_hours']==0 and x['model']=='hgb_unadapted'))<1e-9
(HERE/'closure_latency_results.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'scope':out['scope'],'overall':overall,'matched_closure':closure,'missing_history':masked,'independent_check':out['independent_check']},indent=2))
