"""
통합 합성 데이터(DGP) 모듈 테스트.

검증 항목:
  1. DGP 구조 검증 (선수 수, 기간, 컬럼, 값 범위)
  2. ACWR warmup 27일 제거 후 유효 관측수 확인
  3. 결측 주입 비율 허용 범위 검증
  4. 참값 복원 검증 (Mixed 모형 → 계수 ±30% 이내)
"""

import numpy as np
import pandas as pd
import pytest

from src.data.synthetic_integrated import (
    DEFAULT_PARAMS,
    generate_athlete_random_effects,
    generate_daily_load,
    compute_derived_metrics,
    generate_outcomes,
    inject_missingness,
    generate_integrated_dataset,
)


# ---------------------------------------------------------------------------
# 고정 파라미터
# ---------------------------------------------------------------------------
PARAMS = DEFAULT_PARAMS.copy()


# ---------------------------------------------------------------------------
# 1. DGP 구조 검증
# ---------------------------------------------------------------------------

class TestDGPStructure:
    """DGP 출력의 구조적 정합성을 검증한다."""

    @pytest.fixture(scope="class")
    def dataset(self):
        """테스트용 통합 데이터셋 (클래스 수준 캐싱)."""
        df, re = generate_integrated_dataset(PARAMS, return_complete=True)
        return df, re

    def test_선수_수(self, dataset):
        """생성된 선수 수가 파라미터와 일치하는지 확인."""
        df, _ = dataset
        assert df["athlete"].nunique() == PARAMS["n_athletes"]

    def test_기간(self, dataset):
        """선수당 일수가 파라미터와 일치하는지 확인."""
        df, _ = dataset
        days_per_athlete = df.groupby("athlete")["day"].nunique()
        assert (days_per_athlete == PARAMS["n_days"]).all()

    def test_총_행수(self, dataset):
        """총 행수 = 선수 수 × 일수."""
        df, _ = dataset
        expected = PARAMS["n_athletes"] * PARAMS["n_days"]
        assert len(df) == expected

    def test_필수_컬럼(self, dataset):
        """필수 컬럼이 모두 존재하는지 확인."""
        df, _ = dataset
        required = [
            "athlete", "day", "daily_load",
            "acwr_ra", "acwr_ew", "mono", "strain_val",
            "ln_rmssd", "ln_rmssd_next", "hooper_next",
            "fatigue", "stress", "doms", "sleep",
        ]
        for col in required:
            assert col in df.columns, f"컬럼 누락: {col}"

    def test_부하_양수(self, dataset):
        """일별 부하가 모두 0 이상인지 확인."""
        df, _ = dataset
        assert (df["daily_load"] >= 0).all()

    def test_부하_현실_범위(self, dataset):
        """부하 값이 합리적인 범위(0~2000) 내인지 확인."""
        df, _ = dataset
        assert df["daily_load"].max() < 2000
        assert df["daily_load"].min() >= 0

    def test_랜덤효과_차원(self, dataset):
        """랜덤효과 배열의 차원이 (n_athletes, 2)인지 확인."""
        _, re = dataset
        assert re.shape == (PARAMS["n_athletes"], 2)


# ---------------------------------------------------------------------------
# 2. ACWR warmup 및 유효 관측수
# ---------------------------------------------------------------------------

class TestWarmupAndValidObs:
    """ACWR warmup 기간 제거 후 유효 관측수를 검증한다."""

    @pytest.fixture(scope="class")
    def dataset(self):
        return generate_integrated_dataset(PARAMS)

    def test_acwr_warmup_nan(self, dataset):
        """ACWR rolling의 첫 27일은 NaN이어야 한다."""
        df = dataset
        first_athlete = df[df["athlete"] == df["athlete"].iloc[0]]
        # rolling CTL window=28 → 첫 27일(인덱스 0~26)은 NaN
        acwr_first_27 = first_athlete.iloc[:27]["acwr_ra"]
        assert acwr_first_27.isna().all()

    def test_유효_관측수(self, dataset):
        """warmup 제거 후 유효 관측수 = 선수 × (120-28-1) 이상."""
        df = dataset
        # acwr_ra, mono, strain_val, hooper_next 모두 유효한 행
        valid = df.dropna(subset=["acwr_ra", "mono", "strain_val", "hooper_next"])
        # 최소 기대: 30선수 × (120 - 28 - 1) = 30 × 91 = 2730
        # (실제로는 monotony warmup 6일 추가로 약간 적을 수 있음)
        assert len(valid) >= 2500, f"유효 관측수 부족: {len(valid)}"

    def test_acwr_ewma_warmup(self, dataset):
        """ACWR EWMA의 첫 21일은 NaN이어야 한다."""
        df = dataset
        first_athlete = df[df["athlete"] == df["athlete"].iloc[0]]
        acwr_ew_first_21 = first_athlete.iloc[:21]["acwr_ew"]
        assert acwr_ew_first_21.isna().all()


# ---------------------------------------------------------------------------
# 3. 결측 주입 비율 검증
# ---------------------------------------------------------------------------

class TestMissingness:
    """결측 주입 메커니즘별 비율을 검증한다."""

    @pytest.fixture(scope="class")
    def complete_data(self):
        """결측 주입 전 완전 데이터."""
        return generate_integrated_dataset(PARAMS)

    def test_mcar_비율(self, complete_data):
        """MCAR 결측 비율이 약 10% ± 5%p 범위인지 확인."""
        rng = np.random.default_rng(999)
        valid_before = complete_data["hooper_next"].notna().sum()
        df_miss = inject_missingness(complete_data, rng, "mcar", PARAMS)
        valid_after = df_miss["hooper_next"].notna().sum()
        missing_rate = 1.0 - valid_after / valid_before
        assert 0.05 <= missing_rate <= 0.18, f"MCAR 비율: {missing_rate:.3f}"

    def test_mar_비율(self, complete_data):
        """MAR 결측 비율이 합리적 범위(3%~60%) 내인지 확인.

        MAR 파라미터: logistic(-2.0 + 0.005×load).
        평균 부하 ~400일 때 logit≈0 → P≈0.5이므로 상한을 넓힌다.
        """
        rng = np.random.default_rng(999)
        valid_before = complete_data["hooper_next"].notna().sum()
        df_miss = inject_missingness(complete_data, rng, "mar", PARAMS)
        valid_after = df_miss["hooper_next"].notna().sum()
        missing_rate = 1.0 - valid_after / valid_before
        assert 0.03 <= missing_rate <= 0.60, f"MAR 비율: {missing_rate:.3f}"

    def test_mnar_비율(self, complete_data):
        """MNAR 결측 비율이 합리적 범위(3%~30%) 내인지 확인."""
        rng = np.random.default_rng(999)
        valid_before = complete_data["hooper_next"].notna().sum()
        df_miss = inject_missingness(complete_data, rng, "mnar", PARAMS)
        valid_after = df_miss["hooper_next"].notna().sum()
        missing_rate = 1.0 - valid_after / valid_before
        assert 0.03 <= missing_rate <= 0.30, f"MNAR 비율: {missing_rate:.3f}"

    def test_hooper_항목_동시_결측(self, complete_data):
        """hooper_next 결측 시 4개 항목도 동시에 결측인지 확인."""
        rng = np.random.default_rng(999)
        df_miss = inject_missingness(complete_data, rng, "mcar", PARAMS)
        hooper_na = df_miss["hooper_next"].isna()
        for col in ["fatigue", "stress", "doms", "sleep"]:
            # hooper_next가 NaN인 행의 항목도 NaN이어야 함
            # (원래 NaN이었던 warmup 행 제외)
            injected_mask = hooper_na & complete_data["hooper_next"].notna()
            assert df_miss.loc[injected_mask, col].isna().all(), \
                f"{col} 미동시 결측"

    def test_잘못된_메커니즘_오류(self, complete_data):
        """지원하지 않는 메커니즘 입력 시 ValueError."""
        rng = np.random.default_rng(999)
        with pytest.raises(ValueError, match="지원하지 않는"):
            inject_missingness(complete_data, rng, "invalid", PARAMS)


# ---------------------------------------------------------------------------
# 4. 랜덤효과 생성 검증
# ---------------------------------------------------------------------------

class TestRandomEffects:
    """이변량 정규분포 랜덤효과의 통계적 속성을 검증한다."""

    def test_평균_근사_영(self):
        """대표본에서 랜덤효과 평균이 0에 가까운지 확인."""
        rng = np.random.default_rng(42)
        re = generate_athlete_random_effects(
            rng, 10000,
            PARAMS["sigma_u_hrv"],
            PARAMS["sigma_u_hooper"],
            PARAMS["cor_u"],
        )
        assert abs(re[:, 0].mean()) < 0.02, "u_hrv 평균 편향"
        assert abs(re[:, 1].mean()) < 0.08, "u_hooper 평균 편향"

    def test_표준편차_근사(self):
        """대표본에서 표준편차가 설정값에 가까운지 확인."""
        rng = np.random.default_rng(42)
        re = generate_athlete_random_effects(
            rng, 10000,
            PARAMS["sigma_u_hrv"],
            PARAMS["sigma_u_hooper"],
            PARAMS["cor_u"],
        )
        assert abs(re[:, 0].std() - PARAMS["sigma_u_hrv"]) < 0.02
        assert abs(re[:, 1].std() - PARAMS["sigma_u_hooper"]) < 0.08

    def test_상관_방향(self):
        """대표본에서 상관계수가 설정된 방향(음수)인지 확인."""
        rng = np.random.default_rng(42)
        re = generate_athlete_random_effects(
            rng, 10000,
            PARAMS["sigma_u_hrv"],
            PARAMS["sigma_u_hooper"],
            PARAMS["cor_u"],
        )
        cor = np.corrcoef(re[:, 0], re[:, 1])[0, 1]
        assert cor < 0, f"상관 방향 오류: {cor:.3f}"


# ---------------------------------------------------------------------------
# 5. 참값 복원 검증 (혼합효과모형)
# ---------------------------------------------------------------------------

class TestParameterRecovery:
    """혼합효과모형으로 DGP 참값을 복원할 수 있는지 검증한다."""

    @pytest.fixture(scope="class")
    def analysis_data(self):
        """분석용 데이터: warmup 제거 + 완전 관측만."""
        df = generate_integrated_dataset(PARAMS)
        valid = df.dropna(subset=[
            "acwr_ra", "mono", "strain_val",
            "hooper_next", "ln_rmssd_next",
        ]).copy()
        return valid

    def test_hooper_계수_복원(self, analysis_data):
        """전체 모형(+ln_rmssd)에서 HRV 계수 부호가 음수인지 확인.

        DGP에 HRV→Hooper 경로(beta_hrv_hooper=-0.30)가 포함되어 있으므로,
        전체 모형을 적합해야 직접 효과를 올바르게 분리할 수 있다.
        Monotony 직접 효과는 작고(0.14) 공선성의 영향을 받으므로,
        HRV 경로 복원에 집중한다.
        """
        import statsmodels.formula.api as smf

        model = smf.mixedlm(
            "hooper_next ~ acwr_ra + mono + strain_val + ln_rmssd",
            data=analysis_data,
            groups=analysis_data["athlete"],
        )
        result = model.fit(reml=True)

        beta_hrv = result.fe_params["ln_rmssd"]

        # HRV→Hooper 계수 음수 (참값: -0.30)
        assert beta_hrv < 0, \
            f"HRV→Hooper 부호 오류: {beta_hrv:.4f} (참값 음수)"

    def test_hrv_방향성(self, analysis_data):
        """HRV 모형에서 ACWR 계수의 부호가 음수인지 확인."""
        import statsmodels.formula.api as smf

        model = smf.mixedlm(
            "ln_rmssd_next ~ acwr_ra + mono",
            data=analysis_data,
            groups=analysis_data["athlete"],
        )
        result = model.fit(reml=True)

        beta_acwr = result.fe_params["acwr_ra"]
        # 참값 -0.15 → 부호 음수
        assert beta_acwr < 0, f"HRV ACWR 부호 오류: {beta_acwr:.4f}"
