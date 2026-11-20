

import mysql.connector
import json
from datetime import datetime
from decimal import Decimal

# ======================================
# 1. MySQL 연결
# ======================================



# 1. MySQL 연결
conn = mysql.connector.connect(
    host="121.181.35.7",
    port=3307,
    user="mega_admin",
    password="megaComp!#%",
    database="airpredict",
    connection_timeout=10
)

cursor = conn.cursor(dictionary=True)

# ======================================
# 2. ai_data 최신 1건 조회
# ======================================

sql = """
SELECT
    deviceId,
    input_time,
    io003,
    io010,
    io028,
    io044,
    io045,
    io046
FROM ai_data
WHERE deviceId = 'R00012'
ORDER BY input_time DESC
LIMIT 1
"""

cursor.execute(sql)
data = cursor.fetchone()

cursor.close()
conn.close()

if data is None:
    raise RuntimeError("조회된 데이터가 없습니다.")

# ======================================
# 3. AAS Property 생성
# ======================================

def property_value(name, value):

    if isinstance(value, Decimal):
        value = float(value)

    return {
        "modelType": "Property",
        "idShort": name,
        "valueType": "xs:double",
        "value": None if value is None else str(value)
    }

# ======================================
# 4. AAS JSON 생성
# ======================================

device_id = str(data["deviceId"])

aas_id = f"urn:megacom:aas:{device_id}"
submodel_id = f"urn:megacom:submodel:{device_id}:operation"

aas = {
    "assetAdministrationShells": [
        {
            "modelType": "AssetAdministrationShell",
            "id": aas_id,
            "idShort": "MEGACOM_Compressor",
            "assetInformation": {
                "assetKind": "Instance",
                "globalAssetId": f"urn:megacom:asset:{device_id}"
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
            "submodelElements": [
                {
                    "modelType": "Property",
                    "idShort": "InputTime",
                    "valueType": "xs:string",
                    "value": str(data["input_time"])
                },
                property_value("OilTemperature", data["io003"]),
                property_value("ActivePower", data["io010"]),
                property_value("LoadRate", data["io028"]),
                property_value("Pressure", data["io044"]),
                property_value("FlowmeterTemperature", data["io045"]),
                property_value("FlowRate", data["io046"])
            ]
        }
    ],
    "conceptDescriptions": []
}

# ======================================
# 5. JSON 저장
# ======================================

with open("MEGACOM_test.json", "w", encoding="utf-8") as f:
    json.dump(aas, f, ensure_ascii=False, indent=4)

print("AAS JSON 파일 생성 완료")
print("장비:", device_id)
print("측정시각:", data["input_time"])
print("파일: MEGACOM_test.json")