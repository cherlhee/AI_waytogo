


import os
from datetime import datetime

import mysql.connector


# ==================================================
# 1. 기본 설정
# ==================================================
COM_CODE = "C00088"
DEVICE_ID = "R00012"

SOURCE_TABLE = "ai_data"
TARGET_TABLE = "ai_analysis"


# ==================================================
# 2. 센서 항목 및 저장 컬럼 설정
# ==================================================
SENSORS = {
    "유량계온도": {
        "columns": ["io045"],
        "code": "045",
        "standard": 30
    },
    "전압평균": {
        "columns": ["io004", "io005"],
        "code": "004",
        "standard": 380
    },
    "전류평균": {
        "columns": ["io007", "io008", "io009"],
        "code": "007",
        "standard": 15
    },
    "토출압력": {
        "columns": ["io001"],
        "code": "001",
        "standard": 3
    },
    "오일온도": {
        "columns": ["io003"],
        "code": "003",
        "standard": 80
    },
    "소모품교체주기": {
        "columns": ["io030"],
        "code": "030",
        "standard": 2000
    },
    "선간전압불균형": {
        "columns": ["io004", "io005"],
        "code": "900",
        "standard": 10
    },
    "전류불균형": {
        "columns": ["io007", "io008", "io009"],
        "code": "901",
        "standard": 10
    }
}


# ==================================================
# 3. 숫자 변환
# ==================================================
def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ==================================================
# 4. 항목별 점수 계산
# ==================================================

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


def score_voltage(value, standard):
    if standard is None or standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0
    if diff < 7:
        return 40
    return 70


def score_current(value, standard):
    if standard is None or standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0
    if diff < 10:
        return 40
    if diff < 15:
        return 60
    return 70


def score_pressure(value, previous):
    if previous is None:
        return None

    return 70 if abs(value - previous) >= 3 else 0


def score_oil(value, standard):
    if standard is None or standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0
    if diff < 10:
        return 40
    return 70


def score_consumable(value, standard):
    if standard is None or standard <= 0:
        return None

    ratio = value / standard * 100

    if ratio < 90:
        return 0
    if ratio < 100:
        return 40
    return 70


def score_voltage_unbalance(value, standard):
    if value < 7:
        return 0
    if value <= 10:
        return 40
    return 70


def score_current_unbalance(value, standard):
    if value < 10:
        return 0
    if value <= 15:
        return 40
    return 70


# ==================================================
# 5. 판정 함수 연결
# ==================================================
SCORE_FUNCTIONS = {
    "유량계온도": score_temperature,
    "전압평균": score_voltage,
    "전류평균": score_current,
    "토출압력": score_pressure,
    "오일온도": score_oil,
    "소모품교체주기": score_consumable,
    "선간전압불균형": score_voltage_unbalance,
    "전류불균형": score_current_unbalance
}


# ==================================================
# 6. 알람단계 설정
# ==================================================
def set_alarm(score):
    if score is None:
        return None
    if score == 0:
        return 0       # 정상
    if score < 70:
        return 5       # 주의
    return 9           # 경고


# ==================================================
# 7. 센서값 계산
# ==================================================
def calculate_value(name, values):

    if any(v is None for v in values):
        return None

    if name in ("전류평균", "전류불균형"):
        if any(v <= 0 for v in values):
            return None

    if name in ("선간전압불균형", "전류불균형"):
        maximum = max(values)

        if maximum <= 0:
            return None

        return (
            (maximum - min(values))
            / maximum * 100
        )

    return sum(values) / len(values)


# ==================================================
# 8. 데이터 조회
# ==================================================
def get_sensor_data(cursor):

    columns = list(dict.fromkeys(
        col
        for sensor in SENSORS.values()
        for col in sensor["columns"]
    ))

    sql = f"""
        SELECT input_time, {', '.join(columns)}
        FROM `{SOURCE_TABLE}`
        WHERE comcode = %s
          AND deviceId = %s
        ORDER BY input_time DESC
        LIMIT 2
    """

    cursor.execute(sql, (COM_CODE, DEVICE_ID))
    rows = cursor.fetchall()

    if not rows:
        return None, None

    keys = ["input_time"] + columns

    current = dict(zip(keys, rows[0]))

    previous = (
        dict(zip(keys, rows[1]))
        if len(rows) > 1
        else None
    )

    return current, previous


# ==================================================
# 9. 룰베이스 판정
# ==================================================
def analyze(current, previous):

    results = {}

    for name, sensor in SENSORS.items():

        values = [
            to_float(current.get(col))
            for col in sensor["columns"]
        ]

        value = calculate_value(name, values)
        standard = sensor["standard"]
        score = None

        if value is not None:

            if name == "토출압력":

                old = None

                if previous:
                    try:
                        t1 = datetime.strptime(
                            str(current["input_time"])[:19],
                            "%Y-%m-%d %H:%M:%S"
                        )
                        t0 = datetime.strptime(
                            str(previous["input_time"])[:19],
                            "%Y-%m-%d %H:%M:%S"
                        )

                        if (t1 - t0).total_seconds() == 5:
                            old = to_float(previous.get("io001"))

                    except ValueError:
                        pass

                score = score_pressure(value, old)

            else:
                score = SCORE_FUNCTIONS[name](value, standard)

        results[name] = {
            "value": value,
            "standard": standard,
            "score": score,
            "alarm": set_alarm(score)
        }

    return results


# ==================================================
# 10. ai_analysis INSERT
# ==================================================
def save_analysis(cursor, conn, current, results):

    columns = ["comcode", "deviceId", "input_time"]

    values = [
        COM_CODE,
        DEVICE_ID,
        str(current["input_time"])[:19]
    ]

    for name, sensor in SENSORS.items():

        code = sensor["code"]
        result = results[name]

        columns.extend([
            f"io{code}",
            f"grade_{code}",
            f"alarm_{code}"
        ])

        values.extend([
            result["value"],
            result["score"],
            result["alarm"]
        ])

    column_sql = ", ".join(f"`{col}`" for col in columns)
    placeholders = ", ".join(["%s"] * len(values))

    sql = f"""
        INSERT INTO `{TARGET_TABLE}`
        ({column_sql})
        VALUES ({placeholders})
    """

    cursor.execute(sql, values)
    conn.commit()


# ==================================================
# 11. 실행
# ==================================================
def run(cursor, conn):

    current, previous = get_sensor_data(cursor)

    if current is None:
        print("조회된 데이터가 없습니다.")
        return

    results = analyze(current, previous)

    print("\n측정시각:", current["input_time"])

    for name, result in results.items():
        print(
            f"{name:12} "
            f"기준값={result['standard']} "
            f"현재값={result['value']} "
            f"점수={result['score']} "
            f"알람={result['alarm']}"
        )

    save_analysis(cursor, conn, current, results)

    print("\nai_analysis INSERT 완료")


# ==================================================
# 12. MAIN
# ==================================================
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