

import json
import mysql.connector

from datetime import datetime
from decimal import Decimal


# ==================================================
# 1. MySQL 연결 설정
# ==================================================

DB_CONFIG = {
    "host": "121.181.35.7",
    "port": 3307,
    "user": "mega_admin",
    "password": "megaComp!#%",
    "database": "airpredict"
}

# 
# # 1. MySQL 연결
# conn = mysql.connector.connect(
#     host="121.181.35.7",
#     port=3307,
#     user="mega_admin",
#     password="megaComp!#%",
#     database="airpredict",
#     connection_timeout=10
# )


DEVICE_ID = "R00012"

OUTPUT_FILE = "MEGACOM_test_13.json"


# ==================================================
# 2. 센서 컬럼 정의
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
# 3. MySQL 최신 데이터 1건 조회
# ==================================================

def get_latest_data():

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
            LIMIT 1
        """

        cursor.execute(sql, (DEVICE_ID,))

        return cursor.fetchone()

    finally:
        cursor.close()
        conn.close()


# ==================================================
# 4. AAS Property 생성
# ==================================================

def make_property(name, value, value_type="xs:double"):

    if isinstance(value, Decimal):
        value = float(value)

    if isinstance(value, datetime):
        value = value.isoformat()

    return {
        "modelType": "Property",
        "idShort": name,
        "valueType": value_type,
        "value": None if value is None else str(value)
    }


# ==================================================
# 5. AAS JSON 생성
# ==================================================

def create_aas(data):

    device_id = str(data["deviceId"])
    comcode = str(data["comcode"])

    aas_id = f"urn:megacom:aas:{device_id}"

    submodel_id = (
        f"urn:megacom:submodel:{device_id}:operation"
    )

    # ----------------------------------------------
    # 기본 정보
    # ----------------------------------------------

    properties = [
        make_property(
            "ComCode",
            comcode,
            "xs:string"
        ),

        make_property(
            "DeviceId",
            device_id,
            "xs:string"
        ),

        make_property(
            "InputTime",
            data["input_time"],
            "xs:dateTime"
        )
    ]

    # ----------------------------------------------
    # 센서 데이터
    # ----------------------------------------------

    for column, name in SENSORS.items():

        properties.append(
            make_property(
                name,
                data[column]
            )
        )

    # ----------------------------------------------
    # AAS Environment
    # ----------------------------------------------

    aas = {
        "assetAdministrationShells": [
            {
                "modelType": "AssetAdministrationShell",
                "id": aas_id,
                "idShort": "MEGACOM_Compressor",

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
                "idShort": "OperationData",
                "submodelElements": properties
            }
        ],

        "conceptDescriptions": []
    }

    return aas


# ==================================================
# 6. JSON 파일 저장
# ==================================================

def save_aas(aas):

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            aas,
            f,
            ensure_ascii=False,
            indent=4
        )


# ==================================================
# 7. 메인 프로그램
# ==================================================

def main():

    print("=" * 60)
    print("MEGACOM ai_data → AAS JSON")
    print("=" * 60)

    # MySQL 조회
    data = get_latest_data()

    if data is None:
        print("조회된 데이터가 없습니다.")
        return

    print("장비 ID :", data["deviceId"])
    print("측정시각 :", data["input_time"])

    # AAS 생성
    aas = create_aas(data)

    # JSON 저장
    save_aas(aas)

    print("-" * 60)
    print("AAS JSON 생성 완료")
    print("파일 :", OUTPUT_FILE)
    print("Property 개수 :", 3 + len(SENSORS))
    print("=" * 60)


if __name__ == "__main__":
    main()