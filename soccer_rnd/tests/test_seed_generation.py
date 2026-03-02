"""
시드 데이터 무결성 테스트.

generate_seed_data.py가 생성한 CSV의 구조적 정합성과
기존 R&D 파이프라인 호환성을 검증한다.
"""

import numpy as np
import pandas as pd
import pytest

from src.data.loader import TRACK_B_REQUIRED_COLS, validate_schema
from src.data.supabase_loader import (
    SEED_TRACK_A_REQUIRED_COLS,
    load_seed_track_a,
    load_seed_track_b,
)
from src.data.preprocess import compute_daily_load_metrics


# ---------------------------------------------------------------------------
# 픽스처: 시드 데이터 로딩 (세션 단위 캐싱)
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def track_b_df() -> pd.DataFrame:
    """시드 트랙 B DataFrame."""
    return load_seed_track_b("data/seed/seed_track_b.csv")


@pytest.fixture(scope="session")
def track_a_df() -> pd.DataFrame:
    """시드 트랙 A DataFrame."""
    return load_seed_track_a("data/seed/seed_track_a.csv")


# UUID 목록
EXISTING_5_UUIDS = [
    f"00000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(1, 6)
]
ALL_15_UUIDS = [
    f"00000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(1, 16)
]


# ---------------------------------------------------------------------------
# 테스트
# ---------------------------------------------------------------------------
class Test사용자:
    """사용자 수 및 UUID 보존 검증."""

    def test_사용자_수_15명(self, track_b_df: pd.DataFrame) -> None:
        """트랙 B 시드 데이터에 15명의 고유 사용자가 존재해야 한다."""
        assert track_b_df["athlete_id"].nunique() == 15

    def test_기존_5명_UUID_보존(self, track_b_df: pd.DataFrame) -> None:
        """기존 5명 사용자의 UUID가 시드 데이터에 포함되어야 한다."""
        athletes = set(track_b_df["athlete_id"].unique())
        for uuid in EXISTING_5_UUIDS:
            assert uuid in athletes, f"기존 UUID 누락: {uuid}"

    def test_트랙A_사용자_15명(self, track_a_df: pd.DataFrame) -> None:
        """트랙 A 시드 데이터에도 15명의 고유 피험자가 존재해야 한다."""
        assert track_a_df["subject_id"].nunique() == 15


class Test스키마호환:
    """R&D 표준 스키마 호환성 검증."""

    def test_트랙B_스키마_호환(self, track_b_df: pd.DataFrame) -> None:
        """트랙 B 시드 데이터가 TRACK_B_REQUIRED_COLS을 충족해야 한다."""
        # validate_schema가 에러 없이 실행되면 통과
        validate_schema(track_b_df, TRACK_B_REQUIRED_COLS, "Seed Track B")

    def test_트랙A_스키마_호환(self, track_a_df: pd.DataFrame) -> None:
        """트랙 A 시드 데이터가 필수 컬럼을 충족해야 한다."""
        validate_schema(
            track_a_df, SEED_TRACK_A_REQUIRED_COLS, "Seed Track A"
        )


class Test값범위:
    """데이터 값 범위 검증."""

    def test_RPE_범위_1_10(self, track_b_df: pd.DataFrame) -> None:
        """RPE 값이 1~10 범위 내여야 한다."""
        valid_rpe = track_b_df["rpe"].dropna()
        assert valid_rpe.min() >= 1.0, f"RPE 최솟값 {valid_rpe.min()} < 1"
        assert valid_rpe.max() <= 10.0, f"RPE 최댓값 {valid_rpe.max()} > 10"

    def test_Hooper_각항목_범위_1_7(self, track_b_df: pd.DataFrame) -> None:
        """Hooper 4항목(fatigue, stress, doms, sleep)이 1~7 범위 내여야 한다."""
        for col in ["fatigue", "stress", "doms", "sleep"]:
            valid = track_b_df[col].dropna()
            assert valid.min() >= 1, f"{col} 최솟값 {valid.min()} < 1"
            assert valid.max() <= 7, f"{col} 최댓값 {valid.max()} > 7"


class Test결측:
    """결측 비율 검증."""

    def test_결측_비율_허용범위(self, track_b_df: pd.DataFrame) -> None:
        """Hooper 항목의 결측 비율이 3~7% 범위 내여야 한다 (목표 5%)."""
        for col in ["fatigue", "stress", "doms", "sleep"]:
            missing_rate = track_b_df[col].isna().mean()
            assert 0.03 <= missing_rate <= 0.07, (
                f"{col} 결측률 {missing_rate:.1%}이 허용 범위(3~7%) 밖"
            )


class Test주간패턴:
    """주간 세션 패턴 검증."""

    def test_주간패턴_토요일_경기(self, track_b_df: pd.DataFrame) -> None:
        """토요일의 sRPE가 평일보다 평균적으로 높아야 한다 (경기일)."""
        df = track_b_df.copy()
        df["dow"] = df["date"].dt.dayofweek

        # 토요일(5) vs 평일(0~4)
        sat_mean = df[df["dow"] == 5]["srpe"].mean()
        weekday_mean = df[df["dow"].isin(range(5))]["srpe"].mean()

        assert sat_mean > weekday_mean, (
            f"토요일 평균 sRPE ({sat_mean:.0f}) <= 평일 ({weekday_mean:.0f})"
        )


class Test파이프라인호환:
    """기존 R&D 파이프라인 호환성 검증."""

    def test_compute_daily_load_metrics_호환(
        self, track_b_df: pd.DataFrame
    ) -> None:
        """compute_daily_load_metrics()가 시드 데이터로 정상 실행되어야 한다."""
        result = compute_daily_load_metrics(
            track_b_df, athlete_col="athlete_id", load_col="srpe"
        )

        # 8개 산출 컬럼이 추가되어야 함
        expected_cols = [
            "atl_rolling", "ctl_rolling", "acwr_rolling",
            "atl_ewma", "ctl_ewma", "acwr_ewma",
            "monotony", "strain",
        ]
        for col in expected_cols:
            assert col in result.columns, f"산출 컬럼 누락: {col}"

        # ACWR 유효 값이 존재해야 함
        assert result["acwr_rolling"].dropna().shape[0] > 0


class Test상관관계:
    """부하-웰니스/HRV 관계 검증."""

    def test_부하_웰니스_양의상관(self, track_b_df: pd.DataFrame) -> None:
        """ACWR↑ → Hooper↑ (양의 상관)이 관찰되어야 한다."""
        df = compute_daily_load_metrics(
            track_b_df, athlete_col="athlete_id", load_col="srpe"
        )
        df["hooper_index"] = (
            df["fatigue"] + df["stress"] + df["doms"] + df["sleep"]
        )
        valid = df[["acwr_rolling", "hooper_index"]].dropna()

        if len(valid) > 30:
            corr = valid["acwr_rolling"].corr(valid["hooper_index"])
            assert corr > 0, f"ACWR-Hooper 상관 {corr:.3f} <= 0 (양의 상관 기대)"

    def test_HRV_부하_음의상관(self, track_a_df: pd.DataFrame) -> None:
        """ACWR↑ → ln_rMSSD↓ (음의 상관)이 관찰되어야 한다."""
        valid = track_a_df[["acwr_rolling", "ln_rmssd"]].dropna()

        if len(valid) > 30:
            corr = valid["acwr_rolling"].corr(valid["ln_rmssd"])
            assert corr < 0, f"ACWR-ln_rMSSD 상관 {corr:.3f} >= 0 (음의 상관 기대)"
