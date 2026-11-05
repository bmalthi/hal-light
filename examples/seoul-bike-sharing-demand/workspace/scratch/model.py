"""Day-ahead backtest; input records stay in memory; outputs are aggregates only."""
from pathlib import Path
import json
import math
import duckdb
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parent
SOURCE = '/hal-light/examples/seoul-bike-sharing-demand/question/data.csv'
SQL = f'''SELECT strptime("Date", '%d/%m/%Y')::DATE AS day,
"Hour"::INTEGER AS hour, "Rented Bike Count"::DOUBLE AS y,
"Functioning Day" = 'Yes' AS operating, "Holiday" = 'Holiday' AS holiday,
"Temperature" AS temp, "Humidity" AS humidity, "Rainfall" AS rain,
"Snowfall" AS snow, "Wind speed" AS wind, "Visibility" AS visibility,
"Dew point temperature" AS dew, "Solar Radiation" AS solar
FROM read_csv('{SOURCE}', all_varchar=true) ORDER BY day, hour'''
(ROOT / 'model_input.sql').write_text(SQL)
df = duckdb.connect().execute(SQL).df()
df['day'] = pd.to_datetime(df.day)
assert not df.duplicated(['day', 'hour']).any()
assert len(df) == (df.day.max() - df.day.min()).days * 24 + 24
df.index = df.day + pd.to_timedelta(df.hour, unit='h')
assert df.index.equals(pd.date_range(df.index.min(), df.index.max(), freq='h'))
WEATHER = ['temp', 'humidity', 'rain', 'snow', 'wind', 'visibility', 'dew', 'solar']
df[WEATHER] = df[WEATHER].astype(float)

def features(data):
    f = pd.DataFrame(index=data.index)
    f['hour'] = data.hour
    f['dow'] = data.day.dt.dayofweek
    f['month'] = data.day.dt.month
    f['holiday'] = data.holiday.astype(int)
    f['annual_sin'] = np.sin(2 * np.pi * data.day.dt.dayofyear / 365.25)
    f['annual_cos'] = np.cos(2 * np.pi * data.day.dt.dayofyear / 365.25)
    observed = data.y.where(data.operating)
    for lag in [24, 48, 168]:
        f[f'lag_{lag}'] = observed.shift(lag)
    shifted = pd.concat([observed.shift(24 * i) for i in range(1, 8)], axis=1)
    f['recent_hour_mean'] = shifted.mean(axis=1)
    f['recent_hour_std'] = shifted.std(axis=1)
    f['recent_weekday_mean'] = pd.concat([observed.shift(168 * i) for i in range(1, 5)], axis=1).mean(axis=1)
    daily = data.assign(obs=observed).groupby('day').obs.mean()
    f['prior_day_mean'] = data.day.map(daily.shift(1)).to_numpy()
    return f

X = features(df)
Xoracle = pd.concat([X, df[WEATHER]], axis=1)
eligible = df.operating & (df.day >= df.day.min() + pd.Timedelta(days=28))

def fit_predict(name, train, target):
    if name == 'prior_week':
        return X.loc[target, 'lag_168'].fillna(X.loc[target, 'recent_hour_mean']).to_numpy()
    if name == 'recent_7_days':
        return X.loc[target, 'recent_hour_mean'].to_numpy()
    matrix = Xoracle if name == 'observed_weather_oracle' else X
    model = HistGradientBoostingRegressor(max_iter=180, max_leaf_nodes=15,
        learning_rate=0.06, l2_regularization=10, min_samples_leaf=25,
        early_stopping=False, random_state=42)
    model.fit(matrix.loc[train], df.loc[train, 'y'])
    return np.maximum(0, model.predict(matrix.loc[target])), model

def metrics(y, pred):
    y, pred = np.asarray(y), np.asarray(pred)
    return {'n': len(y), 'actual_mean': float(y.mean()), 'predicted_mean': float(pred.mean()),
        'mae': float(mean_absolute_error(y, pred)), 'rmse': float(np.sqrt(mean_squared_error(y, pred))),
        'wape_pct': float(np.abs(y-pred).sum()/y.sum()*100),
        'bias_pct': float((pred-y).sum()/y.sum()*100)}

NAMES = ['prior_week', 'recent_7_days', 'calendar_history', 'observed_weather_oracle']
validation_parts = {name: [] for name in NAMES}
validation = []
for start, end in [('2018-07-01','2018-08-01'), ('2018-08-01','2018-09-01')]:
    train = eligible & (df.day < start)
    target = eligible & (df.day >= start) & (df.day < end)
    for name in NAMES:
        result = fit_predict(name, train, target)
        pred = result[0] if isinstance(result, tuple) else result
        validation.append({'month': start[:7], 'model': name, **metrics(df.loc[target,'y'], pred)})
        validation_parts[name].append((df.loc[target,'y'].to_numpy(), pred))
pooled = {name: metrics(np.concatenate([p[0] for p in parts]), np.concatenate([p[1] for p in parts])) for name, parts in validation_parts.items()}
selected = min(NAMES[:3], key=lambda n: pooled[n]['mae'])
# Choice is made using July/August only, before computing any final test metrics.
selection = {'selected': selected, 'criterion': 'pooled July/August operating-hour MAE', 'validation': validation, 'pooled': pooled}
(ROOT/'model_selection.json').write_text(json.dumps(selection, indent=2))
print(json.dumps(selection), flush=True)

train = eligible & (df.day < '2018-09-01')
cal = eligible & (df.day >= '2018-09-01') & (df.day < '2018-10-01')
test = (df.day >= '2018-10-01')
optest = test & df.operating
all_preds, models = {}, {}
for name in NAMES:
    result = fit_predict(name, train, test | cal)
    if isinstance(result, tuple):
        pred, models[name] = result
    else:
        pred = result
    all_preds[name] = pd.Series(pred, index=df.index[test | cal])

def block(hour):
    return np.select([hour <= 5, hour <= 9, hour <= 16, hour <= 20], ['00–05','06–09','10–16','17–20'], default='21–23')

df['block'] = block(df.hour)
cal_residual = df.loc[cal, 'y'] - all_preds[selected].loc[cal]
cal_offsets = {}
for b in sorted(df.block.unique()):
    r = cal_residual.loc[df.loc[cal,'block'] == b]
    rank = min(len(r), math.ceil((len(r)+1)*0.9))
    cal_offsets[b] = float(np.sort(r)[rank-1])

point = all_preds[selected].loc[test]
upper = np.maximum(point, point + df.loc[test, 'block'].map(cal_offsets))
result = df.loc[test, ['day','hour','y','operating','block','rain','holiday']].copy()
result['point'] = point
result['upper'] = upper
result['baseline'] = all_preds['recent_7_days'].loc[test]

def planning(g):
    y, p, u = g.y.to_numpy(), g.point.to_numpy(), g.upper.to_numpy()
    return {**metrics(y,p), 'upper_mean': float(u.mean()), 'coverage_pct': float((y <= u).mean()*100),
        'shortfall_pct': float(np.maximum(y-u,0).sum()/y.sum()*100),
        'unused_headroom_mean': float(np.maximum(u-y,0).mean()),
        'pinball90': float(np.maximum(.9*(y-u),-.1*(y-u)).mean()),
        'actual_p90': float(np.quantile(y,.9))}

summary = {**selection, 'split': {'train_start': str(df.loc[train,'day'].min().date()), 'train_end': str(df.loc[train,'day'].max().date()),
    'train_n':int(train.sum()), 'cal_n':int(cal.sum()), 'test_n':int(test.sum()), 'test_operating_n':int(optest.sum())},
    'test': {name: metrics(df.loc[optest,'y'], preds.loc[optest]) for name,preds in all_preds.items()},
    'calibration_offsets': cal_offsets,
    'planning_all': planning(result[result.operating]),
    'planning_blocks': [{'block': k, **planning(g)} for k,g in result[result.operating].groupby('block')],
    'test_months': [{'month': str(k), **planning(g)} for k,g in result[result.operating].groupby(result[result.operating].day.dt.to_period('M'))],
    'test_rain': [{'wet': bool(k), **planning(g)} for k,g in result[result.operating].groupby(result[result.operating].rain > 0)],
    'test_holiday': [{'holiday':bool(k), **planning(g)} for k,g in result[result.operating].groupby('holiday')],
    'test_weekend': [{'weekend':bool(k), **planning(g)} for k,g in result[result.operating].groupby(result[result.operating].day.dt.dayofweek >= 5)]}
# Compare over all hours only as a scenario where service schedule was known.
for name, preds in all_preds.items():
    gated = preds.loc[test].where(df.loc[test,'operating'],0)
    summary.setdefault('known_schedule_all_hours',{})[name] = metrics(df.loc[test,'y'],gated)
# Independently recompute error totals via daily sums.
daily_errors = result[result.operating].assign(ae=lambda x:(x.y-x.point).abs()).groupby('day').agg(ae=('ae','sum'),y=('y','sum'),n=('y','size'))
summary['independent_check'] = {'mae':float(daily_errors.ae.sum()/daily_errors.n.sum()),'wape_pct':float(100*daily_errors.ae.sum()/daily_errors.y.sum()),'total_rentals':float(daily_errors.y.sum())}
# Day-block bootstrap quantifies holdout uncertainty conditional on the fitted model.
rng = np.random.default_rng(42)
g = result[result.operating].copy()
g['gain'] = (g.y-g.baseline).abs()-(g.y-g.point).abs()
daily_gain = g.groupby('day').agg(gain=('gain','sum'),n=('gain','size'))
boot=[]
for _ in range(2000):
    a=daily_gain.iloc[rng.integers(0,len(daily_gain),len(daily_gain))]
    boot.append(a.gain.sum()/a.n.sum())
summary['mae_gain_vs_recent7_daily_bootstrap'] = {'gain':float(g.gain.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist(),'days':len(daily_gain)}
# Seven-calendar-day moving blocks retain short-range weather/event dependence.
by_calendar = daily_gain.reindex(pd.date_range('2018-10-01','2018-11-30'),fill_value=0)
boot=[]
for _ in range(2000):
    starts=rng.integers(0,len(by_calendar)-6,math.ceil(len(by_calendar)/7))
    indices=np.concatenate([np.arange(s,s+7) for s in starts])[:len(by_calendar)]
    a=by_calendar.iloc[indices]
    boot.append(a.gain.sum()/a.n.sum())
summary['mae_gain_vs_recent7_week_block_bootstrap']={'gain':float(g.gain.mean()),'ci95':np.quantile(boot,[.025,.975]).tolist(),'block_days':7}
# Diagnostic baseline envelope, with the identical calibration recipe, no test tuning.
baseline_offsets={}
baseline_resid=df.loc[cal,'y']-all_preds['recent_7_days'].loc[cal]
for b in sorted(df.block.unique()):
    r=baseline_resid.loc[df.loc[cal,'block']==b]
    baseline_offsets[b]=float(np.sort(r)[min(len(r),math.ceil((len(r)+1)*.9))-1])
bg=result[result.operating].copy()
bg['point']=bg.baseline
bg['upper']=np.maximum(bg.point,bg.point+bg.block.map(baseline_offsets))
summary['baseline_envelope']={'offsets':baseline_offsets,'all':planning(bg),
    'blocks':[{'block':b,**planning(g)} for b,g in bg.groupby('block')]}
# Historical next-day illustration beyond the source endpoint, not a present-day forecast.
future_day = df.day.max()+pd.Timedelta(days=1)
future = pd.DataFrame({'day':future_day,'hour':range(24),'y':np.nan,'operating':True,'holiday':False}, index=pd.date_range(future_day,periods=24,freq='h'))
fX = features(pd.concat([df,future])).iloc[-24:]
if selected in models:
    fp = np.maximum(0,models[selected].predict(fX))
elif selected == 'recent_7_days':
    fp = fX.recent_hour_mean.to_numpy()
else:
    fp = fX.lag_168.fillna(fX.recent_hour_mean).to_numpy()
future['point'] = fp
future['block'] = block(future.hour)
future['upper'] = np.maximum(fp,fp+future.block.map(cal_offsets))
future['baseline']=fX.recent_hour_mean.to_numpy()
future['baseline_upper']=np.maximum(future.baseline,future.baseline+future.block.map(baseline_offsets))
summary['next_day_scenario'] = {'date':str(future_day.date()),'assumptions':'Operating throughout; nonholiday; forecasts issued at midnight after previous day complete. Frozen pre-September model and September buffers. Historical illustration only.',
    'total_point':float(future.point.sum()), 'baseline_total':float(future.baseline.sum()),
    'blocks':[{'block':b,'hours':len(g),'point_per_hour':float(g.point.mean()),'upper_per_hour':float(g.upper.mean()),'point_total':float(g.point.sum()),'baseline_per_hour':float(g.baseline.mean()),'baseline_upper_per_hour':float(g.baseline_upper.mean())} for b,g in future.groupby('block')]}
(ROOT/'model_results.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k not in ['validation','pooled']}),flush=True)
