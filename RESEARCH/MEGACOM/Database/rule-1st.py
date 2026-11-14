


import os
import mysql.connector
from datetime import datetime

# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------
nameTable = "ai_analysis"
DEVICE_ID = "R00012"
COM_CODE = "C00088"


# --------------------------------------------------
# 2. 센서 항목
# --------------------------------------------------
SENSOR_COLUMNS = {
    "유량계온도": ["io045"],
    "전압평균": ["io004", "io005"],
    "전류평균": ["io007", "io008", "io009"],
    "토출압력": ["io001"],
    "오일온도": ["io003"]
}


# --------------------------------------------------
# 3. 기준값 (임시값)
# 실제 운영에서는 기준 테이블에서 조회
# --------------------------------------------------
STANDARDS = {
    "유량계온도": 30,
    "전압평균": 380,
    "전류평균": 15,
    "토출압력": 3,
    "오일온도": 80
}


# --------------------------------------------------
# 4. 항목별 점수 계산
# --------------------------------------------------

# 유량계 온도
def score_temperature(value, standard):

    if value < 30:
        return 0
    if value < 35:
        return 40
    if value < 40:
        return 50
    if value < 45:
        return 60

    return 70


# 전압 평균
def score_voltage(value, standard):

    if standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0
    if diff < 7:
        return 40

    return 70


# 전류 평균
def score_current(value, standard):

    if standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0
    if diff < 10:
        return 40
    if diff < 15:
        return 60

    return 70


# 토출압력
def score_pressure(value, previous):

    if previous is None:
        return None

    diff = abs(value - previous)

    if diff >= 3:
        return 70

    return 0


# 오일온도
def score_oil(value, standard):

    if standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0
    if diff < 10:
        return 40

    return 70


# --------------------------------------------------
# 5. 항목별 판정 함수 연결
# --------------------------------------------------
SCORE_FUNCTIONS = {
    "유량계온도": score_temperature,
    "전압평균": score_voltage,
    "전류평균": score_current,
    "토출압력": score_pressure,
    "오일온도": score_oil
}


# --------------------------------------------------
# 6. 알람단계 설정
# --------------------------------------------------
def set_alarm(score):

    if score is None:
        return "미판정"

    if score == 0:
        return 0 #"정상"

    if score < 70:
        return 1 #"주의"

    return 2 #"경고"


# --------------------------------------------------
# 7. INSERT SQL
# --------------------------------------------------
INSERT_SQL = f"""
    INSERT INTO `{nameTable}`
    (
        comcode, deviceId, input_time,

        io045, grade_045, alarm_045,
        io004, grade_004, alarm_004,
        io007, grade_007, alarm_007,
        io001, grade_001, alarm_001,
        io003, grade_003, alarm_003
    )
    VALUES (
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s
    )
"""


# --------------------------------------------------
# 8. 데이터 조회, 점수 계산 및 저장
# --------------------------------------------------
def run(cursor, conn):

    print("hello, run")

    # 조회 컬럼 자동 생성
    columns = list(dict.fromkeys(
        col
        for cols in SENSOR_COLUMNS.values()
        for col in cols
    ))

    # 최근 2개 데이터 조회
    sql = f"""
        SELECT input_time, {', '.join(columns)}
        FROM ai_data
        WHERE comcode = %s
          AND deviceId = %s
        ORDER BY input_time DESC
        LIMIT 2
    """

    cursor.execute(sql, (COM_CODE, DEVICE_ID))

    rows = cursor.fetchall()

    if not rows:
        print("데이터 없음")
        return

    # 현재 데이터
    data = dict(zip(["input_time"] + columns, rows[0]))

    # 이전 데이터
    previous = (
        dict(zip(["input_time"] + columns, rows[1]))
        if len(rows) > 1 else None
    )

    input_time = str(data["input_time"])[:19]

    # --------------------------------------------------
    # 센서값 계산
    # --------------------------------------------------
    results = {}

    for name, cols in SENSOR_COLUMNS.items():

        try:
            values = [float(data[col]) for col in cols]

            if name == "전류평균" and any(v <= 0 for v in values):
                raise ValueError("전류값 오류")

            value = sum(values) / len(values)

            standard = STANDARDS[name]

            # 토출압력은 이전 측정값과 비교
            if name == "토출압력":

                previous_value = None

                if previous:
                    previous_value = previous.get("io001")

                    if previous_value is not None:
                        previous_value = float(previous_value)

                score = SCORE_FUNCTIONS[name](
                    value, previous_value
                )

            else:
                score = SCORE_FUNCTIONS[name](
                    value, standard
                )

            alarm = set_alarm(score)

        except (ValueError, TypeError, KeyError):
            value = None
            score = None
            alarm = "미판정"

        results[name] = {
            "value": value,
            "score": score,
            "alarm": alarm
        }

    # --------------------------------------------------
    # 결과 출력
    # --------------------------------------------------
    print("\n측정시각:", input_time)

    for name, result in results.items():

        print(
            f"{name}: "
            f"현재값={result['value']}, "
            f"점수={result['score']}, "
            f"알람={result['alarm']}"
        )

    # --------------------------------------------------
    # ai_analysis INSERT
    # --------------------------------------------------
    params = (
        COM_CODE,
        DEVICE_ID,
        input_time,

        results["유량계온도"]["value"],
        results["유량계온도"]["score"],
        results["유량계온도"]["alarm"],

        results["전압평균"]["value"],
        results["전압평균"]["score"],
        results["전압평균"]["alarm"],

        results["전류평균"]["value"],
        results["전류평균"]["score"],
        results["전류평균"]["alarm"],

        results["토출압력"]["value"],
        results["토출압력"]["score"],
        results["토출압력"]["alarm"],

        results["오일온도"]["value"],
        results["오일온도"]["score"],
        results["오일온도"]["alarm"]
    )

    cursor.execute(INSERT_SQL, params)
    conn.commit()

    print("\nINSERT 완료")


# --------------------------------------------------
# 9. 메인 함수
# --------------------------------------------------
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
        run(cursor, conn)

    except mysql.connector.Error as err:
        conn.rollback()
        print("MySQL Error:", err)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()