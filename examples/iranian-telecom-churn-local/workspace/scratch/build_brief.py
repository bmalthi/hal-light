"""Build the memo from saved aggregates and the required project HTML shell."""
import html
import json
import math
import re
import subprocess
from pathlib import Path
from scipy.stats import norm

root = Path(__file__).resolve().parents[1]
repo = root.parents[2]
scratch = root / 'scratch'
m = json.loads((scratch / 'model_results.json').read_text())
d = json.loads((root / 'analyse/diagnostics/scratch/aggregates.json').read_text())
pct = lambda x: f'{100*x:.1f}%'
num = lambda x: f'{x:,.0f}'
e = lambda x: html.escape(str(x))

def table(headers, rows):
    return '<table class="bridge"><thead><tr>' + ''.join(f'<th>{e(v)}</th>' for v in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{e(v)}</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table>'

spec = {'id':'policy_precision','form':'hbar','title':'Risk ranking finds more observed churners per contact',
        'subtitle':'653 held-out records • 130 contacts per policy • observed precision, not treatment lift',
        'width':700,'pad_l':165,'value_format':'{:.1%}','x_domain':[0,.8],
        'rows':[{'label':label,'value':m['policies'][key]['precision']} for key,label in [('risk','Risk score'),('complaint_first','Complaints first'),('risk_value','Risk × value'),('value_only','Value only')]]}
(scratch/'chart_specs.json').write_text(json.dumps(spec,indent=2))
subprocess.run(['uv','run','--no-sync',str(repo/'.claude/skills/dataviz/scripts/render.py'),str(scratch/'chart_specs.json'),'--out-dir',str(scratch/'charts'),'--single-mode','light'],check=True)
svg=(scratch/'charts/policy_precision.svg').read_text()
svg=re.sub(r'<\?xml[^>]*\?>','',svg)
# Nominal Wilson interval: illustrative sampling uncertainty, not duplicate-cluster-adjusted.
x,n=77,130
z=norm.ppf(.975)
center=(x/n+z*z/(2*n))/(1+z*z/n)
half=z*math.sqrt((x/n)*(1-x/n)/n+z*z/(4*n*n))/(1+z*z/n)
# Illustrative design only: two primary randomized comparisons, alpha=.025 each.
p0,p1=.6,.5
pbar=(p0+p1)/2
trial_n=math.ceil(((norm.ppf(1-.025/2)*math.sqrt(2*pbar*(1-pbar))+norm.ppf(.8)*math.sqrt(p0*(1-p0)+p1*(1-p1)))/(p0-p1))**2)
random_caught=130*104/653
random_value_share=130/653
training_prior=300/1888
baseline_brier=(104*(1-training_prior)**2+549*training_prior**2)/653
(scratch/'derived_metrics.json').write_text(json.dumps({'constant_training_prior_brier':baseline_brier,'precision_wilson95':[center-half,center+half],'random_caught':random_caught,'random_value_share':random_value_share,'trial_n_per_arm':trial_n,'trial_assumptions':{'p0':p0,'p1':p1,'alpha_per_comparison':.025,'power':.8}},indent=2))
parts=[]
parts.append('''<div class="kicker">Retention targeting · analytical memo</div>
<h1>Prioritize service recovery; test offers before scaling</h1>
<div class="byline">Iranian Telecom Churn · 3,150 records · prepared 4 November 2026 (Pacific)</div>
<section class="bottomline"><b>Start with a service-recovery pilot for active customers with complaints.</b> A simple scorecard detects 77 of 104 held-out churners within a 130-contact budget, but 116 targets are already non-active; this is not an automatic discount list. Use offers only in a randomized, value-screened pilot because this dataset cannot establish incremental retention or profit.</section>
<h2>Complaints identify risk even among active customers</h2>
<p>Overall churn is <b>495 / 3,150 (15.7%)</b>. Customers with complaints churn at <b>83.0%</b>, versus <b>10.1%</b> without. Among active customers alone, the comparison is <b>71.1% versus 2.9%</b>, so the complaint signal is not explained solely by account status.</p>''')
parts.append(table(['Status','Complaints','Customers','Churners','Churn rate'],[[{1:'Active',2:'Non-active'}[r['status']],{0:'No',1:'Yes'}[r['complaint']],num(r['n']),num(r['churns']),pct(r['churn_rate'])] for r in d['status_complaint']]))
parts.append('''<p>These are associations, not evidence that complaints cause churn or that resolving them prevents it. Activity changes the interpretation: the highest call-seconds quartile has <b>0 / 788</b> observed churners, including <b>0 / 22</b> customers with complaints. Zero observed events do not establish zero future risk.</p>
<h2>Lower engagement dominates the descriptive profile</h2>
<p>Each row below is a separate split of the full sample. Numeric bins use full-sample quartiles for description only; the scorecard uses a different, training-only threshold. Counts and percentages are unadjusted. Age values are five codes mapping one-to-one to age groups, not a continuous age distribution.</p>''')
cat_names={'complaint':('Complaints',{0:'No',1:'Yes'}),'status':('Status',{1:'Active',2:'Non-active'}),'tariff':('Tariff',{1:'Pay as you go',2:'Contractual'}),'age':('Age code',{15:'15 (group 1)',25:'25 (group 2)',30:'30 (group 3)',45:'45 (group 4)',55:'55 (group 5)'})}
rows=[]
for field,(label,mapping) in cat_names.items():
    for r in d['category_rates'][field]:
        rows.append([label,mapping[r[field]],num(r['n']),num(r['churns']),pct(r['churn_rate'])])
parts.append(table(['Profile','Segment','Customers','Churners','Rate'],rows))
for field,title in [('failure','Raw failure counts do not show a monotonic gradient'),('tenure','Tenure risk peaks in the 31–35 month band'),('seconds','Churn is concentrated at lower call duration'),('calls','Lower call frequency also marks risk'),('sms','High SMS use is associated with little observed churn'),('numbers','Calling fewer distinct numbers marks risk'),('value','The value index runs opposite to churn risk')]:
    parts.append(f'<h3>{title}</h3>')
    label={'failure':'Call failures','tenure':'Months subscribed','seconds':'Call seconds','calls':'Call count','sms':'SMS count','numbers':'Distinct numbers','value':'Value index'}[field]
    parts.append(table([label,'Customers','Churners','Rate'],[[r[field+'_bin'].split(': ',1)[1],num(r['n']),num(r['churns']),pct(r['churn_rate'])] for r in d['quantile_rates'][field]]))
parts.append('''<p>Call failures require an exposure denominator: among customers with calls, failure/call ratios above 15% have <b>270 / 1,037 (26.0%)</b> churn, compared with <b>6 / 345 (1.7%)</b> for positive ratios up to 5%. Even among active customers without complaints, the rates are <b>24 / 585 (4.1%)</b> versus <b>2 / 333 (0.6%)</b>. This is a diagnostic ratio, not a validated network failure probability: three records have more failures than calls.</p>
<p>Some apparent drivers change after stratification. Among active customers, tenure of at most 30 months has <b>71 / 716 (9.9%)</b> churn versus <b>8 / 535 (1.5%)</b> above 38 months. The age-45 code has 20.0% overall churn but only <b>5 / 252 (2.0%)</b> among active customers. Active contractual customers have <b>5 / 244 (2.0%)</b> churn versus <b>120 / 2,124 (5.6%)</b> for active pay-as-you-go customers; this does not establish that migrating tariff plans prevents churn.</p>
<p>Customer Value is an undocumented calculated index, not verified revenue or future margin. Churners average <b>124.8</b> index units versus <b>535.5</b> for non-churners. Use it as a provisional prioritization signal only; do not translate these units into a cash return.</p>
<h2>A twelve-cell scorecard is useful for ranking</h2>
<p>Split by identical predictor profiles: <b>1,888 training</b>, <b>609 validation</b>, and <b>653 test</b> records. No predictor profile crosses splits. All cutoffs and probabilities are learned from training; validation precision at 20% capacity selects among the three candidates below. The test set is then used for evaluation and explicitly labeled policy sensitivities, without retuning the scorecard.</p>''')
parts.append(table(['Candidate','Validation AUC','Precision at 20%','Detected / 91 churners'],[[{'complaint':'Complaints','complaint_usage':'Complaints + usage','complaint_usage_status':'Complaints + usage + status'}[k],f"{r['auc']:.3f}",pct(r['campaign20']['precision']),r['campaign20']['caught']] for k,r in m['validation'].items()]))
parts.append('''<p>For each complaint × status × usage cell, the score is <code>(training churners + 20 × 300/1888) / (training customers + 20)</code>. This fixed smoothing prevents zero/one probabilities in small cells. Call usage is <b>zero</b>, <b>1–3,100 seconds</b>, or <b>above 3,100 seconds</b>; 3,100 is the median positive training usage. A new combination falls back to the training prevalence, <b>15.9%</b>. Unexpected codes or missing inputs require review. Age and value do not enter the fitted risk score.</p>''')
parts.append(table(['Complaints','Status','Seconds','Training n','Score'],[['Yes' if r['complaint'] else 'No','Active' if r['status']==1 else 'Non-active',{0:'0',1:'1–3,100',2:'>3,100'}[r['usage']],r['n'],pct(r['risk'])] for r in m['scorecard']]))
parts.append(f'''<p>On test: <b>AUC {m['test']['auc']:.3f}</b>, <b>average precision {m['test']['average_precision']:.3f}</b> (prevalence {pct(m['test']['prevalence'])}), and <b>Brier score {m['test']['brier']:.3f}</b>. A constant training-prevalence prediction has Brier about 0.134 on this test. The status-free candidate still reaches <b>AUC 0.856</b> and detects <b>66 / 104</b> churners at 130 contacts.</p>
<p>Calibration is imperfect: the selected 130 average <b>45.7%</b> predicted risk but show <b>59.2%</b> observed churn. Sparse cells are strongly pulled toward the prior. Treat the score as a ranking aid; validate and recalibrate on a later cohort before using probabilities for pricing or expected returns.</p>''')
parts.append(table(['Score band','Test n','Mean prediction','Observed churn'],[[r['band'],r['n'],pct(r['predicted']),pct(r['observed'])] for r in m['calibration']]))
parts.append('''<h2>A contact cap exposes the cost of false positives</h2>
<p>Assume a <b>20% contact cap</b>, not a known currency budget. Take <code>floor(cap × eligible population)</code> contacts; the main retrospective comparison allows all 653 test records. Rank descending by score and use an outcome-blind tie-break (fixed seed 19). Each table reports observed labels, not prevented churn. “Non-churners” are prediction false positives; they are not proven wasted interventions.</p>''')
parts.append(table(['Cap','Contacts','Churners detected','Non-churners','Precision','Recall'],[[pct(r['budget']),r['contacts'],r['caught'],r['false_positives'],pct(r['precision']),pct(r['recall'])] for r in m['budgets']]))
parts.append(f'''<p>At 20%, the confusion counts are <b>77 detected, 53 false positives, 27 missed, and 496 true negatives</b>. The selection lift is <b>3.72×</b> relative to random selection, which would find <b>{random_caught:.1f}</b> churners on average. This is prediction lift, not retention lift.</p>
<p>Tied scores matter: 20 fixed tie seeds detect <b>70–77</b> churners ({pct(70/130)}–{pct(77/130)} precision). The exact expectation under uniform random tie-breaking is <b>{m['expected_ties']['expected_caught']:.1f}</b>. A nominal 95% Wilson interval for the fixed-seed precision is <b>{pct(center-half)}–{pct(center+half)}</b>; it assumes independent records and does not account for duplicate clusters, model selection or future distribution change.</p>
<figure class="fig">{svg}<figcaption>Same 130-contact capacity; every plotted value appears below.</figcaption></figure>''')
policy_labels={'risk':'Risk score','complaint_first':'Complaints first','risk_value':'Risk × value','value_only':'Value only'}
parts.append(table(['Policy','Detected','Non-churners','Precision','Churn-value captured'],[[label,m['policies'][k]['caught'],m['policies'][k]['false_positives'],pct(m['policies'][k]['precision']),pct(m['policies'][k]['value_recall'])] for k,label in policy_labels.items()]))
parts.append('''<p>“Churn-value captured” is the share of <code>sum(value × observed churn)</code> in selected records, not money saved. Risk × value finds fewer churners and does not improve that share here. Value-only targeting contacts 129 observed non-churners out of 130. Multiplying risk by value would also require comparable intervention effectiveness and costs to approximate an economic ranking; neither assumption is established.</p>
<p><b>Eligibility changes the decision.</b> Risk-only selects <b>116 non-active</b> and only <b>14 active</b> customers. Restricting to the <b>493 active</b> test records and contacting 20% gives <b>98 contacts, 21 detected churners, and 77 non-churners</b>: <b>21.4% precision</b>, <b>72.4% recall of 29 active churners</b>, and <b>3.64×</b> lift over the active baseline of 5.9%. Spending the full 130-contact capacity on active customers still detects only 21, adding 32 non-churners. Do not spend the cap merely because it is available.</p>
<section class="rec"><h2>Use separate service, offer and no-action routes</h2>
<p><b>Service intervention:</b> verify active eligibility and contact customers with complaints, ordered by score; use value to resolve equal-risk priorities if service capacity is scarce. Diagnose the complaint and call-failure history before proposing a remedy. The held-out service cohort contains <b>22 active complainants</b>, including <b>17 observed churners and 5 non-churners</b>, well below the 130-contact cap. This is a candidate pilot rule, not a proven effect.</p>
<p><b>Offer:</b> no automatic blanket discount. Test an offer added to service recovery among active complainants with value at least the training median, <b>222.815 index units</b>, after checking reachability and actual future contribution margin. There are only <b>7</b> such test records, insufficient for an effect estimate. Randomize eligible customers to service-only or service-plus-offer; a high historical risk score alone does not justify payment.</p>
<p><b>No proactive paid action:</b> active customers without complaints unless fresh operational evidence creates a service need; low-risk, high-value customers do not receive a discount solely for their value. The candidate rule “active, no complaint, score ≥20%” identifies no offer segment because those scorecard cells never reach 20%. Do not relax the cutoff to fill capacity. Non-active accounts need eligibility verification and a separately measured reactivation route before inclusion in retention.</p>
<p>For a cash budget, choose actions with positive <code>incremental retention probability × future contribution margin − contact/service cost − expected incentive cost</code>, subject to both the total spending limit and service capacity. Costs must include discounts to customers who would stay anyway. Risk × value is not a substitute for the incremental probability. The dataset supplies neither treatment effects, cash margin nor costs, so it cannot identify a profit-maximizing spend.</p></section>
<h2>Only a randomized comparison can establish incremental lift here</h2>
<p>Run two prespecified randomized comparisons: <b>enhanced service versus usual care</b> among verified active complainants, and <b>service plus offer versus the same service alone</b> among value-qualified active complainants. Define eligibility and scores before assignment; preserve ordinary support in all arms. Randomize at account level (or household level if spillovers occur), stratifying by risk, value and complaint type. Keep contact intensity comparable where practical and log assignment, delivery, uptake and costs.</p>
<p>The primary effect is <b>control churn rate minus treatment churn rate</b> over a fixed three-month window after assignment, analyzed by intention to treat. Report confidence intervals for retention lift and incremental contribution margin net of all costs; track complaints and adverse customer experience. Do not use redemption, treated-only retention or before/after comparisons as proof. Freeze the analysis, avoid repeated unplanned peeking, and reserve a later cohort to validate any learned treatment-effect targeting.</p>''')
parts.append(f'''<p>Size the trial from an operational baseline and the minimum economically useful effect. For illustration only, a reduction from <b>60% to 50%</b>, 80% power, and a two-sided <b>2.5%</b> significance level per comparison (two primary comparisons) requires approximately <b>{trial_n:,} customers per arm</b> under independent binomial sampling. Recalculate for the actual baseline, smaller effect, nonresponse and cluster design; the seven offer-eligible test records cannot answer this question.</p>
<h2>Watch items that could change the policy</h2>
<ul>
<li><b>Status timing and eligibility:</b> verify that the scoring snapshot predates the campaign and that non-active accounts can still be retained. If status is unavailable, use the tested status-free scorecard and revalidate on current accounts.</li>
<li><b>Repeated and conflicting records:</b> 300 excess exact duplicates; 14 identical predictor profiles have conflicting outcomes. Keeping profiles together avoids cross-split overlap, but customer IDs and timestamps are needed to distinguish duplicates from genuinely similar customers. Deduplicated descriptive churn is 446 / 2,850 (15.6%); the complaint association persists.</li>
<li><b>Out-of-time performance:</b> no dated snapshots are provided. A conventional row split gives AUC 0.884 and 48.0% precision at 20%, but shares 69 test profiles with training and uses a different test population. Neither split establishes prospective performance.</li>
<li><b>Value and quality:</b> obtain the value formula, currency margin, eligibility and intervention costs. There are no missing values, but charge code 10 occurs despite source documentation specifying 0–9; charge is excluded from the scorecard.</li>
<li><b>Selection and fairness:</b> age does not enter the scorecard, but investigate service access and errors by age and tariff in a larger prospective cohort. Small groups and zero-event segments are not safe grounds for denying ordinary support.</li>
</ul>
<h2>Methodology</h2>
<div class="method"><p>All empirical figures were computed from the supplied local <code>question/data.csv</code>, with no population filters. Source: <a href="https://archive.ics.uci.edu/dataset/563/iranian+churn+dataset">Iranian Churn, UCI Machine Learning Repository</a> (2020), DOI 10.24432/C5JW3Z, CC BY 4.0; metadata retrieved 5 November 2026 UTC. UCI describes first-nine-month attributes and month-12 churn labels; calendar dates and historical intervention assignments are absent. The local exercise’s author is unverified.</p>
<p>Descriptive tables use full-sample aggregates; predictive bins, prior and cell rates use training only. Three candidate feature sets and smoothing strength were fixed before validation. Profile splitting excludes the outcome from the grouping key. Holdout metrics preserve row weights, while all record-level operations stay inside in-memory DuckDB. No customer-level extract or contact list is produced. Saved scripts, SQL, aggregate outputs, checks and limitations are documented in <code>methodology.md</code> and <code>run_log.md</code>.</p></div>
<h2>Question &amp; Framing</h2>
<div class="method"><p><b>As asked:</b> Complete the Iranian Telecom Churn assignment: profile churn by complaints, call failures, subscription length, usage, tariff plan, status, age and customer value; build a model or scorecard and evaluate a budget-constrained campaign; recommend offer, service or no action; explain the evidence needed for incremental retention lift.</p>''')
parts.append(table(['Framing decision','Resolved as'],[['Period','Nine-month feature summary; month-12 churn, per source metadata. No calendar backtest possible.'],['Metrics','Churn rate, AUC, average precision, Brier score, contacts, precision, recall, observed false positives and value-weighted capture.'],['Budget','Assumed 20% contact capacity; sensitivity at 5%, 10%, 30%. Cash-budget optimization remains conditional on costs and effects.'],['Deliverable','Self-contained memo, reproducible aggregate scorecard and policy proposal; no notebook required.']]))
parts.append('</div><div class="foot">Prediction is not treatment response. Offer and service policies require a prospective experiment before scaling.</div>')
shell=(repo/'.claude/skills/analyse/assets/brief_template.html').read_text()
head=shell.split('<body>')[0]
head=re.sub(r'<!--.*?-->','',head,flags=re.S).replace('<title> - brief</title>','<title>Iranian Telecom Churn — retention memo</title>')
(root/'brief.html').write_text(head+'<body><main class="page">'+ '\n'.join(parts)+'</main></body></html>')
print(json.dumps({'brief_bytes':(root/'brief.html').stat().st_size,'trial_n_per_arm':trial_n,'wilson95':[center-half,center+half]},indent=2))

# Follow-up evidence is assembled into the same canonical answer.
if (scratch/'extended_results.json').exists():
    from extend_report import extend
    (root/'brief.html').write_text(extend((root/'brief.html').read_text(),root))
    print('Included repeated-split, model, calibration, deduplication and policy evidence.')
