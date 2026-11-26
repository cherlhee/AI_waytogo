import json
import argparse
import mysql.connector

from datetime import datetime, date
from decimal import Decimal


# ==========================================
# 1. MySQL 연결
# ==========================================

DB_CONFIG = {
    "host": "121.181.35.7",
    "port": 3307,
    "user": "mega_admin",
    "password": "megaComp!#%",
    "database": "airpredict"
}

DEVICE_ID = "R00012"

OUTPUT_FILE = "MEGACOM_100.json"


# ==========================================
# 2. 센서 정의
# ==========================================

SENSORS = {
    "io003": "OilTemperature",
    "io010": "ActivePower",
    "io028": "LoadRate",
    "io044": "Pressure",
    "io045": "FlowmeterTemperature",
    "io046": "FlowRate",
    "io048": "Humidity",
    "io007": "CurrentU",
    "io008": "CurrentV",
    "io009": "CurrentW"
}


# ==========================================
# 3. MySQL 데이터 조회
# ==========================================

def get_data(limit):

    conn = mysql.connector.connect(**DB_CONFIG)

    cursor = conn.cursor(dictionary=True)

    try:

        sql = """
            SELECT
                comcode,
                deviceId,
                input_time,
                io003,
                io010,
                io028,
                io044,
                io045,
                io046,
                io048,
                io007,
                io008,
                io009
            FROM ai_data
            WHERE deviceId = %s
            ORDER BY input_time DESC
            LIMIT %s
        """

        cursor.execute(sql, (DEVICE_ID, limit))

        rows = cursor.fetchall()

        return rows

    finally:
        cursor.close()
        conn.close()


# ==========================================
# 4. Property 생성
# ==========================================

def make_property(name, value, value_type="xs:double"):

    if isinstance(value, Decimal):
        value = float(value)

    if isinstance(value, (datetime, date)):
        value = value.isoformat()

    return {
        "modelType": "Property",
        "idShort": name,
        "valueType": value_type,
        "value": None if value is None else str(value)
    }


# ==========================================
# 5. 측정 기록 생성
# ==========================================

def make_record(row, index):

    properties = [
        make_property(
            "ComCode",
            row["comcode"],
            "xs:string"
        ),
        make_property(
            "DeviceId",
            row["deviceId"],
            "xs:string"
        ),
        make_property(
            "InputTime",
            row["input_time"],
            "xs:dateTime"
        )
    ]

    for column, name in SENSORS.items():

        properties.append(
            make_property(name, row[column])
        )

    record = {
        "modelType": "SubmodelElementCollection",
        "idShort": f"Record_{index:06d}",
        "value": properties
    }

    return record


# ==========================================
# 6. AAS JSON 생성
# ==========================================

def create_aas(rows):

    if not rows:
        raise ValueError("조회된 데이터가 없습니다.")

    device_id = str(rows[0]["deviceId"])

    # 기존 AAS와 충돌하지 않는 테스트용 ID
    aas_id = f"urn:megacom:aas:{device_id}:history100"

    submodel_id = (
        f"urn:megacom:submodel:{device_id}:history100"
    )

    records = []

    # 오래된 데이터부터 정렬
    rows = list(reversed(rows))

    for index, row in enumerate(rows, start=1):

        record = make_record(row, index)

        records.append(record)

    aas = {
        "assetAdministrationShells": [
            {
                "modelType": "AssetAdministrationShell",
                "id": aas_id,
                "idShort": "MEGACOM_History100",
                "assetInformation": {
                    "assetKind": "Instance",
                    "globalAssetId": (
                        f"urn:megacom:asset:{device_id}"
                    )
                },
                "submodels": [
                    {
                        "type": "ModelReference",
                        "keys": [
                            {
                                "type": "Submodel",
                                "value": submodel_id
                            }
                        ]
                    }
                ]
            }
        ],
        "submodels": [
            {
                "modelType": "Submodel",
                "id": submodel_id,
                "idShort": "OperationHistory100",
                "submodelElements": records
            }
        ],
        "conceptDescriptions": []
    }

    return aas


# ==========================================
# 7. JSON 저장
# ==========================================

def save_json(aas):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            aas,
            f,
            ensure_ascii=False,
            indent=2
        )


# ==========================================
# 8. 메인
# ==========================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=100
    )

    args = parser.parse_args()

    if args.limit <= 0:
        parser.error("--limit은 1 이상이어야 합니다.")

    print("=" * 60)
    print("MEGACOM ai_data → AAS JSON")
    print("=" * 60)

    rows = get_data(args.limit)

    if not rows:
        print("조회된 데이터가 없습니다.")
        return

    print("장비 ID :", DEVICE_ID)
    print("데이터 건수 :", len(rows))

    aas = create_aas(rows)

    save_json(aas)

    print("AAS JSON 생성 완료")
    print("파일 :", OUTPUT_FILE)
    print("Record 개수 :",
          len(aas["submodels"][0]["submodelElements"]))

    print("=" * 60)


if __name__ == "__main__":
    main()