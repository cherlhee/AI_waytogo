"""ai_data -> ai_analysis 룰베이스 판정. 실행 전 DB 환경변수 설정 필요."""
import argparse
import logging
import os
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd
import mysql.connector



nameTable = 'ai_analysis'
DEVICE_ID = 'R00012'
COM_CODE = 'C00088'


INSERT_SQL = f'''
INSERT INTO {nameTable}
(comcode, deviceId, input_time)
VALUES (%s, %s, %s)
'''



def run(cursor, conn):
    print('hello, run')

    input_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    params = (COM_CODE, DEVICE_ID, input_time)
    cursor.execute(INSERT_SQL, params)

    conn.commit()

    print("INSERT 완료")
    print("COM_CODE:", COM_CODE)
    print("DEVICE_ID:", DEVICE_ID)
    print("input_time:", input_time)


def main():

    conn = mysql.connector.connect(
        host="121.181.35.7",
        port=3307,
        user="mega_admin",
        password="megaComp!#%",
        database="airpredict",
        connection_timeout=10
    )
    cursor = conn.cursor()

    try:


        # 최근 데이터 조회
        sql = f"""
            SELECT *
            FROM {nameTable}
            ORDER BY input_time DESC
            LIMIT 20
        """
        cursor.execute(sql)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # DataFrame 생성
        df = pd.DataFrame(rows, columns=columns)

        print(f"조회된 데이터: {len(df)}개")
        print(df.tail())

        # to insert;
        run(cursor, conn)


    except mysql.connector.Error as err:
        conn.rollback()
        print("Mysql Error: ", err)

    finally:
        cursor.close()
        conn.close()






if __name__=='__main__': 
    main()
