"""
LOSO 교차 검증 모듈 단위 테스트.

혼합효과모형의 일반화 성능 평가를 위한 LOSO CV 함수들의 정확성을 검증한다.

합성 데이터: 8명 선수 x 30일, hooper_next = 10 + 2*acwr + 1.5*monotony + noise.
"""

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from src.stats.cross_validation import (
    loso_cv,
    loso_cv_multi_model,
    loso_summary,
    plot_loso_results,
)

# Matplotlib 백엔드를 비-대화형으로 설정 (CI 호환)
matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# 합성 데이터 생성 (8명 선수 x 30일)
# ---------------------------------------------------------------------------

@pytest.fixture()
def synthetic_panel() -> pd.DataFrame:
    """합성 패널 데이터를 생성한다.

    hooper_next = 10 + 2*acwr_rolling + 1.5*monotony + 선수별_절편 + noise
    """
    np.random.seed(42)

    n_athletes = 8
    n_days = 30

    records: list[dict] = []
    for athlete_id in range(1, n_athletes + 1):
        # 선수별 랜덤 절편
        random_intercept = np.random.normal(0, 1.5)
        for day in range(n_days):
            srpe = np.random.uniform(100, 600)
            acwr_rolling = np.random.uniform(0.5, 2.0)
            monotony_val = np.random.uniform(0.3, 2.5)
            noise = np.random.normal(0, 0.5)

            hooper_next = (
                10.0
                + 2.0 * acwr_rolling
                + 1.5 * monotony_val
                + random_intercept
                + noise
            )

            records.append({
                "athlete_id": f"A{athlete_id:02d}",
                "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=day),
                "srpe": srpe,
                "hooper_next": hooper_next,
                "acwr_rolling": acwr_rolling,
                "monotony": monotony_val,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# TestLosoCv: LOSO 교차 검증 기본 기능
# ---------------------------------------------------------------------------

class TestLosoCv:
    """LOSO 교차 검증 함수의 기본 동작을 검증한다."""

    def test_결과_컬럼_확인(self, synthetic_panel: pd.DataFrame):
        """반환 DataFrame이 [subject, n_train, n_test, mae, rmse] 컬럼을 가져야 한다."""
        cv_results = loso_cv(
            "hooper_next ~ acwr_rolling + monotony",
            synthetic_panel,
            "athlete_id",
            "hooper_next",
        )
        expected_cols = {"subject", "n_train", "n_test", "mae", "rmse"}
        assert expected_cols == set(cv_results.columns), (
            f"컬럼 불일치: 기대={expected_cols}, 실제={set(cv_results.columns)}"
        )

    def test_fold_수_일치(self, synthetic_panel: pd.DataFrame):
        """고유 선수 수만큼 fold(행)가 생성되어야 한다."""
        cv_results = loso_cv(
            "hooper_next ~ acwr_rolling + monotony",
            synthetic_panel,
            "athlete_id",
            "hooper_next",
        )
        n_athletes = synthetic_panel["athlete_id"].nunique()
        assert len(cv_results) == n_athletes, (
            f"fold 수 불일치: 기대={n_athletes}, 실제={len(cv_results)}"
        )

    def test_mae_rmse_양수(self, synthetic_panel: pd.DataFrame):
        """유효한 fold의 MAE와 RMSE가 0 이상이어야 한다."""
        cv_results = loso_cv(
            "hooper_next ~ acwr_rolling + monotony",
            synthetic_panel,
            "athlete_id",
            "hooper_next",
        )
        valid = cv_results.dropna(subset=["mae", "rmse"])
        assert len(valid) > 0, "유효한 fold가 하나도 없음"
        assert (valid["mae"] >= 0).all(), "MAE에 음수값 존재"
        assert (valid["rmse"] >= 0).all(), "RMSE에 음수값 존재"

    def test_소규모_그룹_경고(self):
        """그룹이 2개 미만일 때(학습 그룹 1개) 경고가 발생해야 한다."""
        # 선수 2명: 한 명을 테스트로 빼면 학습 그룹 1개
        np.random.seed(99)
        small_data = pd.DataFrame({
            "athlete_id": ["P1"] * 10 + ["P2"] * 10,
            "x": np.random.uniform(0, 1, 20),
            "y": np.random.normal(5, 1, 20),
        })

        with pytest.warns(UserWarning, match="2개 미만"):
            cv_results = loso_cv("y ~ x", small_data, "athlete_id", "y")

        # 모든 fold가 NaN이어야 함 (학습 그룹이 항상 1개)
        assert cv_results["mae"].isna().all(), "소규모 그룹에서 NaN이 아닌 MAE 존재"


# ---------------------------------------------------------------------------
# TestLosoSummary: 요약 통계 기능
# ---------------------------------------------------------------------------

class TestLosoSummary:
    """LOSO 결과 요약 함수의 정확성을 검증한다."""

    def test_요약_키_확인(self, synthetic_panel: pd.DataFrame):
        """반환 dict에 필수 키 8개가 모두 존재해야 한다."""
        cv_results = loso_cv(
            "hooper_next ~ acwr_rolling + monotony",
            synthetic_panel,
            "athlete_id",
            "hooper_next",
        )
        summary = loso_summary(cv_results)

        expected_keys = {
            "mean_mae", "std_mae", "median_mae",
            "mean_rmse", "std_rmse", "median_rmse",
            "n_subjects", "n_valid_folds",
        }
        assert expected_keys == set(summary.keys()), (
            f"키 불일치: 기대={expected_keys}, 실제={set(summary.keys())}"
        )

    def test_nan_fold_제외(self):
        """NaN이 포함된 결과에서 n_valid_folds가 정확히 계산되어야 한다."""
        # 수동으로 NaN이 포함된 결과 생성
        cv_results = pd.DataFrame({
            "subject": ["A", "B", "C", "D"],
            "n_train": [90, 90, 90, 90],
            "n_test": [10, 10, 10, 10],
            "mae": [1.0, np.nan, 2.0, 3.0],
            "rmse": [1.5, np.nan, 2.5, 3.5],
        })
        summary = loso_summary(cv_results)

        assert summary["n_subjects"] == 4, "전체 선수 수가 4가 아님"
        assert summary["n_valid_folds"] == 3, "유효 fold 수가 3이 아님"

    def test_모든_fold_유효(self, synthetic_panel: pd.DataFrame):
        """전체 fold가 유효할 때 n_valid_folds == n_subjects 여야 한다."""
        cv_results = loso_cv(
            "hooper_next ~ acwr_rolling + monotony",
            synthetic_panel,
            "athlete_id",
            "hooper_next",
        )
        summary = loso_summary(cv_results)

        assert summary["n_valid_folds"] == summary["n_subjects"], (
            f"유효 fold 수({summary['n_valid_folds']})가 "
            f"전체 선수 수({summary['n_subjects']})와 다름"
        )


# ---------------------------------------------------------------------------
# TestLosoMultiModel: 다중 모형 비교 기능
# ---------------------------------------------------------------------------

class TestLosoMultiModel:
    """다중 모형 LOSO 비교 함수의 정확성을 검증한다."""

    def test_모형수_일치(self, synthetic_panel: pd.DataFrame):
        """모형 수만큼 행이 생성되어야 한다."""
        formulas = {
            "단순모형": "hooper_next ~ acwr_rolling",
            "복합모형": "hooper_next ~ acwr_rolling + monotony",
        }
        result = loso_cv_multi_model(
            formulas, synthetic_panel, "athlete_id", "hooper_next"
        )
        assert len(result) == 2, f"행 수 불일치: 기대=2, 실제={len(result)}"
        assert set(result["model_name"]) == {"단순모형", "복합모형"}

    def test_단일_모형(self, synthetic_panel: pd.DataFrame):
        """모형 1개만 넣어도 정상 작동해야 한다."""
        formulas = {
            "단독모형": "hooper_next ~ acwr_rolling",
        }
        result = loso_cv_multi_model(
            formulas, synthetic_panel, "athlete_id", "hooper_next"
        )
        assert len(result) == 1, f"행 수 불일치: 기대=1, 실제={len(result)}"
        assert "mean_mae" in result.columns
        assert "mean_rmse" in result.columns


# ---------------------------------------------------------------------------
# TestPlotLosoResults: 시각화 기능
# ---------------------------------------------------------------------------

class TestPlotLosoResults:
    """LOSO 결과 시각화 함수를 검증한다."""

    def test_figure_반환(self, synthetic_panel: pd.DataFrame):
        """plot_loso_results가 matplotlib Figure 객체를 반환해야 한다."""
        cv_results = loso_cv(
            "hooper_next ~ acwr_rolling + monotony",
            synthetic_panel,
            "athlete_id",
            "hooper_next",
        )
        fig = plot_loso_results(cv_results, title="LOSO 테스트")
        assert isinstance(fig, matplotlib.figure.Figure), (
            f"반환 타입이 Figure가 아님: {type(fig)}"
        )
