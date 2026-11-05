"""Shared in-memory source/features for the authorized follow-up; no import side effects."""
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

SOURCE = Path('/hal-light/examples/seoul-bike-sharing-demand/question/data.csv')

def load_source():
    sql=f'''SELECT strptime("Date", '%d/%m/%Y')::DATE AS day,
        "Hour"::INTEGER AS hour,"Rented Bike Count"::DOUBLE AS y,
        "Functioning Day"='Yes' AS operating,"Holiday"='Holiday' AS holiday,
        "Seasons" AS season,"Temperature"::DOUBLE AS temp,
        "Rainfall"::DOUBLE AS rain,"Humidity"::DOUBLE AS humidity,
        "Wind speed"::DOUBLE AS wind,"Snowfall"::DOUBLE AS snow
        FROM read_csv('{SOURCE}',all_varchar=true) ORDER BY day,hour'''
    d=duckdb.connect().execute(sql).df()
    d['day']=pd.to_datetime(d.day)
    d.index=pd.DatetimeIndex(d.day+pd.to_timedelta(d.hour,unit='h'))
    d['weekend']=d.day.dt.dayofweek>=5
    d['dow']=d.day.dt.dayofweek
    d['block']=np.select([d.hour<=5,d.hour<=9,d.hour<=16,d.hour<=20],['00–05','06–09','10–16','17–20'],default='21–23')
    assert d.index.equals(pd.date_range(d.index.min(),d.index.max(),freq='h'))
    return d

def features(d, delay_hours=0):
    """Hourly count is available at interval end plus processing delay; issue at midnight."""
    f=pd.DataFrame(index=d.index)
    f['hour']=d.hour
    f['dow']=d.day.dt.dayofweek
    f['month']=d.day.dt.month
    f['holiday']=d.holiday.astype(int)
    f['annual_sin']=np.sin(2*np.pi*d.day.dt.dayofyear/365.25)
    f['annual_cos']=np.cos(2*np.pi*d.day.dt.dayofyear/365.25)
    obs=d.y.where(d.operating)
    def lag(days):
        available=(d.index-pd.Timedelta(days=days)+pd.Timedelta(hours=1+delay_hours))<=d.day
        return obs.shift(days*24).where(available)
    for days in [1,2,7]:
        f[f'lag_{days*24}']=lag(days)
    prior=pd.concat({i:lag(i) for i in range(1,29)},axis=1)
    f['recent_hour_mean']=prior.loc[:,1:7].mean(axis=1)
    f['recent_hour_std']=prior.loc[:,1:7].std(axis=1)
    f['recent_weekday_mean']=prior.loc[:,[7,14,21,28]].mean(axis=1)
    daytype=pd.concat({i:prior[i].where(d.weekend.shift(i*24)==d.weekend) for i in range(1,29)},axis=1).mean(axis=1)
    # Prior day's observations available at midnight after the specified latency.
    daily=d.assign(obs=obs.where(d.hour+1+delay_hours<=24)).groupby('day').obs.mean()
    f['prior_day_mean']=d.day.map(daily.shift(1)).to_numpy()
    baselines=pd.DataFrame({'recent7':f.recent_hour_mean,'daytype28':daytype,
        'weekday4':f.recent_weekday_mean},index=d.index)
    # Prespecified fallback for empty strata; rolling same-hour mean is also cutoff-safe.
    fallback=prior.mean(axis=1)
    baselines=baselines.apply(lambda s:s.fillna(fallback))
    return f,baselines

def estimator():
    return HistGradientBoostingRegressor(max_iter=180,max_leaf_nodes=15,
        learning_rate=.06,l2_regularization=10,min_samples_leaf=25,
        early_stopping=False,random_state=42)

def metrics(y,p):
    y,p=np.asarray(y,dtype=float),np.asarray(p,dtype=float)
    assert len(y)==len(p) and len(y)>0 and np.isfinite(p).all()
    return {'n':len(y),'actual_mean':float(y.mean()),'predicted_mean':float(p.mean()),
        'mae':float(np.abs(y-p).mean()),'rmse':float(np.sqrt(np.mean((y-p)**2))),
        'wape_pct':float(100*np.abs(y-p).sum()/y.sum()),'bias_pct':float(100*(p-y).sum()/y.sum())}
