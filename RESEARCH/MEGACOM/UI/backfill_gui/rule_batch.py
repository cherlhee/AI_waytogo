


import os
import math
import argparse
import re
from datetime import datetime, timedelta

import mysql.connector


# ==========================================================
# 1. 기본 설정
# ==========================================================

COM_CODE = "C00088"
DEVICE_IDS = ("R00012", "R00047", "R00048")

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

def get_sensor_data(cursor, device_id, after_time=None, limit=100):

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

    # 각 장비별로 미처리 시각을 순서대로 조회한다.
    # 기존 ai_analysis에 존재하는 시각은 재분석하지 않는다.
    sql = f"""
        SELECT d.input_time, {', '.join('d.`' + c + '`' for c in columns)}
        FROM `{SOURCE_TABLE}` AS d
        WHERE d.comcode = %s AND d.deviceId = %s
          AND d.input_time >= %s
          AND d.input_time < %s
          AND (%s IS NULL OR d.input_time > %s)
          AND NOT EXISTS (
              SELECT 1 FROM `{TARGET_TABLE}` AS a
              WHERE a.comcode=d.comcode AND a.deviceId=d.deviceId
                AND a.input_time=d.input_time
          )
        ORDER BY d.input_time ASC
        LIMIT %s
    """
    cursor.execute(sql, (COM_CODE, device_id, BACKFILL_FROM, BACKFILL_TO,
                         after_time, after_time, limit))
    keys = ["input_time"] + columns
    return [dict(zip(keys, row)) for row in cursor.fetchall()]


def get_previous_sensor_data(cursor, device_id, before_time):
    columns = list(dict.fromkeys(
        col for sensor in SENSORS.values() for col in sensor["columns"]
    ))
    sql = f"""SELECT input_time, {', '.join('`' + c + '`' for c in columns)}
              FROM `{SOURCE_TABLE}`
              WHERE comcode=%s AND deviceId=%s AND input_time < %s
              ORDER BY input_time DESC LIMIT 1"""
    cursor.execute(sql, (COM_CODE, device_id, before_time))
    row = cursor.fetchone()
    return dict(zip(["input_time"] + columns, row)) if row else None





# ==========================================================
# 9-1. 공통 기준값 조회 (센서별 하나의 외부 테이블)
# ==========================================================

def get_standard(cursor, sensor, device_id):
    table = sensor.get("standard_table")
    column = sensor.get("standard_column")
    if not table and not column:
        return to_float(sensor.get("standard"))
    if not table or not column:
        raise ValueError(f"기준값 설정 오류: table={table!r}, column={column!r}")

    extra_where = dict(sensor.get("standard_where", {}))
    if table == "st_comcode_set":
        extra_where["deviceId"] = device_id

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

def get_current_standard(cursor, current, device_id):

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
            device_id,
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

def get_oiltemp_standard(cursor, current, device_id):

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
            device_id,
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

def analyze(cursor, current, previous, device_id):

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
            standard = get_current_standard(cursor, current, device_id)

        elif standard_type == "oiltemp_sp":
            standard = get_oiltemp_standard(cursor, current, device_id)

        else:
            standard = get_standard(cursor, sensor, device_id)


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

def already_exists(cursor, input_time, device_id):

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
        (COM_CODE, device_id, input_time)
    )

    return cursor.fetchone() is not None


# ==========================================================
# 12. ai_analysis INSERT
# ==========================================================

def save_analysis(cursor, conn, current, results, device_id):

    input_time = str(current["input_time"])[:19]

    # 중복 확인
    if already_exists(cursor, input_time, device_id):

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
        device_id,
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

    # 호출자가 ai_analysis 트랜잭션을 확정

    return True


# ==========================================================
# 13. One-day historical backfill (no ai_alarm access)
# ==========================================================
BACKFILL_FROM = "2026-11-01 00:00:00"
BACKFILL_TO = "2026-11-02 00:00:00"


def connect_db():
    from config import DB_CONFIG
    settings = dict(DB_CONFIG)
    settings["autocommit"] = False
    return mysql.connector.connect(**settings)


def process_device(conn, device_id, batch_size):
    cursor = conn.cursor()
    watermark = None
    total = 0
    try:
        while True:
            rows = get_sensor_data(cursor, device_id, watermark, batch_size)
            if not rows:
                conn.rollback()
                return total
            previous = None
            saved_count = 0
            for current in rows:
                stamp = current["input_time"]
                # Recover the true previous source row even when already
                # analyzed rows were excluded from this batch.
                if previous is None or (parse_time(stamp) - parse_time(previous["input_time"])).total_seconds() != 5:
                    previous = get_previous_sensor_data(cursor, device_id, stamp)
                results = analyze(cursor, current, previous, device_id)
                saved_count += int(save_analysis(cursor, conn, current, results, device_id))
                previous = current
                watermark = stamp
            conn.commit()
            total += saved_count
            print(f"[{device_id}] batch={saved_count} total={total} last={watermark}", flush=True)
    except BaseException:
        conn.rollback()
        raise
    finally:
        cursor.close()


def main():
    global BACKFILL_FROM, BACKFILL_TO, COM_CODE
    parser = argparse.ArgumentParser(description="RULE historical backfill (inclusive calendar dates)")
    parser.add_argument("--comcode", default=COM_CODE)
    parser.add_argument("--date", help="Single day: YYYY-MM-DD")
    parser.add_argument("--start-date", help="First day: YYYY-MM-DD")
    parser.add_argument("--end-date", help="Last day (inclusive): YYYY-MM-DD")
    parser.add_argument("--device-id", choices=DEVICE_IDS)
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()
    COM_CODE = args.comcode
    if args.date and (args.start_date or args.end_date):
        parser.error("Use --date or --start-date/--end-date, not both")
    if bool(args.start_date) != bool(args.end_date):
        parser.error("Specify both --start-date and --end-date")
    try:
        start = datetime.strptime(args.date or args.start_date or "2026-11-01", "%Y-%m-%d")
        end = datetime.strptime(args.date or args.end_date or "2026-11-01", "%Y-%m-%d")
        if end < start:
            parser.error("--end-date must not precede --start-date")
        BACKFILL_FROM = start.strftime("%Y-%m-%d %H:%M:%S")
        BACKFILL_TO = (end + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OverflowError):
        parser.error("Dates must be valid YYYY-MM-DD values")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    devices = (args.device_id,) if args.device_id else DEVICE_IDS
    print(f"Backfill: {BACKFILL_FROM} <= input_time < {BACKFILL_TO}")
    print("Target: ai_analysis only; live alarm recording disabled")
    conn = connect_db()
    try:
        total = 0
        for device in devices:
            count = process_device(conn, device, args.batch_size)
            total += count
            print(f"[{device}] completed: {count} new rows", flush=True)
        print(f"Backfill completed: {total} new rows", flush=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
