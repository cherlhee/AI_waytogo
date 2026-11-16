




import mysql.connector
import pandas as pd
from datetime import datetime
import os



name_table = "ai_data"
name_table = "ai_current_std"
name_table = "ai_oiltemp"



try:
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


    # 2. 최근 20개 데이터 조회
    sql = f"""
        SELECT *
        FROM {name_table}        
    """

    # 3. 데이터 읽기
    cursor = conn.cursor()
    cursor.execute(sql)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # 4. DataFrame 생성
    df = pd.DataFrame(rows, columns=columns)

    print(f"조회된 데이터: {len(df)}개")
    print(df)

    # 5. CSV 저장 폴더 생성
    save_dir = "./CSV_results"
    os.makedirs(save_dir, exist_ok=True)

    # 6. 파일명 생성
    # 6. 파일명 생성
    now = datetime.now().strftime("%Y%m%d")
    filename = f"{name_table}-{now}.csv"

    filepath = os.path.join(save_dir, filename)



    # 7. CSV 파일 저장
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
    if "cursor" in locals():
        cursor.close()

    if "conn" in locals() and conn.is_connected():
        conn.close()