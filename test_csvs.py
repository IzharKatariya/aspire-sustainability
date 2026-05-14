import pandas as pd
from pathlib import Path

files = ['company_a.csv', 'company_b.csv', 'company_c.csv']
for f in files:
    df = pd.read_csv(Path('data/sample_csvs') / f)
    company = df.iloc[0]['company_name']
    year = df.iloc[0]['reporting_year']
    cols = df.shape[1]
    print(f'{f}: {cols} columns | company={company} | year={year}')