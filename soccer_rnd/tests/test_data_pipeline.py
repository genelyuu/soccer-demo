"""
데이터 로딩 및 전처리 파이프라인 단위 테스트.

loader.py의 스키마 검증, preprocess.py의 RR 필터링·일별 부하 지표·시차 데이터셋
생성 로직을 검증한다.
"""

import numpy as np
import pandas as pd
import pytest

from src.data.loader import validate_schema
from src.data.preprocess import (
    build_lagged_dataset,
    compute_daily_load_metrics,
    filter_rr_outliers,
)


# ===========================================================================
# validate_schema 테스트
# ===========================================================================

class TestValidateSchema:
    """스키마 검증 함수 테스트 모음."""

    def test_필수_컬럼_모두_존재하면_통과(self):
        """필수 컬럼이 모두 있으면 예외 없이 통과해야 한다."""
        df = pd.DataFrame({
            "athlete_id": ["P01"],
            "date": ["2025-01-01"],
            "srpe": [300.0],
        })
        # 예외가 발생하지 않으면 성공
        validate_schema(df, ["athlete_id", "date", "srpe"], "Test Schema")

    def test_필수_컬럼_누락시_ValueError(self):
        """필수 컬럼이 누락되면 ValueError가 발생해야 한다."""
        df = pd.DataFrame({
            "athlete_id": ["P01"],
            "date": ["2025-01-01"],
        })
        with pytest.raises(ValueError, match="필수 컬럼 누락"):
            validate_schema(df, ["athlete_id", "date", "srpe"], "Test Schema")

    def test_에러_메시지에_누락_컬럼_포함(self):
        """에러 메시지에 누락된 컬럼명이 포함되어야 한다."""
        df = pd.DataFrame({"a": [1]})
        with pytest.raises(ValueError, match="missing_col"):
            validate_schema(df, ["a", "missing_col"], "Test")


# ===========================================================================
# filter_rr_outliers 테스트
# ===========================================================================

class TestFilterRrOutliers:
    """RR 간격 이상치 필터링 테스트 모음."""

    def test_정상_범위_RR_유지(self):
        """중앙값 ±20% 이내의 값은 그대로 유지되어야 한다."""
        # 중앙값 = 800, 허용 범위: 640~960
        rr = pd.Series([780.0, 800.0, 820.0, 790.0, 810.0])
        result = filter_rr_outliers(rr, threshold=0.20)

        # 모든 값이 NaN 없이 유지
        assert result.notna().all()
        pd.testing.assert_series_equal(result, rr)

    def test_이상치_NaN_대체(self):
        """중앙값 ±20% 범위를 벗어나는 값은 NaN으로 대체되어야 한다."""
        # 중앙값 = 800, 허용 범위: 640~960
        rr = pd.Series([800.0, 800.0, 800.0, 400.0, 1200.0])
        result = filter_rr_outliers(rr, threshold=0.20)

        # 인덱스 0~2: 유지, 인덱스 3(400): NaN, 인덱스 4(1200): NaN
        assert result.iloc[0] == 800.0
        assert result.iloc[1] == 800.0
        assert result.iloc[2] == 800.0
        assert np.isnan(result.iloc[3])
        assert np.isnan(result.iloc[4])

    def test_경계값_포함(self):
        """중앙값의 정확히 ±threshold 경계에 있는 값은 유지되어야 한다."""
        # 중앙값 = 1000, threshold=0.20 → 범위: 800~1200
        rr = pd.Series([1000.0, 800.0, 1200.0])
        result = filter_rr_outliers(rr, threshold=0.20)

        # 경계값(800, 1200)은 범위 내이므로 유지
        assert result.notna().all()


# ===========================================================================
# compute_daily_load_metrics 테스트
# ===========================================================================

class TestComputeDailyLoadMetrics:
    """일별 부하 지표 일괄 산출 테스트 모음."""

    def test_산출_컬럼_존재(self):
        """ATL, CTL, ACWR, Monotony, Strain 컬럼이 모두 생성되어야 한다."""
        # 30일치 합성 데이터 (ACWR rolling은 28일 필요)
        dates = pd.date_range("2025-01-01", periods=30, freq="D")
        df = pd.DataFrame({
            "athlete_id": ["P01"] * 30,
            "date": dates,
            "srpe": [300.0] * 30,
        })

        result = compute_daily_load_metrics(df)

        expected_cols = [
            "atl_rolling", "ctl_rolling", "acwr_rolling",
            "atl_ewma", "ctl_ewma", "acwr_ewma",
            "monotony", "strain",
        ]
        for col in expected_cols:
            assert col in result.columns, f"컬럼 '{col}'이 결과에 없음"

    def test_다중_선수_독립_산출(self):
        """여러 선수가 있을 때 각 선수별로 독립적으로 지표가 산출되어야 한다."""
        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        df = pd.DataFrame({
            "athlete_id": ["P01"] * 10 + ["P02"] * 10,
            "date": list(dates) * 2,
            "srpe": [100.0] * 10 + [500.0] * 10,
        })

        result = compute_daily_load_metrics(df)

        # 각 선수별 ATL 7일 rolling 값이 다른지 확인 (7번째 날 이후)
        p01 = result[result["athlete_id"] == "P01"]
        p02 = result[result["athlete_id"] == "P02"]

        atl_p01_last = p01["atl_rolling"].iloc[-1]
        atl_p02_last = p02["atl_rolling"].iloc[-1]

        # P01(부하 100)과 P02(부하 500)의 ATL은 달라야 함
        assert atl_p01_last != atl_p02_last


# ===========================================================================
# build_lagged_dataset 테스트
# ===========================================================================

class TestBuildLaggedDataset:
    """시차 분석용 데이터셋 생성 테스트 모음."""

    def test_lag1_올바른_shift(self):
        """lag=1 적용 시 결과 컬럼이 1행 후행 이동되어야 한다."""
        df = pd.DataFrame({
            "athlete_id": ["P01"] * 5,
            "load": [10.0, 20.0, 30.0, 40.0, 50.0],
            "outcome": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        result = build_lagged_dataset(
            df,
            outcome_col="outcome",
            predictor_cols=["load"],
            group_col="athlete_id",
            lag=1,
        )

        # lag=1: outcome_lag1 = 다음 행의 outcome
        # 행 0: load=10, outcome_lag1=2.0 (원래 행 1의 outcome)
        # 행 1: load=20, outcome_lag1=3.0
        # 행 2: load=30, outcome_lag1=4.0
        # 행 3: load=40, outcome_lag1=5.0
        # 행 4: NaN → 제거
        assert len(result) == 4
        assert "outcome_lag1" in result.columns

        expected_lagged = [2.0, 3.0, 4.0, 5.0]
        np.testing.assert_array_almost_equal(
            result["outcome_lag1"].values, expected_lagged
        )

    def test_그룹별_독립_shift(self):
        """서로 다른 그룹(선수) 간에 shift가 독립적으로 적용되어야 한다."""
        df = pd.DataFrame({
            "athlete_id": ["P01", "P01", "P01", "P02", "P02", "P02"],
            "load": [10.0, 20.0, 30.0, 100.0, 200.0, 300.0],
            "outcome": [1.0, 2.0, 3.0, 10.0, 20.0, 30.0],
        })

        result = build_lagged_dataset(
            df,
            outcome_col="outcome",
            predictor_cols=["load"],
            group_col="athlete_id",
            lag=1,
        )

        # P01: 3행 중 마지막 1행 NaN 제거 → 2행
        # P02: 3행 중 마지막 1행 NaN 제거 → 2행
        # 총 4행
        assert len(result) == 4

        # P01의 lagged outcome: [2.0, 3.0] (그룹 내 shift)
        p01 = result[result["athlete_id"] == "P01"]
        np.testing.assert_array_almost_equal(
            p01["outcome_lag1"].values, [2.0, 3.0]
        )

        # P02의 lagged outcome: [20.0, 30.0] (그룹 내 shift, P01 영향 없음)
        p02 = result[result["athlete_id"] == "P02"]
        np.testing.assert_array_almost_equal(
            p02["outcome_lag1"].values, [20.0, 30.0]
        )

    def test_NaN_행_제거(self):
        """shift 후 NaN이 포함된 행은 최종 결과에서 제거되어야 한다."""
        df = pd.DataFrame({
            "group": ["A", "A"],
            "x": [1.0, 2.0],
            "y": [10.0, 20.0],
        })

        result = build_lagged_dataset(
            df,
            outcome_col="y",
            predictor_cols=["x"],
            group_col="group",
            lag=1,
        )

        # 2행 중 마지막 1행 NaN 제거 → 1행만 남음
        assert len(result) == 1
        assert result["y_lag1"].iloc[0] == 20.0
