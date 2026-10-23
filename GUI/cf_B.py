"""B: reaches target at least once within the next N minutes."""
import pandas as pd
from cf_core import run

def calculate_cf(df, predict_min=10):
    return run(df, mode='B', horizons=[predict_min])

def calculate_all(df):
    return run(df, mode='B')

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise SystemExit('사용법: python cf_B.py 원본데이터.csv')
    df = pd.read_csv(sys.argv[1], encoding='cp949', low_memory=False)
    print(calculate_all(df).to_string(index=False))
