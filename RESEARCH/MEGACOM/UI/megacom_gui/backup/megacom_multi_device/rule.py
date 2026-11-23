


import os
import time
import math
import argparse
import re
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
# standard_table / standard_column / standard_where: 외부 기준값 조회 설정
# standard: 미설정 센서의 기존 고정 기준값 (외부 테이블 정보 입력 후 제거 가능)
# ==========================================================

SENSORS = {

    "유량계온도": {
        "columns": ["io045"],
        "code": "045",
        "standard_save_column": "gradestd_045",
        "standard_table": "",
        "standard_column": "",
        "standard_where": {},
        "standard": 30
    },

    "전압평균": {
        "columns": ["io004", "io005"],
        "code": "004",
        "standard_save_column": "gradestd_044",
        "standard_table": "st_comcode_set",
        "standard_column": "std_high",
        "standard_where": {"std_item": "io004"}
    },

    "전류평균": {
        "columns": ["io007", "io008", "io009"],
        "code": "007",
        "standard_save_column": "gradestd_007",
        "standard_type": "current_sp"
    },

    "토출압력": {
        "columns": ["io001"],
        "code": "001",
        "standard_save_column": "gradestd_001",
        "standard_table": "st_comcode_set",
        "standard_column": "std_high",
        "standard_where": {"std_item": "io001"},
        "standard": 8
    },

    "오일온도": {
        "columns": ["io003"],
        "code": "003",
        "standard_save_column": "gradestd_003",
        "standard_type": "oiltemp_sp"
    },

    "소모품교체주기": {
        "columns": ["io030"],
        "code": "030",
        "standard_save_column": "gradestd_030",
        "standard_table": "st_sysoption",
        "standard_column": "charval",
        "standard_comcode_column": None,  # 이 테이블에는 업체코드 컬럼이 없는 경우
        "standard_where": {"sysitem": "SOMO_HOUR"},
        "standard": 1220
    },

    "선간전압불균형": {
        "columns": ["io004", "io005"],
        "code": "900",
        "standard_save_column": "gradestd_900",
        "standard_table": "",
        "standard_column": "",
        "standard_where": {},
        "standard": 10
    },

    "전류불균형": {
        "columns": ["io007", "io008", "io009"],
        "code": "901",
        "standard_save_column": "gradestd_901",
        "standard_table": "",
        "standard_column": "",
        "standard_where": {},
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


    # 선간전압불균형
    if name == "선간전압불균형":

        if any(v <= 0 for v in values):
            return None

        voltage_max = max(values)
        voltage_min = min(values)

        voltage_diff = voltage_max - voltage_min

        unbalance = (
            voltage_diff / voltage_max
        ) * 100

        return unbalance



    # 전류 불균형
    if name == "전류불균형":

        if any(v <= 0 for v in values):
            return None

        current_max = max(values)
        current_min = min(values)

        current_diff = current_max - current_min

        unbalance = (
            current_diff / current_max
        ) * 100

        return unbalance
    
    

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

    # SENSORS에 등록된 컬럼
    columns = list(dict.fromkeys(
        col
        for sensor in SENSORS.values()
        for col in sensor["columns"]
    ))

    # SP 기준값 조회에 필요한 컬럼 추가
    required_columns = [
        "io029",   # 주파수
        "io001",   # 토출압력
        "io045"    # 외부온도 (유량계 온도)
    ]

    for col in required_columns:
        if col not in columns:
            columns.append(col)

    # SQL 컬럼 문자열 생성
    column_sql = ", ".join(
        f"`{column}`" for column in columns
    )

    # 최신 데이터 2건 조회
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

    # 컬럼명 구성
    keys = ["input_time"] + columns

    # 최신 데이터
    current = dict(zip(keys, rows[0]))

    # 이전 데이터
    previous = None

    if len(rows) > 1:
        previous = dict(zip(keys, rows[1]))

    return current, previous





# ==========================================================
# 9-1. 공통 기준값 조회 (센서별 하나의 외부 테이블)
# ==========================================================

def get_standard(cursor, sensor):
    table = sensor.get("standard_table")
    column = sensor.get("standard_column")
    if not table and not column:
        return to_float(sensor.get("standard"))
    if not table or not column:
        raise ValueError(f"기준값 설정 오류: table={table!r}, column={column!r}")

    extra_where = sensor.get("standard_where", {})

    # SQL 식별자는 바인딩할 수 없으므로 설정값의 형식을 검증하고 백틱 처리
    def quote_identifier(identifier):
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", identifier):
            raise ValueError(f"잘못된 DB 식별자: {identifier!r}")
        return f"`{identifier}`"

    table_sql = quote_identifier(table)
    column_sql = quote_identifier(column)
    comcode_column = sensor.get("standard_comcode_column", "comcode")
    conditions = []
    params = []
    if comcode_column:
        conditions.append(f"{quote_identifier(comcode_column)} = %s")
        params.append(COM_CODE)

    for field, expected in extra_where.items():
        conditions.append(f"{quote_identifier(field)} = %s")
        params.append(expected)

    where_sql = f" WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT {column_sql} FROM {table_sql}{where_sql} LIMIT 2"
    try:
        cursor.execute(sql, tuple(params))
    except mysql.connector.Error:
        print(f"[기준값 조회 실패] SQL={sql}, PARAMS={params}")
        raise
    rows = cursor.fetchall()
    if not rows:
        print(f"[기준값 없음] table={table}, 조건={extra_where}, comcode={COM_CODE}")
        return None
    if len(rows) > 1:
        raise ValueError(f"기준값 조회 결과가 2건 이상입니다: {table}, {extra_where}")
    return to_float(rows[0][0])





# ==========================================================
# 9-2. 기준전류 조회 (Stored Procedure)
# ==========================================================

def get_current_standard(cursor, current):

    frequency = to_float(current.get("io029"))
    pressure = to_float(current.get("io001"))

    if frequency is None or pressure is None:
        return None

    cursor.execute(
        """
        CALL sp_get_current_std(
            %s, %s, %s, %s
        )
        """,
        (
            COM_CODE,
            DEVICE_ID,
            frequency,
            pressure
        )
    )

    row = cursor.fetchone()

    print("[기준전류 SP 반환값]", row)

    standard = to_float(row[5]) if row else None

    while cursor.nextset():
        pass

    return standard






# ==========================================================
# 9-3. 기준오일온도 조회 (Stored Procedure)
# ==========================================================

def get_oiltemp_standard(cursor, current):

    frequency = to_float(current.get("io029"))
    pressure = to_float(current.get("io001"))
    outside_temp = to_float(current.get("io045"))

    if any(v is None for v in (
        frequency,
        pressure,
        outside_temp
    )):
        return None

    cursor.execute(
        """
        CALL sp_get_oiltemp_std(
            %s, %s, %s, %s, %s
        )
        """,
        (
            COM_CODE,
            DEVICE_ID,
            frequency,
            pressure,
            outside_temp
        )
    )

    row = cursor.fetchone()

    print("[기준오일온도 SP 반환값]", row)

    standard = to_float(row[4]) if row else None

    while cursor.nextset():
        pass

    return standard





# ==========================================================
# 10. 룰베이스 분석
# ==========================================================

def analyze(cursor, current, previous):

    results = {}

    for name, sensor in SENSORS.items():

        values = [
            to_float(current.get(col))
            for col in sensor["columns"]
        ]

        value = calculate_value(name, values)



        # standard = get_standard(cursor, sensor)
        standard_type = sensor.get("standard_type")

        if standard_type == "current_sp":
            standard = get_current_standard(cursor, current)

        elif standard_type == "oiltemp_sp":
            standard = get_oiltemp_standard(cursor, current)

        else:
            standard = get_standard(cursor, sensor)


        # 불균형 항목은 측정값 중 최댓값을 저장 기준값으로 사용
        if name in ("선간전압불균형", "전류불균형"):
            standard_to_save = max(values) if value is not None else None
        else:
            standard_to_save = standard




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
            "standard_to_save": standard_to_save,
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
        "input_time",
        "io029"
    ]

    values = [
        COM_CODE,
        DEVICE_ID,
        input_time,
        to_float(current.get("io029"))
    ]

    # 8개 항목의 현재값, 점수, 알람 및 지정된 기준값만 저장
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

        # 외부 테이블 조회값 또는 고정 기준값을 지정 컬럼에 저장
        standard_save_column = sensor.get("standard_save_column")
        if standard_save_column:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", standard_save_column):
                raise ValueError(f"잘못된 기준값 저장 컬럼: {standard_save_column!r}")
            if standard_save_column in columns:
                raise ValueError(f"중복 저장 컬럼: {standard_save_column}")
            columns.append(standard_save_column)
            values.append(result["standard_to_save"])

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
    results = analyze(cursor, current, previous)

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

    parser.add_argument("--device-id", default="R00012")
    args = parser.parse_args()
    global DEVICE_ID
    DEVICE_ID = args.device_id

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