"""MEGACOM 설정. DB 비밀번호는 환경변수로만 전달합니다."""
import os
from pathlib import Path
BASE = Path(__file__).resolve().parent
MODEL_DIR = BASE / 'models'
RESULT_DIR = BASE / 'results'
HORIZONS = (10, 30, 60, 120)
INPUT_MINUTES = 30
FEATURES = ('io003','temp_rise_5min','io028','io010','io044','io045','io046','io048','io007','io008','io009','io004','io005','current_avg','voltage_avg','current_unbalance')
RAW = ('io003','io028','io010','io044','io045','io046','io048','io007','io008','io009','io004','io005')
MODEL_VERSION = os.getenv('LSTM_MODEL_VERSION', 'megacom-v1')
# DB_CONFIG = dict(
#     host=os.getenv('DB_HOST','127.0.0.1'),
#     port=int(os.getenv('DB_PORT','3306')),
#     user=os.getenv('DB_USER','mega_admin'),
#     password=os.getenv('DB_PASSWORD','megaComp!#%'),
#     database=os.getenv('DB_NAME','airpredict'),
#     connection_timeout=10)


DB_CONFIG = dict(
    host=os.getenv("MYSQL_HOST", "121.181.35.7"),
    port=int(os.getenv("MYSQL_PORT", "3307")),
    user=os.getenv("MYSQL_USER", "mega_admin"),
    password=os.getenv("MYSQL_PASSWORD", "megaComp!#%"),
    database=os.getenv("MYSQL_DATABASE", "airpredict"),
    connection_timeout=10
)


COMCODE = os.getenv('MEGACOM_COMCODE','C00088')
DEVICE_ID = os.getenv('MEGACOM_DEVICE_ID','R00012')
