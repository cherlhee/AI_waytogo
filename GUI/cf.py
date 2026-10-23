


# ============================================================
# cf.py
#
# 확신도 기반 산업용 컴프레서 오일온도 예측
#
# 목표:
#   현재 시점에서 10분 후
#   오일온도가 80 / 85 / 90℃ 이상이 되는 확률 계산
#
# 입력:
#   현재 오일온도
#   5분 온도상승률
#   부하율
#   유효전력
#   평균전류
#
# 사용하지 않음:
#   상세고장항목
#
# 자동 계산:
#   조건별 확률
#   증거별 확신도
#   증거 가중치
#   최적 확신도 임계값
#   예측 성능
#
# ============================================================


import os
import warnings
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    brier_score_loss
)
warnings.filterwarnings("ignore")
# ----------------------------------------------------------





# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
def calculate_cf(df, predict_min=10):
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    
    print("hello, calculate at cf.py")
    result = 1121

    print(df.head()) 


    # ============================================================
    # 0. 사용자 설정
    # ============================================================

    # FILE = r"남양금속 11호기.csv"

    # 예측 시간
    # PREDICT_MIN = 10
    PREDICT_MIN = int(predict_min)
    print(f"Prediction horizon: {PREDICT_MIN} minutes")


    # 목표 온도
    TARGETS = [80, 85, 90]

    # 시간 순서 기반 학습 / 검증 분할
    TRAIN_RATIO = 0.70

    # 규칙 생성 최소 데이터 수
    MIN_COUNT = 20




    # ============================================================
    # 2. 컬럼 검색
    # ============================================================

    def normalize_column_name(name):

        return (
            str(name)
            .replace(" ", "")
            .replace("\n", "")
            .replace("\r", "")
            .replace("_", "")
            .replace("-", "")
            .lower()
        )


    def find_column(columns, keywords):

        normalized_columns = {}

        for col in columns:

            normalized_columns[col] = (
                normalize_column_name(col)
            )

        for keyword in keywords:

            key = normalize_column_name(
                keyword
            )

            for col, normalized in normalized_columns.items():

                if key in normalized:

                    return col

        return None





    # ============================================================
    # 3. 시작
    # ============================================================

    print()
    print("@" * 80)
    print("컴프레서 확신도 기반 오일온도 예측")
    print("@" * 80)
    print()



    # ============================================================
    # 4. CSV 읽기
    # ============================================================

    print("[1] CSV loading...")

    #df = read_csv_auto(FILE)

    print(
        f"데이터 크기 : {df.shape[0]:,} rows, "
        f"{df.shape[1]:,} columns"
    )



    # ============================================================
    # 5. 컬럼 자동 검색
    # ============================================================

    print()
    print("[2] 컬럼 검색...")


    temp_col = find_column(
        df.columns,
        [
            "오일온도",
            "oiltemperature",
            "oiltemp"
        ]
    )


    load_col = find_column(
        df.columns,
        [
            "부하율",
            "load율",
            "load"
        ]
    )


    power_col = find_column(
        df.columns,
        [
            "유효전력",
            "유효 전력",
            "전력",
            "power"
        ]
    )





    # ============================================================
    # 6. 전류 컬럼 자동 검색
    # ============================================================

    current_cols = []

    for col in df.columns:

        normalized = normalize_column_name(col)

        if "전류" in normalized:

            current_cols.append(col)


    print()
    print("자동 검색 결과")
    print("-" * 80)

    print(
        "오일온도 :",
        temp_col
    )

    print(
        "부하율   :",
        load_col
    )

    print(
        "전력     :",
        power_col
    )

    print(
        "전류     :",
        current_cols
    )


    if temp_col is None:

        raise ValueError(
            "오일온도 컬럼을 찾을 수 없습니다."
        )




    # ============================================================
    # 7. 숫자형 변환
    # ============================================================

    print()
    print("[3] 숫자 데이터 변환...")


    numeric_cols = [
        temp_col
    ]


    if load_col is not None:

        numeric_cols.append(
            load_col
        )


    if power_col is not None:

        numeric_cols.append(
            power_col
        )


    numeric_cols += current_cols


    numeric_cols = list(
        dict.fromkeys(numeric_cols)
    )


    for col in numeric_cols:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )






    # ============================================================
    # 8. 평균 전류
    # ============================================================

    if len(current_cols) > 0:

        df["current_mean"] = (
            df[current_cols]
            .mean(axis=1)
        )

    else:

        df["current_mean"] = np.nan


    # ============================================================
    # 9. 시간 순서
    # ============================================================

    df = df.reset_index(drop=True)


    # ============================================================
    # 10. 현재 오일온도
    # ============================================================

    df["current_temp"] = (
        df[temp_col]
    )


    # ============================================================
    # 11. 5분 전 온도
    # ============================================================

    df["temp_5min_ago"] = (
        df["current_temp"]
        .shift(5)
    )


    # ============================================================
    # 12. 온도 변화량
    # ============================================================

    df["temp_change_5min"] = (
        df["current_temp"]
        -
        df["temp_5min_ago"]
    )


    # ============================================================
    # 13. 온도 상승률
    #
    # 단위:
    # ℃ / min
    # ============================================================

    df["temp_rate"] = (
        df["temp_change_5min"]
        / 5.0
    )


    # ============================================================
    # 14. 10분 후 실제 온도
    # ============================================================

    df["future_temp"] = (
        df["current_temp"].shift(-PREDICT_MIN)
    )


    # ============================================================
    # 15. 80 / 85 / 90℃ 실제 도달 여부
    # ============================================================

    for target in TARGETS:

        df[f"actual_{target}"] = (
            df["future_temp"] >= target
        ).astype(int)




    # ============================================================
    # 16. 사용할 입력 증거
    # ============================================================

    FEATURES = [
        "current_temp",
        "temp_rate"
    ]


    if load_col is not None:

        FEATURES.append(
            load_col
        )


    if power_col is not None:

        FEATURES.append(
            power_col
        )


    if len(current_cols) > 0:

        FEATURES.append(
            "current_mean"
        )


    print()
    print("[4] 사용할 증거")
    print("-" * 80)

    for feature in FEATURES:

        print(
            " -",
            feature
        )



    # ============================================================
    # 17. 분석 데이터 생성
    # ============================================================

    data = df.dropna(
        subset=FEATURES + [
            "future_temp"
        ]
    ).copy()


    data = data.reset_index(
        drop=True
    )


    print()
    print("분석 가능 데이터 :", f"{len(data):,}")


    if len(data) < 100:

        raise ValueError("분석 데이터가 너무 적습니다.")




    # ============================================================
    # 18. 시간순 Train / Validation 분리
    # ============================================================

    split_index = int(len(data) * TRAIN_RATIO)

    train = data.iloc[:split_index].copy()

    valid = data.iloc[split_index:].copy()

    train = train.reset_index(drop=True)

    valid = valid.reset_index(drop=True)


    print()
    print("[5] Train / Validation")
    print("-" * 80)

    print(f"Train : {len(train):,}")

    print(f"Valid : {len(valid):,}")


    # ============================================================
    # 19. 구간 정의
    # ============================================================

    # ------------------------------------------------------------
    # 현재 오일온도
    # ------------------------------------------------------------

    TEMP_BINS = [
        -np.inf,
        60,
        65,
        70,
        72,
        74,
        76,
        78,
        80,
        82,
        84,
        86,
        88,
        90,
        92,
        95,
        100,
        np.inf
    ]


    # ------------------------------------------------------------
    # 온도 상승률
    # ------------------------------------------------------------

    RATE_BINS = [
        -np.inf,
        -1.0,
        -0.5,
        -0.2,
        0.0,
        0.2,
        0.4,
        0.6,
        0.8,
        1.0,
        1.5,
        2.0,
        np.inf
    ]


    # ------------------------------------------------------------
    # 부하율
    # ------------------------------------------------------------

    LOAD_BINS = [
        -np.inf,
        20,
        40,
        60,
        70,
        80,
        90,
        100,
        np.inf
    ]




    # ============================================================
    # 20. Train / Valid 구간 생성
    # ============================================================

    train["temp_bin"] = pd.cut(train["current_temp"], bins=TEMP_BINS, right=False)

    valid["temp_bin"] = pd.cut(
        valid["current_temp"],
        bins=TEMP_BINS,
        right=False
    )


    train["rate_bin"] = pd.cut(
        train["temp_rate"],
        bins=RATE_BINS,
        right=False
    )

    valid["rate_bin"] = pd.cut(
        valid["temp_rate"],
        bins=RATE_BINS,
        right=False
    )


    if load_col is not None:

        train["load_bin"] = pd.cut(
            train[load_col],
            bins=LOAD_BINS,
            right=False
        )

        valid["load_bin"] = pd.cut(
            valid[load_col],
            bins=LOAD_BINS,
            right=False
        )



    # ============================================================
    # 21. 전력 구간 자동 생성
    # ============================================================

    if power_col is not None:

        power_values = (
            train[power_col]
            .dropna()
            .values
        )


        if len(power_values) > 0:

            power_quantiles = np.nanquantile(
                power_values,
                [
                    0.00,
                    0.10,
                    0.25,
                    0.50,
                    0.75,
                    0.90,
                    1.00
                ]
            )


            power_quantiles = np.unique(
                power_quantiles
            )


            if len(power_quantiles) >= 3:

                train["power_bin"] = pd.cut(
                    train[power_col],
                    bins=power_quantiles,
                    include_lowest=True,
                    duplicates="drop"
                )

                valid["power_bin"] = pd.cut(
                    valid[power_col],
                    bins=power_quantiles,
                    include_lowest=True,
                    duplicates="drop"
                )


    # ============================================================
    # 22. 확률 규칙 생성
    # ============================================================

    def make_probability_rule(
        source_df,
        bin_col,
        target_col
    ):

        grouped = (
            source_df
            .groupby(
                bin_col,
                observed=True
            )[target_col]
            .agg(
                count="count",
                probability="mean"
            )
            .reset_index()
        )


        grouped = grouped[
            grouped["count"] >= MIN_COUNT
        ].copy()


        grouped["probability"] = (
            pd.to_numeric(
                grouped["probability"],
                errors="coerce"
            )
        )


        return grouped





    # ============================================================
    # 23. 목표온도별 규칙 생성
    # ============================================================

    rules = {}


    print()
    print("[6] 데이터 기반 확률 규칙 생성")
    print("=" * 80)


    for target in TARGETS:

        print()
        print(
            f"{target}℃ 규칙"
        )


        rules[target] = {}

        actual_col = (
            f"actual_{target}"
        )


        # 현재 온도
        rules[target]["temp"] = (
            make_probability_rule(
                train,
                "temp_bin",
                actual_col
            )
        )


        # 상승률
        rules[target]["rate"] = (
            make_probability_rule(
                train,
                "rate_bin",
                actual_col
            )
        )


        # 부하율
        if load_col is not None:

            rules[target]["load"] = (
                make_probability_rule(
                    train,
                    "load_bin",
                    actual_col
                )
            )


        # 전력
        if (
            power_col is not None
            and "power_bin" in train.columns
        ):

            rules[target]["power"] = (
                make_probability_rule(
                    train,
                    "power_bin",
                    actual_col
                )
            )


        for name, rule in rules[target].items():

            print(
                f"  {name:8s}: "
                f"{len(rule):3d} rules"
            )




    # ============================================================
    # 24. 규칙 적용
    # ============================================================

    def apply_rule(
        source_df,
        rule,
        bin_col
    ):

        if rule.empty:

            return pd.Series(
                np.nan,
                index=source_df.index,
                dtype=float
            )


        lookup = (
            rule
            .set_index(bin_col)["probability"]
        )


        result = (
            source_df[bin_col]
            .map(lookup)
        )


        # 반드시 float으로 변환
        result = pd.to_numeric(
            result,
            errors="coerce"
        )


        return result.astype(float)


    # ============================================================
    # 25. 증거별 확신도 생성
    # ============================================================

    EVIDENCE_NAMES = [
        "temp",
        "rate"
    ]


    if load_col is not None:

        EVIDENCE_NAMES.append(
            "load"
        )


    if (
        power_col is not None
        and "power_bin" in train.columns
    ):

        EVIDENCE_NAMES.append(
            "power"
        )


    print()
    print("[7] 증거별 확신도 계산")
    print("-" * 80)

    print(
        "사용 증거:",
        EVIDENCE_NAMES
    )


    for target in TARGETS:

        print(
            f"{target}℃ evidence calculation..."
        )


        for name in EVIDENCE_NAMES:

            rule = (
                rules[target][name]
            )


            if name == "temp":

                bin_col = "temp_bin"

            elif name == "rate":

                bin_col = "rate_bin"

            elif name == "load":

                bin_col = "load_bin"

            elif name == "power":

                bin_col = "power_bin"

            else:

                continue


            train[
                f"cf_{target}_{name}"
            ] = apply_rule(
                train,
                rule,
                bin_col
            )


            valid[
                f"cf_{target}_{name}"
            ] = apply_rule(
                valid,
                rule,
                bin_col
            )





    # ============================================================
    # 26. 확신도 결합
    # ============================================================

    def weighted_confidence(
        source_df,
        target,
        weights
    ):

        weighted_sum = np.zeros(
            len(source_df),
            dtype=float
        )

        weight_sum = np.zeros(
            len(source_df),
            dtype=float
        )


        for i, name in enumerate(
            EVIDENCE_NAMES
        ):

            col = (
                f"cf_{target}_{name}"
            )


            if col not in source_df.columns:

                continue


            # 중요:
            # Categorical 문제를 피하기 위해
            # 무조건 숫자 배열로 변환
            values = pd.to_numeric(
                source_df[col],
                errors="coerce"
            ).to_numpy(
                dtype=float
            )


            valid_mask = np.isfinite(
                values
            )


            weighted_sum[valid_mask] += (
                values[valid_mask]
                *
                weights[i]
            )


            weight_sum[valid_mask] += (
                weights[i]
            )


        confidence = np.full(
            len(source_df),
            np.nan,
            dtype=float
        )


        valid_total = (
            weight_sum > 0
        )


        confidence[valid_total] = (
            weighted_sum[valid_total]
            /
            weight_sum[valid_total]
        )


        # 확률 범위 강제
        confidence = np.clip(
            confidence,
            0.0,
            1.0
        )


        return confidence



    # ============================================================
    # 27. 가중치 자동 최적화
    #
    # Brier Score 최소화
    #
    # Brier Score:
    #
    #   (예측확률 - 실제결과)^2
    #
    # 작을수록 좋음
    # ============================================================

    optimized_weights = {}


    print()
    print("=" * 80)
    print("[8] 증거 가중치 자동 최적화")
    print("=" * 80)


    for target in TARGETS:

        print()
        print(
            f"{target}℃ 가중치 최적화"
        )


        y_true = (
            valid[
                f"actual_{target}"
            ]
            .to_numpy(
                dtype=float
            )
        )


        n_evidence = (
            len(EVIDENCE_NAMES)
        )


        def objective(weights):

            weights = np.asarray(
                weights,
                dtype=float
            )


            weights = np.maximum(
                weights,
                0
            )


            total = weights.sum()


            if total <= 0:

                return 1.0


            weights = (
                weights / total
            )


            confidence = (
                weighted_confidence(
                    valid,
                    target,
                    weights
                )
            )


            mask = np.isfinite(
                confidence
            )


            if mask.sum() == 0:

                return 1.0


            score = brier_score_loss(
                y_true[mask],
                confidence[mask]
            )


            return score


        initial = (
            np.ones(
                n_evidence,
                dtype=float
            )
            /
            n_evidence
        )


        constraints = {
            "type": "eq",
            "fun": lambda w:
                np.sum(w) - 1.0
        }


        bounds = [
            (0.0, 1.0)
            for _ in range(
                n_evidence
            )
        ]


        result = minimize(
            objective,
            initial,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={
                "maxiter": 300,
                "ftol": 1e-9
            }
        )


        if result.success:

            weights = result.x

        else:

            print(
                "  [WARN] 최적화 실패"
            )

            print(
                "  message:",
                result.message
            )

            weights = initial


        weights = np.maximum(
            weights,
            0
        )


        if weights.sum() == 0:

            weights = initial

        else:

            weights = (
                weights
                /
                weights.sum()
            )


        optimized_weights[
            target
        ] = weights


        print()

        for name, weight in zip(
            EVIDENCE_NAMES,
            weights
        ):

            print(
                f"  {name:10s} : "
                f"{weight:.4f} "
                f"({weight*100:.2f}%)"
            )




    # ============================================================
    # 28. 최적 가중치로 종합 확신도 계산
    # ============================================================

    print()
    print("[9] 종합 확신도 계산")


    for target in TARGETS:

        weights = (
            optimized_weights[target]
        )


        train[
            f"confidence_{target}"
        ] = weighted_confidence(
            train,
            target,
            weights
        )


        valid[
            f"confidence_{target}"
        ] = weighted_confidence(
            valid,
            target,
            weights
        )





    # ============================================================
    # 29. 최적 확신도 임계값 자동 검색
    #
    # F1 최대가 되는 threshold 선택
    # ============================================================

    optimal_thresholds = {}


    print()
    print("=" * 80)
    print("[10] 최적 확신도 임계값 검색")
    print("=" * 80)


    for target in TARGETS:

        confidence = (
            valid[
                f"confidence_{target}"
            ]
            .to_numpy(
                dtype=float
            )
        )


        y_true = (
            valid[
                f"actual_{target}"
            ]
            .to_numpy(
                dtype=int
            )
        )


        mask = np.isfinite(
            confidence
        )


        confidence = (
            confidence[mask]
        )

        y_true = (
            y_true[mask]
        )


        best_threshold = 0.50
        best_f1 = -1.0


        for threshold in np.arange(
            0.30,
            0.951,
            0.01
        ):

            prediction = (
                confidence
                >= threshold
            ).astype(int)


            score = f1_score(
                y_true,
                prediction,
                zero_division=0
            )


            if score > best_f1:

                best_f1 = score

                best_threshold = (
                    threshold
                )


        optimal_thresholds[
            target
        ] = best_threshold


        print()
        print(
            f"{target}℃"
        )

        print(
            f"  최적 확신도 기준 : "
            f"{best_threshold:.2f}"
        )

        print(
            f"  Validation F1    : "
            f"{best_f1:.4f}"
        )




    # ============================================================
    # 30. 최종 예측
    # ============================================================

    for target in TARGETS:

        threshold = (
            optimal_thresholds[target]
        )


        valid[
            f"prediction_{target}"
        ] = (
            valid[
                f"confidence_{target}"
            ]
            >= threshold
        ).astype(int)




    # ============================================================
    # 31. 성능 평가
    # ============================================================

    performance = []


    print()
    print("=" * 80)
    print("[11] 최종 예측 성능")
    print("=" * 80)


    for target in TARGETS:

        y_true = (
            valid[
                f"actual_{target}"
            ]
            .to_numpy(
                dtype=int
            )
        )


        y_pred = (
            valid[
                f"prediction_{target}"
            ]
            .to_numpy(
                dtype=int
            )
        )


        confidence = (
            valid[
                f"confidence_{target}"
            ]
            .to_numpy(
                dtype=float
            )
        )


        accuracy = accuracy_score(
            y_true,
            y_pred
        )


        precision = precision_score(
            y_true,
            y_pred,
            zero_division=0
        )


        recall = recall_score(
            y_true,
            y_pred,
            zero_division=0
        )


        f1 = f1_score(
            y_true,
            y_pred,
            zero_division=0
        )


        mask = np.isfinite(
            confidence
        )


        if mask.sum() > 0:

            brier = (
                brier_score_loss(
                    y_true[mask],
                    confidence[mask]
                )
            )

        else:

            brier = np.nan


        cm = confusion_matrix(
            y_true,
            y_pred,
            labels=[0, 1]
        )


        tn = cm[0, 0]
        fp = cm[0, 1]
        fn = cm[1, 0]
        tp = cm[1, 1]


        print()
        print(
            f"목표온도 : {target}℃"
        )

        print(
            f"최적 기준 : "
            f"{optimal_thresholds[target]:.2f}"
        )

        print(
            f"Accuracy  : "
            f"{accuracy*100:.2f}%"
        )

        print(
            f"Precision : "
            f"{precision*100:.2f}%"
        )

        print(
            f"Recall    : "
            f"{recall*100:.2f}%"
        )

        print(
            f"F1        : "
            f"{f1:.4f}"
        )

        print(
            f"Brier     : "
            f"{brier:.4f}"
        )

        print()
        print(
            "Confusion Matrix"
        )

        print(cm)


        performance.append({

            "목표온도": target,

            "최적확신도기준":
                optimal_thresholds[target],

            "Accuracy":
                accuracy,

            "Precision":
                precision,

            "Recall":
                recall,

            "F1":
                f1,

            "BrierScore":
                brier,

            "TN": tn,
            "FP": fp,
            "FN": fn,
            "TP": tp
        })




    # ============================================================
    # 32. 검증 결과 생성
    # ============================================================

    result_df = valid.copy()


    # ============================================================
    # 33. 실제 10분 후 온도
    # ============================================================

    result_df[
        "actual_future_oil_temp"
    ] = (
        result_df["future_temp"]
    )


    # ============================================================
    # 34. 확신도 상태
    # ============================================================

    for target in TARGETS:

        threshold = (
            optimal_thresholds[target]
        )


        confidence = (
            result_df[
                f"confidence_{target}"
            ]
        )


        level = np.select(
            [
                confidence.isna(),

                confidence < 0.30,

                confidence < threshold
            ],
            [
                "DATA 부족",

                "낮음",

                "주의"
            ],
            default="예측"
        )


        result_df[
            f"level_{target}"
        ] = level


    # ============================================================
    # 35. 실제 도달 여부
    # ============================================================

    for target in TARGETS:

        result_df[
            f"actual_reached_{target}"
        ] = (
            result_df[
                "future_temp"
            ]
            >= target
        ).astype(int)


    # ============================================================
    # 36. 예측 성공 여부
    # ============================================================

    for target in TARGETS:

        result_df[
            f"correct_{target}"
        ] = (
            result_df[
                f"prediction_{target}"
            ]
            ==
            result_df[
                f"actual_reached_{target}"
            ]
        ).astype(int)


    # ============================================================
    # 37. CSV 저장
    # ============================================================

    result_file = (
        "확신도_자동계산_80_85_90도_결과.csv"
    )


    result_df.to_csv(
        result_file,
        index=False,
        encoding="utf-8-sig"
    )


    print()
    print(
        "[12] 결과 CSV 저장:"
    )

    print(
        os.path.abspath(
            result_file
        )
    )


    # ============================================================
    # 38. Excel 저장
    # ============================================================

    excel_file = (
        "확신도_자동생성_80_85_90도_규칙.xlsx"
    )


    with pd.ExcelWriter(
        excel_file,
        engine="openpyxl"
    ) as writer:

        # --------------------------------------------------------
        # 성능
        # --------------------------------------------------------

        pd.DataFrame(
            performance
        ).to_excel(
            writer,
            sheet_name="성능",
            index=False
        )


        # --------------------------------------------------------
        # 자동 가중치
        # --------------------------------------------------------

        weight_rows = []


        for target in TARGETS:

            row = {
                "목표온도": target
            }


            weights = (
                optimized_weights[target]
            )


            for name, weight in zip(
                EVIDENCE_NAMES,
                weights
            ):

                row[
                    name
                ] = weight


            row[
                "최적확신도기준"
            ] = (
                optimal_thresholds[target]
            )


            weight_rows.append(
                row
            )


        pd.DataFrame(
            weight_rows
        ).to_excel(
            writer,
            sheet_name="자동가중치",
            index=False
        )


        # --------------------------------------------------------
        # 각 목표온도 규칙
        # --------------------------------------------------------

        for target in TARGETS:

            for name, rule in (
                rules[target].items()
            ):

                sheet_name = (
                    f"{target}_{name}"
                )


                # Excel sheet 이름 최대 31자
                sheet_name = (
                    sheet_name[:31]
                )


                rule.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )


    print()
    print(
        "[13] 규칙 Excel 저장:"
    )

    print(
        os.path.abspath(
            excel_file
        )
    )


    # ============================================================
    # 39. 마지막 요약
    # ============================================================

    print()
    print("=" * 80)
    print("완료")
    print("=" * 80)

    print()

    f1_result = []


    for target in TARGETS:

        row = next(
            x
            for x in performance
            if x["목표온도"] == target
        )


        print(
            f"{target}℃ : "
            f"Threshold={row['최적확신도기준']:.2f}, "
            f"Accuracy={row['Accuracy']*100:.2f}%, "
            f"Precision={row['Precision']*100:.2f}%, "
            f"Recall={row['Recall']*100:.2f}%, "
            f"F1={row['F1']:.4f}, "
            f"Brier={row['BrierScore']:.4f}"
        )

        f1_result.append({
            "목표온도": target,
            "Accuracy": row["Accuracy"],
            "Precision": row["Precision"],
            "Recall": row["Recall"],
            "F1_Score": row["F1"],
            "BrierScore": row["BrierScore"]
        })


    # ============================================================
    # 성능 결과 저장
    # ============================================================

    f1_df = pd.DataFrame(f1_result)
    f1_file = "F1_Score_결과.csv"
    f1_df.to_csv(
        f1_file,
        index=False,
        encoding="utf-8-sig"
    )

    print("F1-score saved;")
    print(os.path.abspath(f1_file))



    print()
    print(
        "결과 CSV :",
        os.path.abspath(result_file)
    )

    print(
        "규칙 Excel :",
        os.path.abspath(excel_file)
    )

    print()
    print("=" * 80)



    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    return result
    # @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@


    
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
if __name__ == '__main__':
    print("hello,main of cf.py")
