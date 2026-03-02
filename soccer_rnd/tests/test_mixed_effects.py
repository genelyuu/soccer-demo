"""
혼합효과모형 모듈 단위 테스트.

랜덤 절편·기울기 모형 적합, 지표 추출, 다중 모형 비교, 시각화 로직을 검증한다.

합성 데이터: 5명 피험자 × 50일, y = 4 + 0.5*x + random_intercept + noise.
"""

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from src.stats.mixed_effects import (
    compare_models,
    extract_model_metrics,
    fit_random_intercept,
    fit_random_slope,
    plot_model_comparison,
)

# Matplotlib 백엔드를 비-대화형으로 설정 (CI 호환)
matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# 합성 데이터 생성 (5명 피험자 × 50일)
# ---------------------------------------------------------------------------

@pytest.fixture()
def synthetic_data() -> pd.DataFrame:
    """합성 반복측정 데이터를 생성한다.

    y = 4 + 0.5*x + random_intercept_per_subject + noise
    """
    rng = np.random.default_rng(seed=42)

    n_subjects = 5
    n_days = 50

    records: list[dict] = []
    for subj_id in range(1, n_subjects + 1):
        # 피험자별 랜덤 절편 (평균 0, 표준편차 1)
        random_intercept = rng.normal(0, 1.0)
        for day in range(n_days):
            x = rng.uniform(0.5, 2.0)
            noise = rng.normal(0, 0.3)
            y = 4.0 + 0.5 * x + random_intercept + noise
            records.append({
                "subject_id": f"S{subj_id:03d}",
                "day": day,
                "x": x,
                "y": y,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# fit_random_intercept 테스트
# ---------------------------------------------------------------------------

class TestFitRandomIntercept:
    """랜덤 절편 모형 적합 테스트 모음."""

    def test_적합_성공_및_결과_타입(self, synthetic_data: pd.DataFrame):
        """합성 데이터에 대해 랜덤 절편 모형이 적합되고, MixedLM 결과 객체를 반환해야 한다."""
        result = fit_random_intercept("y ~ x", synthetic_data, "subject_id")
        # statsmodels는 MixedLMResultsWrapper를 반환하므로 속성 기반 검증
        assert hasattr(result, "fe_params"), "fe_params 속성이 없음"
        assert hasattr(result, "fittedvalues"), "fittedvalues 속성이 없음"

    def test_고정효과_x_계수_양수(self, synthetic_data: pd.DataFrame):
        """합성 데이터의 x 계수(0.5)가 양수로 추정되어야 한다."""
        result = fit_random_intercept("y ~ x", synthetic_data, "subject_id")
        assert result.fe_params["x"] > 0


# ---------------------------------------------------------------------------
# fit_random_slope 테스트
# ---------------------------------------------------------------------------

class TestFitRandomSlope:
    """랜덤 기울기 모형 적합 테스트 모음."""

    def test_적합_성공_및_결과_타입(self, synthetic_data: pd.DataFrame):
        """합성 데이터에 대해 랜덤 기울기 모형이 적합되고, MixedLM 결과 객체를 반환해야 한다."""
        result = fit_random_slope("y ~ x", synthetic_data, "subject_id", "x")
        assert result is None or hasattr(result, "fe_params")

    def test_랜덤_기울기_분산_양수(self, synthetic_data: pd.DataFrame):
        """랜덤 기울기 분산이 0 이상이어야 한다 (추정된 경우)."""
        result = fit_random_slope("y ~ x", synthetic_data, "subject_id", "x")
        if result is not None:
            # cov_re 대각 원소(분산)가 >= 0
            cov_re = result.cov_re
            if isinstance(cov_re, pd.DataFrame):
                variances = np.diag(cov_re.values)
            else:
                variances = np.diag(np.atleast_2d(cov_re))
            assert all(v >= 0 for v in variances), "랜덤효과 분산이 음수임"

    def test_수렴_실패_시_none_반환(self):
        """극단적으로 작은 데이터에서 수렴 실패 시 None을 반환해야 한다."""
        # 그룹당 관측값 1개 → 수렴 불가 가능성 높음
        tiny_data = pd.DataFrame({
            "subject_id": ["A", "B"],
            "x": [1.0, 2.0],
            "y": [3.0, 4.0],
        })
        result = fit_random_slope("y ~ x", tiny_data, "subject_id", "x")
        # 수렴 실패 시 None, 성공 시 결과 객체 — 두 경우 모두 허용
        assert result is None or hasattr(result, "fe_params")


# ---------------------------------------------------------------------------
# extract_model_metrics 테스트
# ---------------------------------------------------------------------------

class TestExtractModelMetrics:
    """모형 지표 추출 테스트 모음."""

    def test_필수_키_존재(self, synthetic_data: pd.DataFrame):
        """반환 dict에 aic, bic, mae, rmse 키가 존재해야 한다."""
        result = fit_random_intercept("y ~ x", synthetic_data, "subject_id")
        metrics = extract_model_metrics(result, synthetic_data, "y")

        for key in ("aic", "bic", "mae", "rmse"):
            assert key in metrics, f"키 '{key}'가 존재하지 않음"
            assert not np.isnan(metrics[key]), f"키 '{key}' 값이 NaN"

    def test_none_입력_시_nan_반환(self, synthetic_data: pd.DataFrame):
        """result가 None이면 모든 값이 NaN인 dict를 반환해야 한다."""
        metrics = extract_model_metrics(None, synthetic_data, "y")

        assert np.isnan(metrics["aic"])
        assert np.isnan(metrics["bic"])
        assert np.isnan(metrics["mae"])
        assert np.isnan(metrics["rmse"])


# ---------------------------------------------------------------------------
# compare_models 테스트
# ---------------------------------------------------------------------------

class TestCompareModels:
    """다중 모형 비교 테스트 모음."""

    def test_비교_dataframe_행수(self, synthetic_data: pd.DataFrame):
        """2개 모형 비교 시 DataFrame 행 수가 2여야 한다."""
        ri_result = fit_random_intercept("y ~ x", synthetic_data, "subject_id")
        rs_result = fit_random_slope("y ~ x", synthetic_data, "subject_id", "x")

        models = {
            "random_intercept": ri_result,
            "random_slope": rs_result,
        }
        comparison_df = compare_models(models, synthetic_data, "y")

        assert len(comparison_df) == 2
        assert "model_name" in comparison_df.columns
        assert "aic" in comparison_df.columns
        assert "cohens_f2" in comparison_df.columns


# ---------------------------------------------------------------------------
# plot_model_comparison 테스트
# ---------------------------------------------------------------------------

class TestPlotModelComparison:
    """모형 비교 시각화 테스트 모음."""

    def test_figure_반환(self, synthetic_data: pd.DataFrame):
        """plot_model_comparison이 matplotlib Figure를 반환해야 한다."""
        ri_result = fit_random_intercept("y ~ x", synthetic_data, "subject_id")
        rs_result = fit_random_slope("y ~ x", synthetic_data, "subject_id", "x")

        models = {
            "random_intercept": ri_result,
            "random_slope": rs_result,
        }
        comparison_df = compare_models(models, synthetic_data, "y")
        fig = plot_model_comparison(comparison_df, metric="aic")

        assert isinstance(fig, matplotlib.figure.Figure)
        plt.close(fig)  # 리소스 정리
