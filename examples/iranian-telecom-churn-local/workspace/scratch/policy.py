from pathlib import Path
import json
ROOT=Path(__file__).parent
# Reuse only this run's engine and saved instruments.
exec((ROOT/'analyze.py').read_text().split("print(json.dumps")[0])
q('policy',f'''CREATE TEMP VIEW main.policy AS SELECT *,
 CASE WHEN complaints=1 THEN 'Service investigation' WHEN p>=0.2 AND customer_value>=200 THEN 'Offer experiment' ELSE 'No paid action' END AS action,
 CASE WHEN complaints=1 THEN 1 WHEN p>=0.2 AND customer_value>=200 THEN 4 ELSE 0 END AS cost,
 CASE WHEN complaints=1 THEN 100000+p ELSE p*customer_value END AS priority
FROM main.score_{chosen} WHERE bucket>=8''')
out['policy_pool']=q('policy_pool','''SELECT action,count(*) n,sum(churn) churners,avg(churn) rate,avg(customer_value) mean_value,sum(cost) cost_units FROM main.policy GROUP BY 1 ORDER BY 1''')
out['policy_budgets']=[]
for budget in [30,60,120,240]:
    out['policy_budgets']+=q('policy_budget_'+str(budget),f'''WITH g AS (SELECT priority,action,cost,count(*) n,sum(churn) y,sum(churn*customer_value) yv FROM main.policy WHERE cost>0 GROUP BY 1,2,3),
 a AS(SELECT *,coalesce(sum(n*cost) OVER(ORDER BY priority DESC ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) prev_cost FROM g),
 w AS(SELECT *,greatest(0,least(1.0,({budget}-prev_cost)/(n*cost))) weight FROM a)
 SELECT {budget} budget_units,action,sum(n*weight) selected,sum(n*cost*weight) spend,
 sum(y*weight) caught,sum((n-y)*weight) false_positives,sum(yv*weight) churn_value
 FROM w GROUP BY 1,2 ORDER BY 2''')
log('Composite action policy evaluated on held-out rows entirely in SQL: complaints → service investigation; noncomplainants with score≥0.20 and customer-value proxy≥200 → randomized offer experiment candidates; remaining → no paid action/monitor. Illustrative costs service=1 unit, offer=4 units; budgets 30/60/120/240 units per 600 test customers. Policy intentionally differs from pure risk ranking; policy_pool.sql and policy_budget_*.sql supply exact totals. No claim these cost assumptions or value units are monetary.')
(ROOT/'results.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'policy_pool':out['policy_pool'],'policy_budgets':out['policy_budgets']},indent=2))
