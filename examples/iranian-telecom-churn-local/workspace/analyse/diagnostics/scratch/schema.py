import json
from pathlib import Path
import duckdb

path = str(Path(__file__).resolve().parents[4] / 'question/data.csv')
con = duckdb.connect()
print(json.dumps(con.execute('DESCRIBE SELECT * FROM read_csv_auto(?)', [path]).fetchall()))
