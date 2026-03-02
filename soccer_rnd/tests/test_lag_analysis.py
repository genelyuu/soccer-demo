"""
다중 시차(multi-lag) 분석 모듈 단위 테스트.

합성 데이터를 사용하여 lag_correlation_table, lag_mixed_effects_comparison,
optimal_lag, plot_lag_profile 함수의 정확성을 검증한다.
"""

import matplotlib
import matplotlib.figure
import numpy as np
import pandas as pd
import pytest

from src.stats.lag_analysis import (
    lag_correlation_table,
    lag_mixed_effects_comparison,
    optimal_lag,
    plot_lag_profile,
)

# matplotlib 백엔드를 비대화식으로 설정 (CI 환경 호환)
matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# 합성 데이터 생성 픽스처
# ---------------------------------------------------------------------------

@pytest.fixture()
def synthetic_lag1_data() -> pd.DataFrame:
    """
    lag=1 상관이 뚜렷하게 존재하는 합성 패널 데이터를 생성한다.

    구조: 3명의 선수, 각 60일.
    predictor(t-1)과 outcome(t) 사이에 강한 양의 상관을 주입한다.
    """
    np.random.seed(42)
    frames = []

    for player_id in ["P1", "P2", "P3"]:
        n = 60
        predictor = np.random.normal(50, 10, size=n)
        noise = np.random.normal(0, 2, size=n)
        # outcome(t) = 0.8 * predictor(t-1) + noise
        outcome = np.full(n, np.nan)
        outcome[1:] = 0.8 * predictor[:-1] + noise[1:]

        frame = pd.DataFrame({
            "player_id": player_id,
            "day": np.arange(n),
            "predictor": predictor,
            "outcome": outcome,
        })
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


@pytest.fixture()
def synthetic_multi_predictor_data() -> pd.DataFrame:
    """
    다중 예측변수를 가진 합성 패널 데이터를 생성한다.

    2명의 선수, 각 80일. predictor_a(lag=2)와 predictor_b(lag=0)가
    outcome에 기여하도록 설계한다.
    """
    np.random.seed(123)
    frames = []

    for player_id in ["A", "B"]:
        n = 80
        pred_a = np.random.normal(30, 5, size=n)
        pred_b = np.random.normal(20, 3, size=n)
        noise = np.random.normal(0, 1, size=n)

        outcome = np.full(n, np.nan)
        # outcome(t) = 0.5 * pred_a(t-2) + 0.3 * pred_b(t) + noise
        outcome[2:] = 0.5 * pred_a[:-2] + 0.3 * pred_b[2:] + noise[2:]

        frame = pd.DataFrame({
            "player_id": player_id,
            "day": np.arange(n),
            "predictor_a": pred_a,
            "predictor_b": pred_b,
            "outcome": outcome,
        })
        frames.append(frame)

    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# lag_correlation_table 테스트
# ---------------------------------------------------------------------------

class TestLagCorrelationTable:
    """lag_correlation_table 함수 테스트 모음."""

    def test_lag1_상관이_lag0보다_크다(self, synthetic_lag1_data):
        """
        lag=1 상관이 의도적으로 주입된 데이터에서
        lag=1의 |r|이 lag=0의 |r|보다 큰지 확인한다.
        """
        result = lag_correlation_table(
            synthetic_lag1_data,
            predictor_col="predictor",
            outcome_col="outcome",
            group_col="player_id",
            max_lag=3,
        )

        r_lag0 = result.loc[result["lag"] == 0, "pearson_r"].values[0]
        r_lag1 = result.loc[result["lag"] == 1, "pearson_r"].values[0]

        assert abs(r_lag1) > abs(r_lag0), (
            f"lag=1의 |r|({abs(r_lag1):.4f})이 "
            f"lag=0의 |r|({abs(r_lag0):.4f})보다 커야 한다."
        )

    def test_반환_컬럼_구조(self, synthetic_lag1_data):
        """반환 DataFrame이 필수 컬럼 [lag, pearson_r, p_value, n_obs]를 포함하는지 확인한다."""
        result = lag_correlation_table(
            synthetic_lag1_data,
            predictor_col="predictor",
            outcome_col="outcome",
            group_col="player_id",
            max_lag=5,
        )

        expected_cols = {"lag", "pearson_r", "p_value", "n_obs"}
        assert expected_cols.issubset(set(result.columns)), (
            f"필수 컬럼 누락. 기대: {expected_cols}, 실제: {set(result.columns)}"
        )

    def test_행_수는_max_lag_플러스_1(self, synthetic_lag1_data):
        """반환 DataFrame의 행 수는 max_lag + 1이어야 한다."""
        max_lag = 4
        result = lag_correlation_table(
            synthetic_lag1_data,
            predictor_col="predictor",
            outcome_col="outcome",
            group_col="player_id",
            max_lag=max_lag,
        )

        assert len(result) == max_lag + 1, (
            f"행 수 불일치. 기대: {max_lag + 1}, 실제: {len(result)}"
        )


# ---------------------------------------------------------------------------
# lag_mixed_effects_comparison 테스트
# ---------------------------------------------------------------------------

class TestLagMixedEffectsComparison:
    """lag_mixed_effects_comparison 함수 테스트 모음."""

    def test_반환_컬럼_구조(self, synthetic_lag1_data):
        """반환 DataFrame에 기본 컬럼과 예측변수별 계수/p-value 컬럼이 존재하는지 확인한다."""
        result = lag_mixed_effects_comparison(
            synthetic_lag1_data,
            outcome_col="outcome",
            predictor_cols=["predictor"],
            group_col="player_id",
            max_lag=3,
        )

        required_cols = {"lag", "aic", "bic", "mae", "rmse",
                         "coef_predictor", "pvalue_predictor"}
        assert required_cols.issubset(set(result.columns)), (
            f"필수 컬럼 누락. 기대: {required_cols}, 실제: {set(result.columns)}"
        )

    def test_lag_범위_확인(self, synthetic_lag1_data):
        """반환된 lag 값이 0부터 max_lag까지 빠짐없이 존재하는지 확인한다."""
        max_lag = 5
        result = lag_mixed_effects_comparison(
            synthetic_lag1_data,
            outcome_col="outcome",
            predictor_cols=["predictor"],
            group_col="player_id",
            max_lag=max_lag,
        )

        expected_lags = set(range(0, max_lag + 1))
        actual_lags = set(result["lag"].values)

        assert expected_lags == actual_lags, (
            f"lag 범위 불일치. 기대: {expected_lags}, 실제: {actual_lags}"
        )


# ---------------------------------------------------------------------------
# optimal_lag 테스트
# ---------------------------------------------------------------------------

class TestOptimalLag:
    """optimal_lag 함수 테스트 모음."""

    def test_aic_최소_lag_반환(self):
        """AIC가 최소인 lag을 올바르게 반환하는지 확인한다."""
        comparison_df = pd.DataFrame({
            "lag": [0, 1, 2, 3, 4],
            "aic": [120.5, 100.2, 98.1, 105.3, 110.0],
            "bic": [125.0, 105.0, 103.0, 110.0, 115.0],
        })

        result = optimal_lag(comparison_df, criterion="aic")
        assert result == 2, f"AIC 최소 lag은 2이어야 한다. 실제: {result}"

    def test_bic_기준으로도_동작(self):
        """criterion='bic'로 설정했을 때 BIC 최소 lag을 반환하는지 확인한다."""
        comparison_df = pd.DataFrame({
            "lag": [0, 1, 2, 3],
            "aic": [120.0, 100.0, 110.0, 130.0],
            "bic": [130.0, 115.0, 105.0, 125.0],
        })

        result = optimal_lag(comparison_df, criterion="bic")
        assert result == 2, f"BIC 최소 lag은 2이어야 한다. 실제: {result}"

    def test_존재하지_않는_기준_컬럼_에러(self):
        """존재하지 않는 criterion 컬럼을 지정하면 ValueError가 발생해야 한다."""
        comparison_df = pd.DataFrame({
            "lag": [0, 1],
            "aic": [100.0, 110.0],
        })

        with pytest.raises(ValueError, match="기준 컬럼"):
            optimal_lag(comparison_df, criterion="nonexistent")


# ---------------------------------------------------------------------------
# plot_lag_profile 테스트
# ---------------------------------------------------------------------------

class TestPlotLagProfile:
    """plot_lag_profile 함수 테스트 모음."""

    def test_figure_객체_반환(self):
        """plot_lag_profile이 matplotlib.figure.Figure 객체를 반환하는지 확인한다."""
        corr_table = pd.DataFrame({
            "lag": [0, 1, 2, 3],
            "pearson_r": [0.1, 0.8, 0.3, -0.05],
            "p_value": [0.5, 0.001, 0.1, 0.9],
            "n_obs": [50, 50, 50, 50],
        })

        fig = plot_lag_profile(corr_table, title="테스트 프로파일")

        assert isinstance(fig, matplotlib.figure.Figure), (
            f"반환 타입이 Figure가 아닙니다. 실제: {type(fig)}"
        )
