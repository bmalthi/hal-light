"""Aggregate-only descriptive diagnostics; never materializes row-level extracts."""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SOURCE = str(ROOT.parents[2] / 'question/data.csv')
con = duckdb.connect()
con.execute('''CREATE TEMP VIEW data AS SELECT
 "Call  Failure" AS failure, "Complains" AS complaint,
 "Subscription  Length" AS tenure, "Charge  Amount" AS charge,
 "Seconds of Use" AS seconds, "Frequency of use" AS calls,
 "Frequency of SMS" AS sms, "Distinct Called Numbers" AS numbers,
 "Age Group" AS age_group, "Tariff Plan" AS tariff, "Status" AS status,
 "Age" AS age, "Customer Value" AS value, "Churn" AS churn
 FROM read_csv_auto(''' + repr(SOURCE) + ''')''')

def query(sql):
    result = con.execute(sql)
    columns = [column[0] for column in result.description]
    return [dict(zip(columns, row)) for row in result.fetchall()]

def rates(group, source='data', where='TRUE'):
    # Small joint cells are described by size only, never outcome-specific values.
    return query(f'''SELECT {group}, count(*) AS n,
      CASE WHEN count(*) >= 10 THEN sum(churn) END AS churns,
      CASE WHEN count(*) >= 10 THEN avg(churn) END AS churn_rate
      FROM {source} WHERE {where} GROUP BY {group} ORDER BY {group}''')

fields = ['failure', 'complaint', 'tenure', 'charge', 'seconds', 'calls', 'sms',
          'numbers', 'age_group', 'tariff', 'status', 'age', 'value', 'churn']
continuous = ['failure', 'tenure', 'charge', 'seconds', 'calls', 'sms', 'numbers', 'age', 'value']
profile = []
for field in fields:
    row = query(f'''SELECT count(*) AS n, count(*) - count({field}) AS missing,
      count(DISTINCT {field}) AS distinct_values, min({field}) AS minimum,
      quantile_cont({field}, .25) AS q25, quantile_cont({field}, .5) AS median,
      quantile_cont({field}, .75) AS q75, max({field}) AS maximum,
      avg({field}) AS mean, stddev_samp({field}) AS standard_deviation FROM data''')[0]
    profile.append({'field': field, **row})

feature_list = ', '.join(fields[:-1])
full_list = ', '.join(fields)
quality = {
    'total': query('SELECT count(*) AS n, sum(churn) AS churns, avg(churn) AS churn_rate FROM data')[0],
    'exact_duplicates': query(f'''SELECT count(*) AS distinct_full_rows,
      sum(n - 1) AS duplicate_excess_rows, count(*) FILTER (WHERE n > 1) AS repeated_groups,
      sum(n) FILTER (WHERE n > 1) AS rows_in_repeated_groups, max(n) AS largest_group
      FROM (SELECT {full_list}, count(*) AS n FROM data GROUP BY {full_list})''')[0],
    'feature_duplicates': query(f'''SELECT count(*) AS distinct_feature_rows,
      sum(n - 1) AS duplicate_excess_rows, count(*) FILTER (WHERE labels > 1) AS conflicting_label_groups,
      sum(n) FILTER (WHERE labels > 1) AS rows_in_conflicting_label_groups
      FROM (SELECT {feature_list}, count(*) AS n, count(DISTINCT churn) AS labels
      FROM data GROUP BY {feature_list})''')[0],
    'deduplicated_total': query('SELECT count(*) AS n, sum(churn) AS churns, avg(churn) AS churn_rate FROM (SELECT DISTINCT * FROM data)')[0],
    'consistency': query('''SELECT count(*) FILTER (WHERE calls = 0) AS zero_calls,
      count(*) FILTER (WHERE seconds = 0) AS zero_seconds,
      count(*) FILTER (WHERE calls = 0 AND seconds > 0) AS zero_calls_positive_seconds,
      count(*) FILTER (WHERE calls > 0 AND seconds = 0) AS positive_calls_zero_seconds,
      count(*) FILTER (WHERE calls = 0 AND failure > 0) AS zero_calls_positive_failure,
      count(*) FILTER (WHERE failure > calls) AS failures_exceed_calls,
      count(*) FILTER (WHERE charge NOT BETWEEN 0 AND 9) AS charge_outside_documented_0_to_9,
      count(*) FILTER (WHERE complaint NOT IN (0,1) OR churn NOT IN (0,1)
        OR tariff NOT IN (1,2) OR status NOT IN (1,2)) AS invalid_binary_codes FROM data''')[0],
}

bin_expressions = {}
for field in continuous:
    thresholds = next(row for row in profile if row['field'] == field)
    cuts = list(dict.fromkeys(thresholds[key] for key in ['q25', 'median', 'q75']))
    clauses = []
    for index, cut in enumerate(cuts):
        previous = cuts[index - 1] if index else None
        label = f'<= {cut:g}' if previous is None else f'> {previous:g} to <= {cut:g}'
        clauses.append(f"WHEN {field} <= {cut} THEN '{index + 1}: {label}'")
    bin_expressions[f'{field}_bin'] = 'CASE ' + ' '.join(clauses) + f" ELSE '{len(cuts) + 1}: > {cuts[-1]:g}' END"
bin_expressions['failure_relative_bin'] = '''CASE
 WHEN calls = 0 THEN '0: no calls'
 WHEN failure = 0 THEN '1: no failures'
 WHEN failure::DOUBLE / calls <= .05 THEN '2: >0 to 5%'
 WHEN failure::DOUBLE / calls <= .15 THEN '3: >5 to 15%'
 ELSE '4: >15%' END'''
bin_expressions['zero_usage'] = "CASE WHEN seconds = 0 AND calls = 0 THEN 'No calls/seconds' ELSE 'Some calls/seconds' END"
con.execute('CREATE TEMP VIEW binned AS SELECT *, ' + ', '.join(f'{value} AS {key}' for key, value in bin_expressions.items()) + ' FROM data')

summary = {
    'source': SOURCE,
    'note': 'All outputs are aggregates. Joint strata with n < 10 suppress churn counts/rates. Percentiles define bins on the full sample. Descriptive associations only.',
    'quality': quality,
    'profile': profile,
    'category_rates': {field: rates(field) for field in ['complaint', 'status', 'tariff', 'age_group', 'charge', 'age']},
    'quantile_rates': {field: rates(f'{field}_bin', 'binned') for field in continuous},
    'status_complaint': rates('status, complaint'),
    'status_stratified': {field: rates(f'status, {field}_bin', 'binned') for field in continuous},
    'complaint_status_stratified': {field: rates(f'status, complaint, {field}_bin', 'binned') for field in ['failure', 'seconds', 'calls', 'sms', 'value']},
    'relative_failure': rates('failure_relative_bin', 'binned'),
    'relative_failure_status_complaint': rates('status, complaint, failure_relative_bin', 'binned'),
    'zero_usage': rates('status, zero_usage', 'binned'),
    'status_tariff': rates('status, tariff'),
    'status_age_group': rates('status, age_group'),
    'churn_group_means': query('SELECT churn, count(*) AS n, ' + ', '.join(f'avg({f}) AS mean_{f}' for f in continuous) + ' FROM data GROUP BY churn ORDER BY churn'),
    'age_group_mapping': query('SELECT age_group, count(*) AS n, min(age) AS minimum_age, max(age) AS maximum_age, count(DISTINCT age) AS distinct_ages FROM data GROUP BY age_group ORDER BY age_group'),
    'value_correlations': query('SELECT ' + ', '.join(f'corr(value, {f}) AS value_{f}' for f in ['seconds', 'calls', 'sms', 'numbers', 'age', 'charge']) + ' FROM data')[0],
    'independent_total_check': rates('status'),
    'complaint_deduplicated': rates('complaint', '(SELECT DISTINCT * FROM data)'),
    'status_complaint_deduplicated': rates('status, complaint', '(SELECT DISTINCT * FROM data)'),
}
total = quality['total']
assert sum(row['n'] for row in summary['independent_total_check']) == total['n']
assert sum(row['churns'] for row in summary['independent_total_check']) == total['churns']
for table in summary['quantile_rates'].values():
    assert sum(row['n'] for row in table) == total['n']
    assert sum(row['churns'] for row in table) == total['churns']
assert sum(row['n'] for row in summary['status_complaint']) == total['n']
assert sum(row['churns'] for row in summary['status_complaint']) == total['churns']
summary['validation'] = {'status_total_reconciles': True, 'quantile_tables_reconcile': True, 'status_complaint_reconciles': True}
(ROOT / 'scratch/aggregates.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'quality': quality, 'value_correlations': summary['value_correlations'], 'profile': profile, 'validation': summary['validation']}, indent=2))
