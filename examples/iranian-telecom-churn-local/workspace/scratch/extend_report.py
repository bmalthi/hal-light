"""Assemble requested robustness evidence into the canonical memo."""
import html
import json
import re
import subprocess


def extend(document,root):
    scratch=root/'scratch'; repo=root.parents[2]
    r=json.loads((scratch/'extended_results.json').read_text())
    p=json.loads((root/'analyse/robustness/scratch/summary.json').read_text())
    c=json.loads((scratch/'extended_calibration_summary.json').read_text())
    s={(x['version'],x['family']):x['stages'] for x in r['summary']}
    labels={'scorecard':'Scorecard','logistic_core':'Logistic: 3 inputs','tree_core':'Shallow tree: 3 inputs','logistic_expanded':'Logistic: 10 inputs','tree_expanded':'Shallow tree: 10 inputs'}
    pct=lambda x:f'{100*x:.1f}%'
    pp=lambda x:f'{100*x:+.2f} pp'
    rng=lambda a:f"{pct(a['p10'])}–{pct(a['p90'])}"
    def table(head,rows):
        esc=lambda x:html.escape(str(x))
        return '<table class="bridge"><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(v)+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table>'
    def mean(f,metric,stage='raw',version='full'):
        return s[version,f][stage][metric]['mean']
    # Independent agreement between the model-memory and aggregate-SQL paths.
    for metric in ['precision','recall','value_recall']:
        assert abs(mean('scorecard',metric)-p['full']['test_campaign20'][metric]['mean'])<1e-10
        assert abs(mean('scorecard',metric,'active_raw')-p['full']['active_policies']['scorecard'][metric]['mean'])<1e-10
    spec={'id':'repeated_precision','form':'hbar','width':700,'pad_l':190,
          'title':'Richer models improve predictive precision',
          'subtitle':'Mean across 30 grouped splits • 20% of all test records contacted • uniform tie expectation',
          'value_format':'{:.1%}','x_domain':[0,.8],
          'rows':[{'label':label,'value':mean(f,'precision')} for f,label in labels.items()]}
    (scratch/'repeated_chart_spec.json').write_text(json.dumps(spec,indent=2))
    subprocess.run(['uv','run','--no-sync',str(repo/'.claude/skills/dataviz/scripts/render.py'),str(scratch/'repeated_chart_spec.json'),'--out-dir',str(scratch/'charts'),'--single-mode','light'],check=True)
    svg=(scratch/'charts/repeated_precision.svg').read_text()
    svg=re.sub(r'<\?xml[^>]*\?>','',svg)
    sections=[]
    sections.append('''<h2>The scorecard is stable enough to benchmark, but leaves predictive gains available</h2>
<p><b>Thirty grouped train/validation/test splits</b> test stability, model capacity, calibration and duplicate sensitivity. The same predictor profiles remain together, and every model in a split sees the same held-out records. All settings and probability calibration are fitted without test outcomes. Results below use <b>mean performance across splits</b>; ranges are the 10th–90th percentiles. They describe sensitivity to splitting, <b>not confidence intervals</b>: tests overlap and the dataset has already been explored.</p>
<p>The scorecard averages <b>54.3% precision</b> (48.1–59.1%) and <b>70.3% recall</b> (66.0–74.5%) at a 20% all-account contact cap. Its complete recall range is 62.9–77.9%. The original 74.0% single-split recall is plausible, but sits toward the favorable end of this distribution. Boundary ties are averaged exactly rather than allowing a lucky tie seed to decide performance.</p>
<p>Compare models first on the same three inputs—complaints, status and call seconds—then expand to ten behavioral inputs. The expanded models add failures, tenure, charge, call frequency, SMS, distinct called numbers and tariff. Age and the undocumented value index are excluded from risk fitting; value remains an evaluation weight. Logistic models use regularization and log transforms for usage/counts; shallow trees learn a small number of interactions. Neither model family is tuned on test.</p>''')
    sections.append(f'<figure class="fig">{svg}<figcaption>Every value is repeated in the table. Selection quality does not measure treatment benefit.</figcaption></figure>')
    sections.append(table(['Model','AUC','Precision','Precision range','Recall','Value captured'],[[label,f"{mean(f,'auc'):.3f}",pct(mean(f,'precision')),rng(s['full',f]['raw']['precision']),pct(mean(f,'recall')),pct(mean(f,'value_recall'))] for f,label in labels.items()]))
    sections.append('''<p>The ten-input logistic model improves precision by <b>5.65 percentage points</b> and recall by <b>7.39 points</b> versus the scorecard on average, with positive differences on all 30 matched splits. That is consistency across resamples, not 30 independent demonstrations. The three-input shallow tree also improves recall and value capture, so the gain is not solely from collecting more features. Expanded trees capture more of the churn-associated value index than expanded logistic models, despite similar overall precision; model choice depends on the operational objective.</p>
<h2>Duplicate removal preserves the model comparison</h2>
<p>Repeat the complete fit, validation selection and test pipeline on <b>2,850 exact distinct rows</b>, keeping each profile in the same partition as in the full-data counterpart. Contradictory-label profiles remain grouped; no outcome is used to split them. Deduplication changes both training and evaluation weights, so the difference is a sensitivity result—not a pure improvement in training.</p>''')
    sections.append(table(['Model','Full precision','Dedup precision','Full recall','Dedup recall'],[[label,pct(mean(f,'precision')),pct(mean(f,'precision',version='deduplicated')),pct(mean(f,'recall')),pct(mean(f,'recall',version='deduplicated'))] for f,label in labels.items()]))
    sections.append('''<p>Scorecard precision changes by <b>−0.56 points</b> on average; expanded-logistic precision changes by <b>−0.01 points</b>. The richer-model advantage therefore does not depend on the exact duplicate rows. Without customer IDs, neither keeping nor removing matching rows can establish the true number of independent customers.</p>
<h2>Calibration helps the scorecard’s probabilities, not its ranking</h2>
<p>A sigmoid calibration model is fitted to each selected model’s validation predictions and evaluated on the separate test subset. The same validation subset selects model settings and fits calibration; it never becomes test data. Lower Brier score means lower mean squared probability error. The table reports mean test error before and after calibration.</p>''')
    sections.append(table(['Model','Raw Brier','Calibrated Brier','Splits improved / 30'],[[label,f"{mean(f,'brier'):.4f}",f"{mean(f,'brier','calibrated'):.4f}",next(x for x in c if x['version']=='full' and x['family']==f)['calibration']['brier_improved_splits']] for f,label in labels.items()]))
    sections.append('''<p>The scorecard underpredicts the selected top fifth’s churn by <b>9.95 points</b> on average; calibration changes that to <b>1.10 points of overprediction</b>. Its mean absolute overall calibration bias falls from <b>2.16 to 1.68 points</b>, and fixed-band calibration error falls from <b>2.93 to 2.70 points</b>. Brier improves in <b>25 / 30</b> splits. In contrast, all four logistic/tree alternatives have slightly worse mean Brier after this calibration step; do not apply it automatically. All fitted calibration slopes are positive, so rankings, precision and recall are unchanged. These checks do not establish calibration on future accounts.</p>
<h2>Among active customers, combine complaints with usage</h2>
<p>For an operational retention comparison, allocate <b>20% of each active test population</b> to every rule—87–101 contacts, about 94 on average. This is a different denominator from the all-account table. Each active test subset has only <b>12–38 churn events</b>; precision and recall remain variable. The model alternatives are trained and tuned on all accounts, then restricted to active accounts for this evaluation; dedicated active-only fitting is not claimed.</p>''')
    active=[]
    for key,label in [('complaint_first','Complaints first, then random'),('low_seconds','Lowest call seconds'),('scorecard','Scorecard'),('complaint_then_low_seconds','Complaints, then lowest seconds')]:
        a=p['full']['active_policies'][key]
        active.append([label,pct(a['precision']['mean']),rng(a['precision']),pct(a['recall']['mean']),pct(a['value_recall']['mean'])])
    for f in ['logistic_core','tree_core','logistic_expanded','tree_expanded']:
        a=s['full',f]['active_raw']
        active.append([labels[f],pct(a['precision']['mean']),rng(a['precision']),pct(a['recall']['mean']),pct(a['value_recall']['mean'])])
    sections.append(table(['Active targeting rule','Precision','Precision range','Recall','Value captured'],active))
    sections.append('''<p><b>Complaints followed by low call seconds</b> improves active precision by <b>3.01 points</b> and recall by <b>11.44 points</b> over the scorecard, with positive differences in all 30 splits, both with and without exact duplicates. Low usage alone has lower value capture than the scorecard in every full-data split. The ten-input logistic model adds further breadth: <b>81.2% active-churn recall</b> versus 62.8% for the scorecard, but still only <b>20.8% precision</b>. Roughly four in five contacts therefore have observed non-churn labels.</p>
<p>The three-input shallow tree is a useful competing candidate: <b>80.4% active-churn recall</b> and <b>83.9% capture of the churn-associated value index</b>, versus 81.2% and 68.9% for expanded logistic. Its larger index capture does not establish higher profit. Prospective validation should compare these objectives after defining true margin.</p>
<p><b>A small service-only cohort is a different trade-off.</b> Contacting only active complainants averages <b>16 contacts</b>, or <b>3.4% of active accounts</b>, with <b>68.8% observed churn</b> and <b>45.1% active-churn recall</b>. Its churn fraction ranges from 52.9% to 84.8% across the middle 80% of splits; the cap never binds. This supports it as a focused service-recovery experiment, but it misses over half of active churn. Do not compare its precision with full-budget rules as if contact volume were equal.</p>
<p><b>Policy implication:</b> begin with the focused service pilot; if seeking broader coverage, test a complaints-then-low-usage outreach rule and compare the three-input tree and expanded logistic as predictive challengers. Broader contact is not a reason to send blanket discounts. Reserve offers for randomized, margin-qualified treatment tests and retain ordinary service for everyone.</p>
<h2>Three operational questions need data this file does not contain</h2>''')
    sections.append(table(['Check worth doing','Why it could change the call','Why it cannot be completed here'],[
        ['Status and timing audit','Establish whether non-active accounts are still reachable/retainable and whether each predictor existed before campaign assignment.','The CSV has one summarized Status value, no customer ID, dated feature snapshots, status-change or churn timestamps, contactability fields, or campaign-assignment date. UCI describes a nominal nine-to-twelve-month design; that does not verify row-level timing or eligibility.'],
        ['Validate customer value and margin','Choose economically worthwhile interventions and assess whether index-weighted capture reflects future profit.','No authoritative value formula, currency/unit definition, longitudinal revenue, contribution margin, service cost, offer cost or redemption data is supplied. The index can be profiled but cannot be validated as future cash margin.'],
        ['Measure intervention effectiveness','Distinguish customers whose churn can be prevented from customers merely likely to churn; estimate incremental net benefit.','No randomized assignment, service/offer exposure, usual-care control, treatment timing, uptake or intervention cost fields exist. Churn outcomes alone cannot identify treatment effects. A prospective experiment is needed.']]))
    sections.append('''<p>These gaps are missing evidence, not inconclusive statistical tests. Repeated splitting, deduplication and better prediction cannot fill them. The experiment design below specifies how to obtain the causal evidence.</p>
<h2>A frozen holdout illustrates the scorecard and budget mechanics</h2>
<p>The following scorecard and budget tables retain one reproducible training/validation/test split. Use the 30-split comparisons above for stability and policy selection; this worked example explains the scorecard and contact-count arithmetic.</p>''')
    document=document.replace('<h2>A twelve-cell scorecard is useful for ranking</h2>','\n'.join(sections)+'<h3>The twelve-cell scorecard</h3>',1)
    document=re.sub(r'<section class="bottomline">.*?</section>',
        '<section class="bottomline"><b>Pilot service recovery for active complainants; use richer models to test broader outreach.</b> Across 30 grouped splits, expanded logistic detects 77.7% of all-account churn at a 20% contact cap, versus 70.3% for the scorecard, and the gain survives duplicate removal. Among active accounts, a simple complaints-then-low-usage rule improves coverage, but neither predictive accuracy nor the value index proves that an offer prevents churn or pays for itself.</section>',document,count=1,flags=re.S)
    document=document.replace('verify active eligibility and contact customers with complaints, ordered by score; use value to resolve equal-risk priorities if service capacity is scarce.','verify active eligibility and contact customers with complaints; use call usage and the tested model candidates to design prioritization if capacity is scarce.')
    document=document.replace('The held-out service cohort contains <b>22 active complainants</b>','In the single frozen holdout, the service cohort contains <b>22 active complainants</b>')
    document=document.replace('The candidate rule “active, no complaint, score ≥20%” identifies no offer segment because those scorecard cells never reach 20%. Do not relax the cutoff to fill capacity.','Broader low-usage outreach belongs in a measured pilot; do not fill spare capacity with unproven discounts.')
    document=document.replace('Age and value do not enter the fitted risk score.','Age and value do not enter any fitted risk model in this memo.')
    document=document.replace('No customer-level extract or contact list is produced.','For the requested continuous-feature model comparisons, authorized source records are processed transiently in local memory; no row-level file, prediction list or customer contact list is saved.')
    document=document.replace('Holdout metrics preserve row weights, while all record-level operations stay inside in-memory DuckDB.','Holdout metrics preserve row weights. The original scorecard and policy checks run inside in-memory DuckDB; the expanded model comparisons use transient local arrays and emit only aggregates.')
    document=document.replace('explain the evidence needed for incremental retention lift.</p>','explain the evidence needed for incremental retention lift. The follow-up additionally requests repeated grouped splits, regularized/tree comparisons, calibration and duplicate sensitivity, active-policy comparisons, and explicit reasons the three operational checks remain unavailable.</p>')
    document=document.replace('No calendar backtest possible.','No calendar backtest possible; 30 repeated grouped splits provide internal sensitivity only.')
    document=document.replace('Self-contained memo, reproducible aggregate scorecard and policy proposal; no notebook required.','Self-contained memo, reproducible scorecard and model/policy comparisons, with missing operational evidence explained; no notebook required.')
    return document
