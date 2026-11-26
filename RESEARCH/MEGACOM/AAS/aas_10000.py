

import json
import mysql.connector
import os

from datetime import datetime, date
from decimal import Decimal


# ==================================================
# 1. 설정
# ==================================================

DB_CONFIG = {
    "host": "121.181.35.7",
    "port": 3307,
    "user": "mega_admin",
    "password": "megaComp!#%",
    "database": "airpredict"
}

DEVICE_ID = "R00012"

LIMIT = 10000

OUTPUT_FILE = "MEGACOM_10000.json"


# ==================================================
# 2. 센서 정의
# ==================================================

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


# ==================================================
# 3. MySQL 데이터 조회
# ==================================================

def get_data():

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

        cursor.execute(sql, (DEVICE_ID, LIMIT))

        rows = cursor.fetchall()

        return list(reversed(rows))

    finally:
        cursor.close()
        conn.close()


# ==================================================
# 4. Property 생성
# ==================================================

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


# ==================================================
# 5. Record 생성
# ==================================================

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

    return {
        "modelType": "SubmodelElementCollection",
        "idShort": f"Record_{index:06d}",
        "value": properties
    }


# ==================================================
# 6. AAS JSON 생성
# ==================================================

def create_aas(rows):

    device_id = DEVICE_ID

    aas_id = (
        f"urn:megacom:aas:{device_id}:history10000"
    )

    submodel_id = (
        f"urn:megacom:submodel:{device_id}:history10000"
    )

    records = []

    for index, row in enumerate(rows, start=1):

        records.append(
            make_record(row, index)
        )

        if index % 1000 == 0:
            print(f"변환 완료: {index:,} / {len(rows):,}")

    return {
        "assetAdministrationShells": [
            {
                "modelType": "AssetAdministrationShell",
                "id": aas_id,
                "idShort": "MEGACOM_History10000",

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
                "idShort": "OperationHistory50000",
                "submodelElements": records
            }
        ],

        "conceptDescriptions": []
    }


# ==================================================
# 7. JSON 저장
# ==================================================

def save_json(aas):

    print("\nJSON 파일 저장 중...")

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            aas,
            f,
            ensure_ascii=False,
            separators=(",", ":")
        )

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)

    print(f"파일 크기: {size_mb:.2f} MB")


# ==================================================
# 8. 메인
# ==================================================

def main():

    print("=" * 60)
    print("MEGACOM 50,000건 AAS JSON 생성")
    print("=" * 60)

    print("MySQL 데이터 조회 중...")

    rows = get_data()

    if not rows:
        print("데이터가 없습니다.")
        return

    print(f"조회 건수: {len(rows):,}")

    print("최초 측정시각:", rows[0]["input_time"])
    print("최종 측정시각:", rows[-1]["input_time"])

    aas = create_aas(rows)

    save_json(aas)

    print("=" * 60)
    print("AAS JSON 생성 완료")
    print("파일:", OUTPUT_FILE)
    print("Record:", len(rows))
    print("Property:", len(rows) * 13)
    print("=" * 60)


if __name__ == "__main__":
    main()