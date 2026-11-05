"""Additional aggregate checks and calibration summaries, without unit records."""
import json
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parent
r=json.loads((root/'extended_results.json').read_text())
output=[]
for version in ['full','deduplicated']:
    for family in ['scorecard','logistic_core','tree_core','logistic_expanded','tree_expanded']:
        subset=[x for x in r['runs'] if x['version']==version and x['family']==family]
        o={'version':version,'family':family,'calibration':{}}
        for stage in ['raw','calibrated']:
            eces=[]
            for run in subset:
                bins=[b for b in r['calibration_bins'] if b['version']==version and b['family']==family and b['stage']==stage and b['seed']==run['seed']]
                assert sum(b['n'] for b in bins)==run['test_n']
                assert sum(b['events'] for b in bins)==run[stage]['churners']
                eces.append(sum(abs(b['sum_prediction']-b['events']) for b in bins)/run['test_n'])
            o['calibration'][stage]={'mean_absolute_bias':float(np.mean([abs(x[stage]['bias']) for x in subset])),
                'mean_band_ece':float(np.mean(eces)),
                'mean_top20_bias':float(np.mean([x[stage]['campaign']['mean_prediction']-x[stage]['campaign']['precision'] for x in subset]))}
        o['calibration']['brier_improved_splits']=sum(x['calibrated']['brier']<x['raw']['brier'] for x in subset)
        output.append(o)
# Family comparisons on identical split, budget and source-weighting conditions.
for version in ['full','deduplicated']:
    for seed in r['design']['seeds']:
        group=[x for x in r['runs'] if x['version']==version and x['seed']==seed]
        assert len(set((x['test_n'],x['raw']['churners'],x['active_raw']['n'],x['active_raw']['churners']) for x in group))==1
        for x in group:
            assert x['train_n']+x['validation_n']+x['test_n']==(3150 if version=='full' else 2850)
            assert abs(x['raw']['campaign']['precision']-x['calibrated']['campaign']['precision'])<1e-10
            assert abs(x['raw']['campaign']['recall']-x['raw']['campaign']['caught']/x['raw']['churners'])<1e-10
(root/'extended_calibration_summary.json').write_text(json.dumps(output,indent=2))
print(json.dumps([x for x in output if x['version']=='full'],indent=2))
