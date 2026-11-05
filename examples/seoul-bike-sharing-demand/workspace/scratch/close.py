from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parents[1]; a=json.loads((R/'scratch/results.json').read_text())
assert a['quality_all'][0]['other_nulls']==0
assert sum(r['rentals'] for r in a['season'])==a['quality'][0]['rentals']
assert len(a['next_day'])==24
stamp=subprocess.check_output(['date','-u','+%Y-%m-%dT%H:%M:%SZ'],text=True).strip()
with (R/'run_log.md').open('a') as f:
 f.write('\n## '+stamp+'\nCoverage check against prompt: hour/season diagnosis -> first profiles and seasonal peak table; weather/holiday/functioning -> weather and closure sections; deployable forecast -> calendar rule, input-availability table and full next-day curve; operational metrics -> chronological MAE/RMSE/WAPE/bias and coverage/headroom; service/staffing/rebalancing -> seasonal pilot and station-data requirements; misleading-model risks/drift -> watch items. All requested analytical pieces covered.\nStrict verify_brief.py passes. Palette validation passes. Independent total, MAE/WAPE and season sum checks pass. Visual QA: initial sandbox Chrome returned exit 134 with no output; approved local headless render succeeded. Inspected top 3,600px and remaining forecast/recommendation/method sections via scratch/qa-lower.html preview; no overlap/clipping or truncated values. Browser stopped after each screenshot. Only aggregate results, code and QA artifacts retained; no raw extract.\n')
print('Coverage, independent checks and visual QA logged.')
