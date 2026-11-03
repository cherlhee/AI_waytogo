


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

        # 버퍼링 커서 사용
        cursor = conn.cursor(buffered=True)

        # 1. 테이블 목록 조회
        cursor.execute("SHOW TABLES")

        print("\n테이블 목록:")
        for table in cursor.fetchall():
            print(table[0])

        # 2. ai_data 테이블 조회
        cursor.execute("SELECT * FROM ai_data LIMIT 100")

        # 컬럼명 가져오기
        columns = [desc[0] for desc in cursor.description]

        print("\n컬럼명:")
        print(columns)

        # 3. 데이터 가져오기
        rows = cursor.fetchall()

        print("\nai_data 테이블 내용:")

        for row in rows:
            print(row)

        print(f"\n조회된 데이터 개수: {len(rows)}")

except mysql.connector.Error as err:
    print("MySQL 오류:", err)

finally:
    if cursor is not None:
        cursor.close()

    if conn is not None and conn.is_connected():
        conn.close()
        print("\nMySQL 연결 종료")