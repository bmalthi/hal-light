from pathlib import Path
import csv
import json

source = Path('/hal-light/examples/seoul-bike-sharing-demand/question/data.csv')
raw = source.read_bytes()
for enc in ['utf-8-sig', 'cp1252']:
    try:
        text = raw.decode(enc)
        break
    except UnicodeDecodeError:
        continue
header = next(csv.reader(text.splitlines()))
print(json.dumps({'encoding': enc, 'columns': header}))
