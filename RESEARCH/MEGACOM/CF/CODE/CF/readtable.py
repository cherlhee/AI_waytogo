




import mysql.connector
import pandas as pd
from datetime import datetime
import os

conn = None
cursor = None

try:
    # 1. MySQL 연결

    # 1. MySQL 연결
    conn = mysql.connector.connect(
        host="121.181.35.7",
        port=3307,
        user="mega_admin",
        password="megaComp!#%",
        database="airpredict",
        connection_timeout=10
    )



    print("MySQL 접속 성공!")

    # 2. 가장 최근에 저장된 2000개 데이터 조회
    sql = """
        SELECT *
        FROM ai_oiltemp
        WHERE device_id = 'R00012'
          AND prediction_model = 'CF'
        ORDER BY id DESC
        LIMIT 2000
    """

    cursor = conn.cursor()
    cursor.execute(sql)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # 3. DataFrame 생성
    df = pd.DataFrame(rows, columns=columns)

    print(f"조회된 데이터: {len(df)}개")

    # 4. CSV 저장 시 시간순으로 정렬
    if not df.empty:
        df = df.sort_values(
            by=["input_time", "prediction_horizon_min"],
            ascending=[False, True]
        )

    print(df)

    # 5. CSV 저장 폴더 생성
    save_dir = "./CSV_results"
    os.makedirs(save_dir, exist_ok=True)

    # 6. 파일명 생성
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ai_oiltemp_recent2000_{now}.csv"

    filepath = os.path.join(save_dir, filename)

    # 7. CSV 저장
    df.to_csv(
        filepath,
        index=False,
        encoding="utf-8-sig"
    )

    print("\nCSV 저장 완료!")
    print("저장 위치:", os.path.abspath(filepath))

except mysql.connector.Error as err:
    print("MySQL 오류:", err)

finally:
    if cursor is not None:
        cursor.close()

    if conn is not None and conn.is_connected():
        conn.close()