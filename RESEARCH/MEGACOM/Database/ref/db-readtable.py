



import mysql.connector

conn = mysql.connector.connect(
    host="121.181.35.7",
    port=3307,
    user="mega_admin",
    password="megaComp!#%",
    database="airpredict",
    connection_timeout=10
)
cursor = conn.cursor()

cursor.execute("SHOW TABLES")

print("테이블 목록:")
for table in cursor.fetchall():
    print(table[0])

cursor.close()
conn.close()