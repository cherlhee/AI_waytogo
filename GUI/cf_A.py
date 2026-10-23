"""A: exactly N minutes later >= target temperature."""
import pandas as pd
from cf_core import run

def calculate_cf(df, predict_min=10):
    return run(df, mode='A', horizons=[predict_min])

def calculate_all(df):
    return run(df, mode='A')

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        raise SystemExit('사용법: python cf_A.py 원본데이터.csv')
    df = pd.read_csv(sys.argv[1], encoding='cp949', low_memory=False)
    print(calculate_all(df).to_string(index=False))
