
# test inputing data to db;


import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="megaComp!#%",
    database="ai-td6",
    charset="utf8mb4"
)

cursor = conn.cursor()

sql = """
INSERT INTO ai_analysis
(io045, io004, io007, io900)
VALUES (%s, %s, %s, %s)
"""

data = [
    (80.5, 220.1, 10.5, 380.1),
    (82.3, 221.2, 11.2, 381.2),
    (85.7, 219.5, 12.5, 379.5),
    (88.2, 222.1, 13.8, 382.1),
    (90.5, 220.8, 15.2, 380.8)
]

cursor.executemany(sql, data)

conn.commit()

print(f"{cursor.rowcount}개 데이터 저장 완료")




# append additional data;
#########################################

# 2. 데이터 입력
sql = """
INSERT INTO ai_analysis
(io045, io004, io007, io900)
VALUES (%s, %s, %s, %s)
"""

# 입력 데이터
data = (
    999.50,    # 유량계온도
    999.50,   # 전압평균
    999.30,    # 전류평균
    999.20    # 선간전압
)

# 3. SQL 실행
cursor.execute(sql, data)

# 4. 데이터 저장
conn.commit()

print("데이터 저장 완료!")









##########################################
# 5. 연결 종료
cursor.close()
conn.close()



