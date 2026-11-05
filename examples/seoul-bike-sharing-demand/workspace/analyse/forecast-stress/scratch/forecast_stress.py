"""Forward model comparison and sequential workload envelopes; aggregates-only writes."""
from pathlib import Path
import sys
import json
import math
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
PARENT=HERE.parents[2]
sys.path.insert(0,str(PARENT/'scratch'))
from forecast_common import load_source,features,estimator,metrics

d=load_source()
last_closed=pd.Series(d.index.where(~d.operating),index=d.index).ffill()
d['post_closure24']=d.operating&((d.index-last_closed)>pd.Timedelta(0))&((d.index-last_closed)<=pd.Timedelta(hours=24))
X,B=features(d)
names=['recent7','daytype28','weekday4','hgb_expanding','hgb_rolling90']
p=B.copy()
p['hgb_expanding']=np.nan
p['hgb_rolling90']=np.nan
models={}
train_info=[]
for start in pd.date_range('2018-03-01','2018-11-01',freq='MS'):
    end=start+pd.offsets.MonthBegin(1)
    target=(d.day>=start)&(d.day<end)
    for name in names[3:]:
        lower=max(pd.Timestamp('2017-12-29'),start-pd.Timedelta(days=90)) if name=='hgb_rolling90' else pd.Timestamp('2017-12-29')
        train=d.operating&(d.day>=lower)&(d.day<start)
        mod=estimator()
        mod.fit(X.loc[train],d.loc[train,'y'])
        p.loc[target,name]=np.maximum(0,mod.predict(X.loc[target]))
        train_info.append({'model':name,'forecast_month':str(start.date())[:7],'train_first':str(d.loc[train,'day'].min().date()),'train_last':str(d.loc[train,'day'].max().date()),'train_n':int(train.sum())})
        models[name]=mod

score=d.operating&(d.day>='2018-04-01')
assert p.loc[score,names].notna().all().all()
pooled={name:metrics(d.loc[score,'y'],p.loc[score,name]) for name in names}
best_baseline=min(names[:3],key=lambda x:pooled[x]['mae'])
best_model=min(names,key=lambda x:pooled[x]['mae'])
rows=d.loc[score,['day','hour','y','season','weekend','block','holiday','rain','post_closure24']].copy()
rows[names]=p.loc[score,names]

def grouped_scores(key,series):
    return [{key:str(k),'model':name,**metrics(g.y,g[name])} for k,g in rows.groupby(series) for name in names]

out={'design':{'prediction_start':'2018-03-01','scoring_start':'2018-04-01','scoring_end':'2018-11-30','best_baseline_by_pooled_mae':best_baseline,'best_candidate_by_pooled_mae':best_model,'exploratory':True},
     'training_windows':train_info,'pooled':pooled,
     'monthly':grouped_scores('month',rows.day.dt.to_period('M')),
     'seasonal':grouped_scores('season',rows.season),
     'daytype':grouped_scores('weekend',rows.weekend),
     'blocks':grouped_scores('block',rows.block),
     'oct_nov':{name:metrics(rows.loc[rows.day>='2018-10-01','y'],rows.loc[rows.day>='2018-10-01',name]) for name in names}}

# Paired circular-free moving blocks of seven consecutive calendar dates.
rng=np.random.default_rng(42)
boots={}
for name in names:
    if name==best_baseline:continue
    temp=rows.assign(gain=(rows.y-rows[best_baseline]).abs()-(rows.y-rows[name]).abs())
    daily=temp.groupby('day').agg(gain=('gain','sum'),n=('gain','size')).reindex(pd.date_range('2018-04-01','2018-11-30'),fill_value=0)
    estimates=[]
    for _ in range(2000):
        starts=rng.integers(0,len(daily)-6,math.ceil(len(daily)/7))
        indexes=np.concatenate([np.arange(s,s+7) for s in starts])[:len(daily)]
        sample=daily.iloc[indexes]
        estimates.append(sample.gain.sum()/sample.n.sum())
    boots[name]={'reference':best_baseline,'mae_gain':float(temp.gain.mean()),'ci95':np.quantile(estimates,[.025,.975]).tolist(),'block_days':7,'replicates':2000}
out['paired_bootstrap']=boots
out['reconciliation']={name:{'direct_mae':pooled[name]['mae'],'monthly_rebuilt_mae':float(sum(r['mae']*r['n'] for r in out['monthly'] if r['model']==name)/pooled[name]['n'])} for name in names}
out['monthly_wins']={name:sum(name==min([r for r in out['monthly'] if r['month']==month],key=lambda z:z['mae'])['model'] for month in sorted({r['month'] for r in out['monthly']})) for name in names}
print(json.dumps({'pooled':pooled,'best_baseline':best_baseline,'monthly_wins':out['monthly_wins']}),flush=True)

def quantile90(values):
    return float(np.sort(values)[min(len(values),math.ceil((len(values)+1)*.9))-1])

def envelope_metrics(g):
    y,u=g.y.to_numpy(),g.upper.to_numpy()
    return {'n':len(g),'actual_mean':float(y.mean()),'upper_mean':float(u.mean()),'coverage_pct':float(100*np.mean(y<=u)),
        'shortfall_pct':float(100*np.maximum(y-u,0).sum()/y.sum()),
        'unused_headroom_mean':float(np.maximum(u-y,0).mean()),
        'pinball90':float(np.maximum(.9*(y-u),.1*(u-y)).mean()),
        'fallback_pct':float(100*g.fallback.mean())}

out['envelopes']=[]
# Compare all models; no tuning or filtering by observed test performance.
for name in names:
    resid=(d.y-p[name]).where(d.operating&(d.day>='2018-03-01'))
    for recipe in ['fixed_march_block','rolling28_block','rolling56_block_daytype']:
        upper=pd.Series(np.nan,index=d.index)
        fallback=pd.Series(False,index=d.index)
        for day in pd.date_range('2018-04-01','2018-11-30'):
            target=(d.day==day)
            if recipe=='fixed_march_block':
                past=(d.day>='2018-03-01')&(d.day<'2018-04-01')
            else:
                window=28 if recipe=='rolling28_block' else 56
                past=(d.day>=day-pd.Timedelta(days=window))&(d.day<day)
            valid=past&resid.notna()
            assert d.loc[valid,'day'].max()<day
            for block in d.block.unique():
                t=target&(d.block==block)
                cell=valid&(d.block==block)
                if recipe=='rolling56_block_daytype':
                    cell&=(d.weekend==(day.dayofweek>=5))
                selected=resid.loc[cell].to_numpy()
                pooled_fallback=False
                if len(selected)<30:
                    pooled_fallback=True
                    selected=resid.loc[valid&(d.block==block)].to_numpy()
                if len(selected)<30:
                    selected=resid.loc[valid].to_numpy()
                assert len(selected)>=30
                offset=max(0,quantile90(selected))
                upper.loc[t]=p.loc[t,name]+offset
                fallback.loc[t]=pooled_fallback
        eg=rows[['day','hour','y','weekend','block','holiday','rain','post_closure24']].copy()
        eg['upper']=upper.loc[score]
        eg['fallback']=fallback.loc[score]
        assert eg.upper.notna().all()
        detail={'model':name,'recipe':recipe,'overall':envelope_metrics(eg),
            'monthly':[{'month':str(k),**envelope_metrics(g)} for k,g in eg.groupby(eg.day.dt.to_period('M'))],
            'daytype':[{'weekend':bool(k),**envelope_metrics(g)} for k,g in eg.groupby('weekend')],
            'blocks':[{'block':k,**envelope_metrics(g)} for k,g in eg.groupby('block')],
            'holiday':[{'holiday':bool(k),**envelope_metrics(g)} for k,g in eg.groupby('holiday')],
            'rain':[{'wet':bool(k),**envelope_metrics(g)} for k,g in eg.groupby(eg.rain>0)],
            'post_closure':[{'post_closure24':bool(k),**envelope_metrics(g)} for k,g in eg.groupby('post_closure24')],
            'oct_nov':envelope_metrics(eg.loc[eg.day>='2018-10-01'])}
        out['envelopes'].append(detail)

# Historical forecast extension: all source rows retained only in memory.
future_day=d.day.max()+pd.Timedelta(days=1)
future=pd.DataFrame({'day':future_day,'hour':range(24),'y':np.nan,'operating':True,'holiday':False,'weekend':True},index=pd.date_range(future_day,periods=24,freq='h'))
fX,fB=features(pd.concat([d,future]))
fX,fB=fX.iloc[-24:],fB.iloc[-24:]
future['block']=np.select([future.hour<=5,future.hour<=9,future.hour<=16,future.hour<=20],['00–05','06–09','10–16','17–20'],default='21–23')
for name in names:
    if name in models:
        lower=max(pd.Timestamp('2017-12-29'),future_day-pd.Timedelta(days=90)) if name=='hgb_rolling90' else pd.Timestamp('2017-12-29')
        train=d.operating&(d.day>=lower)&(d.day<future_day)
        final_model=estimator().fit(X.loc[train],d.loc[train,'y'])
        future[name]=np.maximum(0,final_model.predict(fX))
    else:
        future[name]=fB[name]
future['daytype28_rolling28_upper']=np.nan
resid=(d.y-p['daytype28']).where(d.operating&(d.day>='2018-03-01'))
for block in future.block.unique():
    past=(d.day>=future_day-pd.Timedelta(days=28))&(d.day<future_day)&(d.block==block)&resid.notna()
    r=resid.loc[past].to_numpy()
    assert len(r)>=30
    future.loc[future.block==block,'daytype28_rolling28_upper']=future.loc[future.block==block,'daytype28']+max(0,quantile90(r))
out['dec1_scenario']={'date':'2018-12-01','assumptions':'Operating nonholiday Saturday; previous day finalized at midnight; HGB refit at Dec 1 using data through Nov 30, consistent with monthly policy; no observed outcome; historical illustration only. Upper column averages hourly envelopes, not a block-total quantile.',
    'daily_totals':{name:float(future[name].sum()) for name in names},
    'blocks':[{'block':b,'hours':len(g),**{name:float(g[name].mean()) for name in names},'daytype28_rolling28_upper':float(g.daytype28_rolling28_upper.mean())} for b,g in future.groupby('block')]}
(HERE/'results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'paired_bootstrap':boots,'envelopes':[{'model':r['model'],'recipe':r['recipe'],**r['overall']} for r in out['envelopes']]}),flush=True)
