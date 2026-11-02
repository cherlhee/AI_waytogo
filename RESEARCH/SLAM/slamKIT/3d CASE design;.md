


  

![사용자 첨부 파일](blob:https://chatgpt.com/13dbd589-ec6c-499c-b29b-f3209773cfec)

make a cad drawing using freecad

## FreeCAD를 이용한 자율주행 SLAM 로봇카트 CAD 설계

제공하신 사진을 기준으로 FreeCAD에서 수정할 수 있는 3D CAD 모델을 제작하겠습니다.

사진에는 다음과 같은 구조가 있습니다.

- 알루미늄 판금형 직사각형 차체
    
- 메카넘 휠 4개
    
- 상단 LiDAR 센서 1개
    
- 전방 깊이 카메라 1개
    
- 상단 탈착식 커버
    
- 내부 Jetson Orin Nano, 배터리 및 모터제어보드 설치 공간
    

### 기본 설계 치수 (가정)

사진만으로 실제 치수를 알 수 없으므로 아래 크기를 적용하겠습니다.

|부품|설계 치수|
|---|---|
|차체 길이|300 mm|
|차체 폭|220 mm|
|차체 높이|90 mm|
|메카넘 휠|직경 80 mm × 4개|
|알루미늄 판재|두께 2 mm|
|LiDAR|직경 55 mm|
|전방 카메라|90 × 25 × 25 mm|

설계 결과는 FreeCAD에서 각 부품의 위치와 치수를 수정할 수 있도록 구성하겠습니다.

## CAD 파일 제작 완료

3D CAD 모델 (STEP)

FreeCAD에서 바로 열고 수정 가능한 3D 형상

STEP 파일

FreeCAD 매크로 (FCMacro)

부품별 모델을 생성하고 FCStd 프로젝트로 저장

매크로 파일

### FreeCAD에서 실행하는 방법

1. FreeCAD를 실행합니다.
    
2. STEP 파일을 `파일 → 열기`로 불러옵니다.
    
3. 마우스로 회전하면서 차체와 바퀴를 확인합니다.
    
4. 매크로 파일은 `매크로 → 매크로`에서 실행할 수 있습니다.
    

현재 모델은 사진을 바탕으로 만든 개념설계입니다. 메카넘 휠의 롤러는 단순화되어 있으며, 모터 고정홀, 판금 절곡부, 실제 센서 체결홀 등은 아직 상세 설계되지 않았습니다.

다음 단계에서는 이 모델을 기반으로 2mm 알루미늄 판금 차체의 제작도면(DXF), 절곡도, 모터 고정홀까지 설계할 수 있습니다.

![](chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/browser/images/acrobat_dc_20x20_dark.svg)PDF로 변환