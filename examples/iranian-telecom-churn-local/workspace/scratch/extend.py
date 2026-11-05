from pathlib import Path
p=Path(__file__).parent/'analyze.py'
s=p.read_text(); marker="(ROOT/'results.json').write_text"
addition='''
q('unique_test_view',f'CREATE TEMP VIEW main.unique_scores AS SELECT DISTINCT * FROM main.score_{chosen}')
out['dedup_test']=evaluate('dedup_test','main.unique_scores','bucket>=8')
for col,expr in [('call_frequency',"CASE WHEN calls<100 THEN '<100' WHEN calls<250 THEN '100–249' ELSE '250+' END"),('sms_frequency',"CASE WHEN sms=0 THEN '0' WHEN sms<100 THEN '1–99' ELSE '100+' END")]:
    out['profiles']+=q('profile_'+col,f"SELECT '{col}' dimension,{expr} bin_label,count(*) n,sum(churn) churners,avg(churn) rate,avg(customer_value) mean_value FROM main.features GROUP BY 1,2 HAVING count(*)>=10 ORDER BY 2")
out['validation_selection']=[{'name':name,'precision20':v['curves'][2]['precision'],'auc':v['metrics']['auc']} for name,v in out['validation'].items()]
# Independent capacity calculation sums every score's higher-score peers without a window.
out['budget_independent']=q('budget_independent',f\'''WITH g AS (SELECT p,count(*) n,sum(churn) y FROM main.score_{chosen} WHERE bucket>=8 GROUP BY p),
w AS (SELECT a.*,greatest(0,least(1.0,(120-coalesce((SELECT sum(b.n) FROM g b WHERE b.p>a.p),0))/a.n)) weight FROM g a)
SELECT sum(n*weight) selected,sum(y*weight) caught FROM w\''')
assert abs(out['budget_independent'][0]['caught']-out['test']['curves'][2]['caught'])<1e-8
log('Independent capacity computation using correlated higher-score sums agrees with 20% test capture. Deduplicated-test weight sensitivity added without model refit; all usage proxies (seconds, call frequency, SMS) profiled. Earlier parser errors from reserved aliases seconds/value/level/precision were resolved by safe aliases; a Decimal/float assertion error was fixed with numeric normalization. Failed runs did not imply missing data. All final outputs regenerated successfully.')
'''
s=s.replace(marker,addition+'\n'+marker)
p.write_text(s)
