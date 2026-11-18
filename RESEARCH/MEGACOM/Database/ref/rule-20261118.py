


import os
import time
import math
import argparse
from datetime import datetime

import mysql.connector


# ==========================================================
# 1. 기본 설정
# ==========================================================

COM_CODE = "C00088"
DEVICE_ID = "R00012"

SOURCE_TABLE = "ai_data"
TARGET_TABLE = "ai_analysis"

DEFAULT_INTERVAL = 5.0


# ==========================================================
# 2. 센서 항목 설정
#
# columns : ai_data에서 조회할 컬럼
# code    : ai_analysis에 저장할 컬럼 번호
# standard: 기준값 (현재 임시값)
# ==========================================================

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


# ==========================================================
# 3. 숫자 변환
# ==========================================================

def to_float(value):

    try:
        number = float(value)

        if not math.isfinite(number):
            return None

        return number

    except (TypeError, ValueError):
        return None


# ==========================================================
# 4. 항목별 점수 계산
# ==========================================================

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

    if standard is None or standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0

    if diff < 7:
        return 40

    return 70


# 전류 평균
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


# 토출압력: 이전 5초 측정값과 비교
def score_pressure(value, previous):

    if previous is None:
        return None

    diff = abs(value - previous)

    if diff >= 3:
        return 70

    return 0


# 오일온도
def score_oil(value, standard):

    if standard is None or standard <= 0:
        return None

    diff = abs(value - standard) / standard * 100

    if diff < 5:
        return 0

    if diff < 10:
        return 40

    return 70


# 소모품 교체주기
def score_consumable(value, standard):

    if standard is None or standard <= 0:
        return None

    ratio = value / standard * 100

    if ratio < 90:
        return 0

    if ratio < 100:
        return 40

    return 70


# 선간전압 불균형
def score_voltage_unbalance(value, standard):

    if value < 7:
        return 0

    if value <= 10:
        return 40

    return 70


# 전류 불균형
def score_current_unbalance(value, standard):

    if value < 10:
        return 0

    if value <= 15:
        return 40

    return 70


# ==========================================================
# 5. 판정 함수 연결
# ==========================================================

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


# ==========================================================
# 6. 알람단계
#
# 0 = 정상
# 5 = 주의
# 9 = 경고
# ==========================================================

def set_alarm(score):

    if score is None:
        return None

    if score == 0:
        return 0

    if score < 70:
        return 5

    return 9


# ==========================================================
# 7. 센서 현재값 계산
# ==========================================================

def calculate_value(name, values):

    if any(v is None for v in values):
        return None

    # 전류는 0 이하를 결측 처리
    if name in ("전류평균", "전류불균형"):

        if any(v <= 0 for v in values):
            return None

    # 전압 불균형
    if name == "선간전압불균형":

        if any(v <= 0 for v in values):
            return None

        average = sum(values) / len(values)

        if average <= 0:
            return None

        return (
            max(abs(v - average) for v in values)
            / average * 100
        )

    # 전류 불균형
    if name == "전류불균형":

        average = sum(values) / len(values)

        if average <= 0:
            return None

        return (
            max(abs(v - average) for v in values)
            / average * 100
        )

    # 나머지 센서: 평균 또는 단일 측정값
    return sum(values) / len(values)


# ==========================================================
# 8. 측정시각 변환
# ==========================================================

def parse_time(value):

    if isinstance(value, datetime):
        return value

    return datetime.strptime(
        str(value)[:19],
        "%Y-%m-%d %H:%M:%S"
    )


# ==========================================================
# 9. 최신 데이터 조회
# ==========================================================

def get_sensor_data(cursor):

    columns = list(dict.fromkeys(
        col
        for sensor in SENSORS.values()
        for col in sensor["columns"]
    ))

    column_sql = ", ".join(
        f"`{column}`" for column in columns
    )

    sql = f"""
        SELECT input_time, {column_sql}
        FROM `{SOURCE_TABLE}`
        WHERE comcode = %s
          AND deviceId = %s
        ORDER BY input_time DESC
        LIMIT 2
    """

    cursor.execute(
        sql,
        (COM_CODE, DEVICE_ID)
    )

    rows = cursor.fetchall()

    if not rows:
        return None, None

    keys = ["input_time"] + columns

    current = dict(zip(keys, rows[0]))

    previous = None

    if len(rows) > 1:
        previous = dict(zip(keys, rows[1]))

    return current, previous


# ==========================================================
# 10. 룰베이스 분석
# ==========================================================

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

                old_pressure = None

                if previous is not None:

                    try:
                        current_time = parse_time(
                            current["input_time"]
                        )

                        previous_time = parse_time(
                            previous["input_time"]
                        )

                        time_diff = (
                            current_time - previous_time
                        ).total_seconds()

                        if time_diff == 5:

                            old_pressure = to_float(
                                previous.get("io001")
                            )

                    except (ValueError, TypeError):
                        pass

                score = score_pressure(
                    value,
                    old_pressure
                )

            else:

                score = SCORE_FUNCTIONS[name](
                    value,
                    standard
                )

        results[name] = {
            "value": value,
            "standard": standard,
            "score": score,
            "alarm": set_alarm(score)
        }

    return results


# ==========================================================
# 11. DB 중복 저장 확인
# ==========================================================

def already_exists(cursor, input_time):

    sql = f"""
        SELECT 1
        FROM `{TARGET_TABLE}`
        WHERE comcode = %s
          AND deviceId = %s
          AND input_time = %s
        LIMIT 1
    """

    cursor.execute(
        sql,
        (COM_CODE, DEVICE_ID, input_time)
    )

    return cursor.fetchone() is not None


# ==========================================================
# 12. ai_analysis INSERT
# ==========================================================

def save_analysis(cursor, conn, current, results):

    input_time = str(current["input_time"])[:19]

    # 중복 확인
    if already_exists(cursor, input_time):

        print(
            f"[{datetime.now()}] "
            f"이미 저장된 데이터: {input_time}"
        )

        return False

    columns = [
        "comcode",
        "deviceId",
        "input_time"
    ]

    values = [
        COM_CODE,
        DEVICE_ID,
        input_time
    ]

    # 8개 항목의 현재값, 점수, 알람 추가
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

    column_sql = ", ".join(
        f"`{column}`" for column in columns
    )

    placeholders = ", ".join(
        ["%s"] * len(values)
    )

    sql = f"""
        INSERT INTO `{TARGET_TABLE}`
        ({column_sql})
        VALUES ({placeholders})
    """

    cursor.execute(sql, values)

    conn.commit()

    return True


# ==========================================================
# 13. 분석 실행
# ==========================================================

def run(cursor, conn, last_input_time=None):

    current, previous = get_sensor_data(cursor)

    if current is None:

        print(
            f"[{datetime.now()}] "
            "조회된 데이터가 없습니다."
        )

        return last_input_time

    input_time = str(current["input_time"])[:19]

    # 실행 중 중복 처리 방지
    if input_time == last_input_time:

        print(
            f"[{datetime.now()}] "
            "신규 데이터 없음"
        )

        return last_input_time

    # 8개 항목 분석
    results = analyze(current, previous)

    print("\n" + "=" * 65)

    print("측정시각:", input_time)

    print("=" * 65)

    for name, result in results.items():

        print(
            f"{name:12} "
            f"기준값={result['standard']} "
            f"현재값={result['value']} "
            f"점수={result['score']} "
            f"알람={result['alarm']}"
        )

    # DB 저장
    saved = save_analysis(
        cursor,
        conn,
        current,
        results
    )

    if saved:

        print(
            f"\n[{datetime.now()}] "
            "ai_analysis INSERT 완료"
        )

    return input_time


# ==========================================================
# 14. MAIN
# ==========================================================

def main():

    parser = argparse.ArgumentParser(
        description="MEGACOM 설비 룰베이스 분석"
    )

    # 1회 실행 옵션
    parser.add_argument(
        "--once",
        action="store_true",
        help="한 번만 실행하고 종료"
    )

    # 반복 실행 간격
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL,
        help="반복 실행 간격(초), 기본값 5초"
    )

    args = parser.parse_args()

    if args.interval <= 0:
        parser.error("--interval은 0보다 커야 합니다.")

    conn = None
    cursor = None

    last_input_time = None

    try:

        # MySQL 연결
        conn = mysql.connector.connect(

            host=os.getenv(
                "DB_HOST",
                "121.181.35.7"
            ),

            port=int(
                os.getenv(
                    "DB_PORT",
                    "3307"
                )
            ),

            user=os.getenv(
                "DB_USER",
                "mega_admin"
            ),
            
            password="megaComp!#%",

            database=os.getenv(
                "DB_NAME",
                "airpredict"
            ),

            connection_timeout=10
        )

        cursor = conn.cursor()

        print("\nMySQL 연결 성공")

        print("업체코드:", COM_CODE)
        print("설비번호:", DEVICE_ID)

        # ----------------------------------------------
        # 1회 실행
        # ----------------------------------------------
        if args.once:

            print("\n실행모드: 1회 실행")

            run(
                cursor,
                conn
            )

        # ----------------------------------------------
        # 연속 실행
        # ----------------------------------------------
        else:

            print("\n실행모드: 연속 실행")

            print(
                f"실행간격: {args.interval}초"
            )

            print(
                "종료하려면 Ctrl + C"
            )

            while True:

                try:

                    # DB 연결 확인
                    conn.ping(
                        reconnect=True,
                        attempts=3,
                        delay=2
                    )

                    last_input_time = run(
                        cursor,
                        conn,
                        last_input_time
                    )

                except mysql.connector.Error as err:

                    conn.rollback()

                    print(
                        f"[{datetime.now()}] "
                        f"MySQL Error: {err}"
                    )

                except Exception as err:

                    conn.rollback()

                    print(
                        f"[{datetime.now()}] "
                        f"Error: {err}"
                    )

                time.sleep(
                    args.interval
                )

    except KeyboardInterrupt:

        print(
            "\n사용자 요청으로 종료합니다."
        )

    except mysql.connector.Error as err:

        print(
            "MySQL 연결 오류:",
            err
        )

    finally:

        if cursor is not None:
            cursor.close()

        if conn is not None and conn.is_connected():
            conn.close()

        print("\n프로그램 종료")


# ==========================================================
# 15. 프로그램 시작
# ==========================================================

if __name__ == "__main__":
    main()