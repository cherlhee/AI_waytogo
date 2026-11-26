


import json
import os
from datetime import datetime
from decimal import Decimal

import mysql.connector


# ==========================================
# 1. MySQL 설정
# ==========================================

DB_CONFIG = {
    "host": os.environ["MEGACOM_DB_HOST"],
    "port": int(os.getenv("MEGACOM_DB_PORT", "3306")),
    "user": os.environ["MEGACOM_DB_USER"],
    "password": os.environ["MEGACOM_DB_PASSWORD"],
    "database": os.environ["MEGACOM_DB_NAME"],
}


DEVICE_ID = "R00012"

OUTPUT_FILE = "MEGACOM_ai_data.json"


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
    "io009": "CurrentW",
    "io004": "VoltageUV",
    "io005": "VoltageVW",
}


# ==========================================
# 3. MySQL 최신 데이터 조회
# ==========================================

def get_latest_data():

    conn = mysql.connector.connect(**DB_CONFIG)

    cursor = conn.cursor(dictionary=True)

    try:
        columns = [
            "comcode",
            "deviceId",
            "input_time"
        ] + list(SENSORS.keys())

        sql = f"""
            SELECT {", ".join(columns)}
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


# ==========================================
# 4. AAS Property 생성
# ==========================================

def make_property(name, value, value_type="xs:double"):

    if value is None:
        return None

    if isinstance(value, Decimal):
        value = float(value)

    return {
        "modelType": "Property",
        "idShort": name,
        "valueType": value_type,
        "value": str(value)
    }


# ==========================================
# 5. AAS JSON 생성
# ==========================================

def create_aas(data):

    device_id = str(data["deviceId"])
    comcode = str(data["comcode"])

    aas_id = (
        f"urn:megacom:{comcode}:aas:{device_id}"
    )

    submodel_id = (
        f"urn:megacom:{comcode}:submodel:"
        f"{device_id}:operation"
    )

    properties = []

    # 측정시각
    input_time = data["input_time"]

    if isinstance(input_time, datetime):
        input_time = input_time.isoformat()

    properties.append(
        make_property(
            "InputTime",
            input_time,
            "xs:dateTime"
        )
    )

    # 센서 데이터
    for column, name in SENSORS.items():

        prop = make_property(
            name,
            data.get(column)
        )

        if prop is not None:
            properties.append(prop)

    aas = {
        "assetAdministrationShells": [
            {
                "modelType": "AssetAdministrationShell",
                "id": aas_id,
                "idShort": "MEGACOM_Compressor",
                "assetInformation": {
                    "assetKind": "Instance",
                    "globalAssetId": (
                        f"urn:megacom:{comcode}:asset:"
                        f"{device_id}"
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


# ==========================================
# 6. 파일 저장
# ==========================================

def main():

    data = get_latest_data()

    if data is None:
        print("조회된 데이터가 없습니다.")
        return

    aas = create_aas(data)

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

    print("AAS JSON 생성 완료")
    print("장비:", data["deviceId"])
    print("측정시각:", data["input_time"])
    print("파일:", OUTPUT_FILE)


if __name__ == "__main__":
    main()