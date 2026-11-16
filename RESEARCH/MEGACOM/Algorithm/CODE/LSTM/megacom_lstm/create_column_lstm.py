

import mysql.connector
import pandas as pd
from datetime import datetime
import os



tableName = 'ai_lstm_r'

new_column = 'rmse'
after_column = 'mae'




try:

    # ==========================================================
    # MySQL 연결
    # ==========================================================

    conn = mysql.connector.connect(
        host="121.181.35.7",
        port=3307,
        user="mega_admin",
        password="megaComp!#%",
        database="airpredict",
        connection_timeout=10
    )

    print("MySQL 접속 성공!")

    cursor = conn.cursor()



    # ==========================================================
    # to delete a column;
    # ==========================================================

    # sql = f"""
    #     ALTER TABLE {tableName}
    #     DROP COLUMN prediction_abs_error
    # """
    # 
    # cursor.execute(sql)

    # ==========================================================
    # to check whether a new column exists;
    # ==========================================================

    cursor.execute(f"SHOW COLUMNS FROM {tableName}")

    existing_columns = [
        row[0] for row in cursor.fetchall()
    ]



    # ==========================================================
    # to insert a new column;
    # ==========================================================

    if new_column not in existing_columns:

        sql = f"""
            ALTER TABLE {tableName}
            ADD COLUMN {new_column} DECIMAL(10,2) NULL
            AFTER {after_column}
        """
        
        cursor.execute(sql)

        print(f"Finished inserting column: {new_column}")

    else:
        print(f"Already exists; {new_column}")




    # ==========================================================
    # 최근 20개 데이터 조회
    # ==========================================================

    sql = f"""
        SELECT *
        FROM {tableName}
        ORDER BY input_time DESC
        LIMIT 200
    """

    cursor.execute(sql)

    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    # 4. DataFrame 생성
    df = pd.DataFrame(rows, columns=columns)

    print(f"조회된 데이터: {len(df)}개")
    print(df)


    # ==========================================================
    # CSV 저장 
    # ==========================================================

    save_dir = "./CSV_results"
    os.makedirs(save_dir, exist_ok=True)

    # 6. 파일명 생성
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{tableName}_recent200_{now}.csv"

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