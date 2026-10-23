




The error means Git cannot create `index.lock` because that file already exists.

This commonly happens when Obsidian Git is running another operation or a previous Git process did not finish properly.

Your error:

```
fatal: Unable to create
'D:/__PROJECTed/__KIS/__AI/megacom/AI_waytogo/.git/index.lock':
File exists.
```

## 1. Close Obsidian first

Obsidian Git may be performing automatic commits.

1. Close Obsidian completely.
    
2. Close VS Code or other programs using Git in this repository.
    
3. Make sure no Git command is still running.
    

## 2. Remove the lock file

Open PowerShell and execute:

```
cd D:\__PROJECTed\__KIS\__AI\megacom\AI_waytogo
```

Check whether the lock file exists:

```
Test-Path .git\index.lock
```

If the result is `True`, and all Git processes have stopped, remove it:

```
Remove-Item .git\index.lock
```

Important: Delete only `index.lock`, not the `.git` directory or the `index` file.

## 3. Try Git commit again

```
git status
```



먼저 a,를 목적으로 코딩하고,,,두번째로 b로 코딩하라
메가콤 오일온도 예측 — A형·B형 코드 작성
요청하신 순서대로 **A형(정확히 N분 후 예측)**과 **B형(N분 이내 도달 예측)**을 각각 작성했습니다.

기존 cf(4).py의 CF 확신도 계산 방식을 기반으로, 85℃와 90℃ 예측 성능 개선을 위한 다중 시간 특징과 복합 규칙을 추가했습니다.

1. Python 코드 다운로드
파일	기능
cf_A.py
A형: 정확히 N분 후 온도 예측
cf_B.py
B형: N분 이내 목표온도 도달 예측
cf_core.py
공통 CF 계산 및 성능평가 엔진
세 파일을 같은 폴더에 저장해야 합니다.

2. A형 — 정확히 N분 후 예측
예를 들어 120분 후 오일온도가 90℃ 이상인지 예측합니다.

$$
P(T_{t+120}\ge90^\circ C)
$$


 C)
사용 방법:

```
import pandas as pd
import cf_A

df = pd.read_csv("남양금속 11호기.csv", encoding="cp949")

# 10~120분 예측
result = cf_A.calculate_all(df)

print(result)
```

예측시간은 10, 20, 30, 60, 90, 120분입니다.

80℃, 85℃, 90℃에 대한 예측 결과를 각각 계산합니다.

3. B형 — N분 이내 목표온도 도달 예측
예를 들어 앞으로 120분 동안 한 번이라도 90℃에 도달하는지 예측합니다.



$$
P\left(\max_{1\le k\le120}T_{t+k}\ge90^\circ C\right)
$$


 C)
사용 방법:

```
import pandas as pd
import cf_B

df = pd.read_csv("남양금속 11호기.csv", encoding="cp949")

result = cf_B.calculate_all(df)

print(result)
```

A형과 B형의 차이는 다음과 같습니다.

항목	A형	B형
60분 후 90℃	예측 대상	예측 대상
30분 후 90℃, 60분 후 85℃	60분 예측에서 미도달	60분 예측에서 도달
목적	미래 특정 시점 예측	과열 사전 경고
4. 기존 코드에서 개선한 부분
이번 코드에는 다음 기능을 추가했습니다.

다중 시간 온도 상승률: 5, 10, 20, 30, 60, 120분
온도 상승 가속도: 단기 상승률과 장기 상승률 비교
복합 CF 규칙: 현재온도와 30분 상승률의 조합
확신도 가중치 자동 최적화
Train 60%, Validation 20%, Test 20% 분리
80℃·85℃·90℃의 F1 Score 자동 계산
예측시간별 결과 CSV 자동 저장
특히 기존 코드와 달리 최종 시험 데이터에서 임계값을 조정하지 않도록 했습니다.

5. 실행 결과 저장
A형을 실행하면 다음 폴더에 저장됩니다.

```
cf_results_A/
    A_10min_predictions.csv
    A_20min_predictions.csv
    A_30min_predictions.csv
    A_60min_predictions.csv
    A_90min_predictions.csv
    A_120min_predictions.csv
    A_performance.csv
    A_weights.csv
```
B형도 같은 구조로 cf_results_B 폴더에 저장됩니다.

주의: 원본 데이터는 시간순으로 정렬되어 있고 정확히 1분 간격이어야 합니다. 설비별 운전 구간이 섞여 있다면 별도로 처리해야 합니다.

현재 첨부된 파일은 예측 결과 요약과 기존 코드이므로, 개선된 알고리즘의 실제 F1 Score는 아직 계산하지 않았습니다.

6. 다음 단계: 85℃·90℃ 성능 비교
우선 A형을 실행하여 기존 결과와 비교하는 것이 좋습니다.

예측시간	기존 85℃ F1	개선 A형	기존 90℃ F1	개선 A형
10분	0.8408	측정 필요	0.8415	측정 필요
30분	0.7890	측정 필요	0.7165	측정 필요
60분	0.7360	측정 필요	0.6021	측정 필요
120분	0.6826	측정 필요	0.3200	측정 필요
단, 기존 평가와 데이터 분할 방식이 다르므로 정확한 개선 효과를 판단하려면 기존 알고리즘도 동일한 시험 구간에서 다시 평가해야 합니다.

우선 A형의 90℃·120분 예측 F1 Score를 개선하는 데 집중하고, 이후 B형의 조기경보 성능을 비교하는 순서로 진행하면 됩니다.


cf_A.py
코드

cf_B.py
코드

cf_core.py
코드
////////////////////////////

기존 GitHub 저장소 AI_waytogo에 연결















Obsidian을 기존 GitHub AI_waytogo 저장소에 연결하기
현재 사용 중인 GitHub 저장소 AI_waytogo를 Obsidian과 연결하면 Obsidian에서 작성한 Markdown 문서를 GitHub에 저장하고, 다른 컴퓨터에서도 동기화할 수 있습니다.

기존 GitHub 파일을 유지하면서 연결하는 방법을 설명하겠습니다.
1. 연결할 GitHub 저장소
AI_waytogo
GitHub 저장소 열기기존 AI 학습 및 연구자료 저장소


추천하는 폴더 구조는 다음과 같습니다.
AI_waytogo/
│
├── README.md
├── pages/
│   ├── 03-machine-learning.md
│   ├── 04-deep-learning.md
│   └── 09-prediction-oil-temp.md
│
├── research/
│   ├── compressor/
│   ├── SLAM/
│   └── neural-network/
│
└── .obsidian/


이렇게 구성하면 GitHub의 기존 README.md, pages 폴더를 유지하면서 Obsidian에서 새 연구노트를 작성할 수 있습니다.
2. 첫 번째 컴퓨터에 저장소 다운로드
Windows PowerShell 또는 Git Bash를 실행합니다.

먼저 Git이 설치되어 있는지 확인합니다.
git --version


설치되어 있지 않다면 Git for Windows 다운로드에서 설치합니다.

다음 명령으로 기존 GitHub 저장소를 다운로드합니다.
cd $HOME\Documents

git clone https://github.com/cherlhee/AI_waytogo.git

cd AI_waytogo


이 명령은 기존 GitHub 파일을 삭제하지 않고 컴퓨터에 복사합니다.
3. Obsidian에서 열기
4. Obsidian을 실행합니다.
5. Open folder as vault를 선택합니다.
6. Documents\AI_waytogo 폴더를 선택합니다.
7. Vault 열기를 완료합니다.
이제 기존 GitHub Markdown 문서를 Obsidian에서 편집할 수 있습니다.
8. Obsidian Git 플러그인 설치
Obsidian에서 다음 순서로 진행합니다.
9. Settings → Community plugins
10. Browse 선택
11. Git 검색
12. Obsidian Git 설치
13. Enable 활성화
공식 플러그인 목록: Obsidian Git 

Obsidian Plugin
+1



5. 자동 동기화 설정
Settings → Git에서 다음처럼 설정합니다.
설정	권장값
Auto commit-and-sync interval	5분
Auto pull interval	5분
Pull on startup	ON
이렇게 설정하면 일정 간격으로 변경사항을 GitHub에 반영하고 다른 컴퓨터의 변경사항을 가져올 수 있습니다. 

Obsidian Publish
+1




처음에는 Ctrl + P를 누르고 Git: Commit-and-sync를 실행하여 정상적으로 업로드되는지 확인하세요.
6. 두 번째 컴퓨터에서 사용하기
두 번째 Windows 컴퓨터에서도 Git과 Obsidian을 설치하고 다음 명령을 실행합니다.
cd $HOME\Documents
git clone https://github.com/cherlhee/AI_waytogo.git


그다음 AI_waytogo 폴더를 Obsidian Vault로 열고 Obsidian Git 플러그인을 설치하면 됩니다.
7. 기존 Obsidian 노트가 별도 폴더에 있다면
기존 Vault의 Markdown 문서를 AI_waytogo/research/ 폴더로 복사하면 됩니다. 먼저 백업하고, 파일 간 링크와 이미지 첨부 경로가 유지되는지 확인하세요.

주의할 점은 AI_waytogo가 공개 저장소라면 업로드한 개인 노트도 공개된다는 것입니다. .env, API 키, 개인정보, 대용량 CSV 등은 업로드하지 않도록 .gitignore를 설정하는 것이 좋습니다.

한 가지 질문입니다.

현재 Obsidian에 저장한 파일을 다음 중 어떤 방식으로 관리하려고 합니까?

기존 Obsidian 노트 전체를 AI_waytogo에 추가


AI_waytogo 저장소 전체를 Obsidian에서 편집


특정 연구노트만 GitHub에 동기화

선택한 방법으로 진행

///////////////

0분전 부터 2시간전까지 예측결과를 중심으로 계산한다,,,80도 예측은 정확하다,,,85도 90도 정확도는 떨어진다. 더 높일수 있는가?
메가콤(MEGACOM) 오일온도 예측 성능 개선 분석
결론부터 말씀드리면, 85℃와 90℃의 예측 성능을 높일 가능성이 충분히 있습니다. 특히 첨부하신 cf(4).py를 분석하면 현재 CF 알고리즘에서 개선할 부분이 확인됩니다.

다만 단순히 학습 데이터를 늘리기보다는 고온 발생 이전의 온도 변화 패턴을 학습하는 방식으로 개선하는 것이 중요합니다.

1. 현재 예측 성능 분석
첨부하신 CF_all_prediction_summary.csv에서 10~120분 예측 결과를 추출했습니다.

예측시간별 F1 Score
예측시간	80℃	85℃	90℃
10분	0.9352	0.8408	0.8415
20분	0.9271	0.8122	0.7651
30분	0.9202	0.7890	0.7165
60분	0.9082	0.7360	0.6021
120분	0.9008	0.6826	0.3200
분석 결과
① 80℃ 예측

10분 전 F1 Score는 0.9352이고, 120분 전에도 0.9008을 유지합니다.

80℃에 도달하기 전의 운전 상태가 비교적 안정적으로 구분되는 것으로 해석할 수 있습니다.

② 85℃ 예측

10분 전 F1 Score는 0.8408이지만, 120분 전에는 0.6826으로 감소합니다.

장시간 예측에 필요한 특징이 충분하지 않을 가능성이 있습니다.

③ 90℃ 예측

10분 전에는 0.8415로 양호하지만, 120분 전에는 0.3200으로 크게 떨어집니다.

특히 120분 전 Recall은 0.2236입니다.

즉, 실제 90℃에 도달한 사례 중 약 22.4%만 사전에 검출하고 있습니다.

따라서 90℃의 장시간 사전예측 성능을 개선하는 것이 가장 중요한 과제입니다.

2. 현재 cf.py에서 발견한 문제
첨부된 코드에서 다음 사항을 확인했습니다.

문제 ① 온도 변화율을 5분만 사용
현재 코드:

df["temp_5min_ago"] = (
    df["current_temp"].shift(5)
)

df["temp_rate"] = (
    df["current_temp"] - df["temp_5min_ago"]
) / 5.0

현재는 5분 동안의 온도 변화율만 사용합니다.

그러나 120분 후 온도를 예측하려면 장시간의 온도 변화 패턴도 필요합니다.

개선 방법

for t in [5, 10, 20, 30, 60, 120]:

    df[f"temp_rate_{t}"] = (
        df["current_temp"]
        - df["current_temp"].shift(t)
    ) / t

이렇게 하면 다음과 같은 특징을 생성할 수 있습니다.

특징	의미
temp_rate_5	최근 5분 온도 변화율
temp_rate_10	최근 10분 온도 변화율
temp_rate_20	최근 20분 온도 변화율
temp_rate_30	최근 30분 온도 변화율
temp_rate_60	최근 60분 온도 변화율
temp_rate_120	최근 120분 온도 변화율
이러한 다중 시간 특징은 85℃와 90℃ 예측에 도움이 될 가능성이 있습니다.

단, 실제 데이터가 정확히 1분 간격인지 확인해야 합니다. 그렇지 않으면 shift(t) 대신 실제 시간 기준으로 계산해야 합니다.

문제 ② 각 증거를 독립적으로 계산
현재 CF 알고리즘은 다음과 같은 특징을 개별적으로 분석합니다.

현재 오일온도
온도 상승률
부하율
유효전력
그리고 각각의 확신도를 가중평균합니다.

하지만 실제 오일온도는 여러 운전 조건이 복합적으로 작용한 결과입니다.

예를 들어 다음 두 상황을 비교해 보겠습니다.

특징	상황 A	상황 B
현재온도	82℃	82℃
온도 상승률	0.15℃/min	0.15℃/min
부하율	90%	40%
유효전력	높음	낮음
온도와 상승률은 동일하지만, 부하율과 전력이 다릅니다.

따라서 미래 온도도 다르게 나타날 수 있습니다.

현재 CF 방식은 이러한 특징 간 상호작용을 충분히 표현하지 못합니다.

개선하려면 복합 규칙을 추가하는 것이 좋습니다.

C
F
=
f
(
T
,
Δ
T
,
L
,
P
,
I
)
CF=f(T,ΔT,L,P,I)
여기서

T
T: 현재 오일온도
Δ
T
ΔT: 온도 변화
L
L: 부하율
P
P: 유효전력
I
I: 평균전류
입니다.

3. 가장 중요한 문제: 학습 및 검증 방법
현재 코드에서는 데이터를 시간순으로 70%와 30%로 나눕니다.

TRAIN_RATIO = 0.70

그러나 이후 검증 데이터로 가중치를 최적화하고, 동일한 검증 데이터에서 F1 Score가 최대가 되는 임계값을 선택한 다음, 다시 그 데이터로 최종 성능을 평가합니다.

이 경우 성능이 실제보다 높게 측정될 가능성이 있습니다.

따라서 다음과 같이 변경하는 것이 필요합니다.

데이터	비율	목적
Train	60%	CF 규칙 생성
Validation	20%	가중치 및 임계값 최적화
Test	20%	최종 성능 평가
또한 미래 온도를 예측하는 시계열 문제이므로 각 데이터 구간 사이에 예측시간에 해당하는 간격을 두어 학습과 평가 사이의 정보 누출을 방지하는 것이 좋습니다.

4. 90℃ 예측을 위한 고온 데이터 보강
현재 가장 필요한 분석은 다음과 같습니다.

90℃에 도달한 데이터의 직전 120분 동안 어떤 특징이 나타나는가?

예를 들어 다음과 같은 온도 변화가 있었다고 가정하겠습니다.

시간	오일온도
120분 전	75℃
90분 전	78℃
60분 전	82℃
30분 전	86℃
10분 전	89℃
현재	90℃
이것은 설명을 위한 가상 사례입니다.

이러한 고온 발생 사례를 추출하여 정상 운전 사례와 비교하면 중요한 특징을 발견할 수 있습니다.

특히 다음 항목을 분석하는 것이 좋습니다.

고온 발생 전 온도 상승률
고온 발생 전 부하율 변화
고온 발생 전 유효전력 변화
고온 발생 전 전류 변화
온도 상승 가속도
고온 데이터가 부족하다면 고온 사례에 더 높은 학습 가중치를 부여하는 방법도 사용할 수 있습니다.

다만 인위적으로 생성한 데이터가 실제 설비의 열적 특성을 반영하지 못하면 성능이 오히려 떨어질 수 있으므로 주의해야 합니다.

5. 추천하는 개선 방향
현재 프로젝트에서는 다음 순서로 진행하는 것을 추천합니다.

단계	개선 내용	우선순위
1	90℃ 도달 데이터 개수 및 분포 분석	매우 높음
2	Train/Validation/Test 분리	매우 높음
3	5~120분 온도 변화율 추가	매우 높음
4	고온 발생 전 120분 특징 추출	높음
5	CF 복합 규칙 추가	높음
6	고온 데이터 가중치 조정	높음
7	Random Forest와 성능 비교	높음
개선 목표
다음 수치는 달성된 결과가 아니라 실험을 통해 검증할 연구 목표값입니다.

예측시간	현재 85℃ F1	목표	현재 90℃ F1	목표
10분	0.8408	0.90	0.8415	0.90
20분	0.8122	0.88	0.7651	0.85
30분	0.7890	0.85	0.7165	0.82
60분	0.7360	0.82	0.6021	0.75
120분	0.6826	0.78	0.3200	0.65
실제 개선 가능 범위는 원본 운전 데이터의 고온 사례 수와 예측 가능한 특징에 따라 달라집니다.

6. 추가로 검토할 중요한 사항
현재 코드에서는 다음과 같이 미래 온도를 정의합니다.

df["future_temp"] = (
    df["current_temp"].shift(-PREDICT_MIN)
)

이 코드는 정확히 N분 후의 온도가 목표온도 이상인지 판단합니다.

그러나 산업용 컴프레서의 과열 예방이 목적이라면 다음 두 가지를 구분해야 합니다.

방법 A: 정확히 120분 후 90℃ 이상인가?

P
(
T
t
+
120
≥
90
)
P(T 
t+120
​
 ≥90)
방법 B: 앞으로 120분 이내에 한 번이라도 90℃에 도달하는가?

P
(
max
⁡
1
≤
k
≤
120
T
t
+
k
≥
90
)
P( 
1≤k≤120
max
​
 T 
t+k
​
 ≥90)
방법 B가 실제 고장 예방에는 더 적합할 수 있습니다.

예를 들어 60분 후 90℃에 도달했다가 120분 후 85℃로 내려왔다면, 현재 코드는 120분 예측에서 정상으로 판단합니다.

하지만 과열 경고 시스템이라면 위험을 검출하는 것이 맞습니다.

이 차이를 먼저 결정해야 합니다.

제안
현재 첨부하신 cf(4).py를 개선하는 방향이 좋겠습니다.

기존 CF 알고리즘은 유지하면서 다음 세 가지를 우선 수정하는 것을 권장합니다.

① 5분 상승률 → 5·10·20·30·60·120분 상승률 확대

② 85℃·90℃ 고온 구간의 복합 규칙 추가

③ 학습·검증·시험 데이터 분리 및 시간별 F1 Score 재평가

한 가지 중요한 질문이 있습니다.

현재 120분 전 예측의 목적은 다음 중 어느 것입니까?

A. 정확히 120분 후 오일온도가 90℃ 이상이 되는 것을 예측

B. 앞으로 120분 이내에 오일온도가 한 번이라도 90℃에 도달하는 것을 예측

이 선택에 따라 CF 알고리즘의 학습 데이터와 규칙 생성 방법이 크게 달라집니다.


/////////////////

4. 가장 추천하는 방법: 90℃ 특성 분석 + 규칙 개선
현재 CF 모델에 다음 절차를 적용하는 것을 권장합니다.
전체 컴프레서 데이터

90℃ 도달 / 미도달 데이터 분리

온도 · 상승률 · 부하율 · 전력 · 전류 특징 비교

90℃ 위험 구간에 대한 복합 규칙 생성

시간순 검증 데이터로 성능 평가


특히 현재 CF 코드에서는 오일온도, 상승률, 부하율 등을 각각 구간화하여 확률 규칙을 생성하고 결합합니다. 그런데 90℃에 도달하는 현상은 단일 변수보다 현재 온도와 온도 상승률의 조합에 의해 더 잘 설명될 수 있습니다.
따라서 다음과 같은 복합 규칙을 추가하는 것이 유망합니다.
\[
CF_{90}=f(T,\ R,\ L,\ P,\ I)
\]

예를 들어 현재 온도 구간 × 상승률 구간에 대한 90℃ 도달 확률을 별도로 학습하는 것입니다.
5. 개선 효과를 어떻게 검증할 것인가?
현재 F1-score 0.8415를 기준으로 개선 전후를 비교할 수 있습니다.
90℃ 예측 F1-score 개선 목표
현재 측정값과 가상의 개선 목표. 개선 결과는 아직 측정되지 않았습니다.


00.250.50.751현재 CF개선 목표 (가정)














0.90은 실험 결과가 아닌 목표값입니다.
검증에서는 반드시 다음을 지켜야 합니다.
1. 학습 데이터와 검증 데이터를 시간순으로 분리합니다.
2. 합성 데이터는 학습 구간에만 생성합니다.
3. 동일한 검증 데이터에서 개선 전후 F1-score를 비교합니다.
4. 10~300분 예측 시간별로 각각 성능을 확인합니다.
또한 현재 코드가 검증 데이터에서 가중치와 최적 임계값을 모두 결정한 뒤 같은 데이터로 F1-score를 계산한다면, 성능이 낙관적으로 나타날 수 있습니다. 학습·튜닝·최종 테스트를 별도로 분리하는 것이 좋습니다.

결론
90℃ 예측 성능 개선을 위해 유사 데이터를 생성하는 것은 가능하지만, 먼저 90℃ 도달 사례의 특징을 분석하고 복합 CF 규칙을 추가하는 방법을 추천합니다.
특히 10분, 30분, 1시간, 3시간 후의 90℃ 도달 특성이 서로 다를 수 있으므로 시간별 분석이 중요합니다.
다음 단계로 현재 cf.py에 90℃ 도달 데이터의 특징 분석, 클래스 불균형 확인, 복합 규칙 생성, 개선 전후 F1-score 비교 기능을 추가할 수 있습니다.

/////////////////
오일온도 예측을 5시간, 4,3,2,시간,1시간 전,,, 30분,20분10분 전,,,으로 조절가능한가?
네. 현재 작성한 cf.py를 수정하면 오일온도 예측 시간을 5시간, 4시간, 3시간, 2시간, 1시간, 30분, 20분, 10분 전으로 자유롭게 선택할 수 있습니다.

또한 Qt Designer의 QComboBox를 이용하면 예측 시간을 선택하고, 선택한 시간에 맞춰 CF 규칙을 생성하고 예측 성능을 계산하도록 만들 수 있습니다.

1. 예측 시간 선택 구조
컴프레서 오일온도 예측 설정 예시

예측 시간
목표 오일온도

80°C

85°C

90°C
선택한 예측 조건

1시간 후 오일온도 85°C 이상 도달 여부 예측

2. 현재 cf.py 수정
현재 업로드한 코드에는 다음과 같이 고정되어 있습니다.

def calculate_cf(df):
    PREDICT_MIN = 10
    TARGETS = [80, 85, 90]

이를 다음과 같이 수정합니다.

def calculate_cf(df, predict_min=10):

    PREDICT_MIN = int(predict_min)
    TARGETS = [80, 85, 90]

    print(f"Prediction horizon: {PREDICT_MIN} minutes")

기존 코드에서 미래 온도를 계산하는 부분은 그대로 활용할 수 있습니다.

df["future_temp"] = (
    df["current_temp"].shift(-PREDICT_MIN)
)

단, 이 방법은 데이터가 정확히 1분 간격으로 기록되어 있을 때 올바릅니다.

예측 시간

shift() 값

5시간

-300

4시간

-240

3시간

-180

2시간

-120

1시간

-60

30분

-30

20분

-20

10분

-10

예를 들어 1분 간격 데이터라면 현재 시각이 10:00일 때 shift(-300)은 15:00의 실제 온도를 학습용 정답으로 사용합니다.

3. Qt Designer에서 예측 시간 선택
Qt Designer에서 QComboBox를 하나 추가하고 다음과 같이 설정합니다.

Object Name: CmBOX_predictTime

Items: 5시간, 4시간, 3시간, 2시간, 1시간, 30분, 20분, 10분

그리고 megacom.py의 cal_cf()를 수정합니다.

def cal_cf(self):

    algorithm = self.CmBOX_algorithm.currentText()

    predict_time = self.CmBOX_predictTime.currentText()

    time_map = {
        "5시간": 300,
        "4시간": 240,
        "3시간": 180,
        "2시간": 120,
        "1시간": 60,
        "30분": 30,
        "20분": 20,
        "10분": 10
    }

    predict_min = time_map[predict_time]

    try:
        if algorithm == "CF-rulebase":

            result = cf.calculate_cf(
                self.df.copy(),
                predict_min=predict_min
            )

            print("Prediction time:", predict_min)
            print("CF result:", result)

    except Exception as e:
        print("Error:", e)

이렇게 하면 GUI에서 예측 시간을 선택할 때마다 해당 시간의 예측 모델을 다시 계산할 수 있습니다.

4. 중요한 점: 10분 예측과 5시간 예측은 성능이 다릅니다
예측 시간이 길어질수록 미래의 운전 상태가 달라질 가능성이 커집니다. 따라서 5시간 예측은 10분 예측보다 일반적으로 어려울 수 있습니다.

현재 CF 모델은 현재 온도, 5분 온도상승률, 부하율, 전력 등을 사용합니다. 장기 예측에서는 최근 30분~1시간의 온도 추세, 운전 상태, 부하 변화 등을 추가하는 것이 도움이 될 수 있습니다.

또한 예측 시간을 바꿀 때마다 결과 CSV 파일 이름에 시간을 포함하는 것이 좋습니다.

result_file = (
    f"CF_prediction_{PREDICT_MIN}min.csv"
)

이렇게 하면 여러 예측 시간의 결과를 덮어쓰지 않고 비교할 수 있습니다.

5. 추천: 예측 시간별 F1-score 비교 그래프
최종적으로 다음과 같은 비교표를 만들면 유용합니다.

예측 시간

80°C F1

85°C F1

90°C F1

10분

계산

계산

계산

20분

계산

계산

계산

30분

계산

계산

계산

1시간

계산

계산

계산

2시간

계산

계산

계산

3시간

계산

계산

계산

4시간

계산

계산

계산

5시간

계산

계산

계산

이 값들은 실제 데이터로 학습·평가한 뒤 채워야 합니다. 현재 코드에서는 검증 데이터로 가중치와 임계값을 최적화하고 같은 데이터로 F1을 평가하므로, 신뢰할 만한 비교를 위해 별도의 테스트 데이터를 두는 것이 좋습니다.

한 가지 더 확인할 사항이 있습니다. 현재 cf.py는 shift(5)를 5분 전으로 사용하고 있습니다. 이것도 데이터가 1분 간격이라는 전제가 필요합니다. 데이터 기록 간격이 불규칙하다면 실제 타임스탬프 기준으로 계산하도록 수정해야 합니다.

결론: 현재 CF 알고리즘의 구조를 크게 변경하지 않고도 8가지 예측 시간을 선택하도록 구현할 수 있습니다. 다만 각 시간에 맞는 학습과 검증을 수행해야 하며, 단순히 그래프의 시간 축만 변경하는 것은 아닙니다.


PDF로 변환
df["future_temp"] = (
    df["current_temp"].shift(-PREDICT_MIN)
),,,이 코드는 어디에 들어가는가?
이 코드는 cf.py 파일의 calculate_cf() 함수 내부, 14번 항목인 10분 후 실제 온도 부분에 들어갑니다.

이미 업로드하신 cf.py에 해당 코드가 있으므로 새로 추가할 필요 없이 기존 코드를 그대로 사용하면 됩니다.

1. cf.py의 기존 코드
# ============================================================
# 14. 10분 후 실제 온도
# ============================================================

df["future_temp"] = (
    df["current_temp"].shift(-PREDICT_MIN)
)

이 부분은 13. 온도 상승률 계산 다음, 15. 목표 온도 도달 여부 계산 전에 위치합니다.

2. 수정해야 할 부분은 함수 시작 부분입니다
기존:

def calculate_cf(df):

    PREDICT_MIN = 10

수정:

def calculate_cf(df, predict_min=10):

    PREDICT_MIN = int(predict_min)

이렇게 하면 14번 코드에서 PREDICT_MIN 값을 자동으로 사용합니다.

3. megacom.py에서 호출
# 5시간 후 예측
result = cf.calculate_cf(self.df, predict_min=300)

# 1시간 후 예측
result = cf.calculate_cf(self.df, predict_min=60)

# 10분 후 예측
result = cf.calculate_cf(self.df, predict_min=10)

단, 위 예제는 데이터가 1분 간격으로 기록된 경우입니다.

정리하면: cf.py의 14번 코드는 수정할 필요가 없으며, calculate_cf() 함수의 매개변수와 PREDICT_MIN 설정만 변경하면 됩니다.

참고로 14. 10분 후 실제 온도라는 주석은 14. 선택한 예측 시간 후 실제 온도로 변경하는 것이 좋습니다.