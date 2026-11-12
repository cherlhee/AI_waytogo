



import mysql.connector

conn = None
cursor = None

try:
    conn = mysql.connector.connect(
        host="121.181.35.7",
        port=3307,
        user="mega_admin",
        password="megaComp!#%",
        database="airpredict",
        connection_timeout=10
    )

    if conn.is_connected():
        print("MySQL 접속 성공!")

        cursor = conn.cursor(buffered=True)

        # 조회할 테이블 목록
        tables = ["ai_data", "ai_alarm", "ai_analysis", "ai_oiltemp", "ai_lstm_r"]

        for table in tables:

            print(f"\n========== {table} ==========")

            # 테이블 컬럼 구조 조회
            cursor.execute(f"DESCRIBE `{table}`")

            columns = cursor.fetchall()

            print("\n컬럼 구조:")
            print("컬럼명 | 데이터타입 | NULL | KEY | DEFAULT | EXTRA")
            print("-" * 90)

            for col in columns:
                print(
                    f"{col[0]} | {col[1]} | {col[2]} | "
                    f"{col[3]} | {col[4]} | {col[5]}"
                )

            print(f"\n총 컬럼 수: {len(columns)}")

except mysql.connector.Error as err:
    print("MySQL 오류:", err)

finally:
    if cursor is not None:
        cursor.close()

    if conn is not None and conn.is_connected():
        conn.close()
        print("\nMySQL 연결 종료")