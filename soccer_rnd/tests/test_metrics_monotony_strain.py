"""
Monotony, Strain, sRPE, Hooper Index 및 HRV 지표 단위 테스트.

훈련 단조성/부담 지표, 주관적 부하, HRV 시간 영역 지표의 산출 로직을 검증한다.
"""

import numpy as np
import pandas as pd
import pytest

from src.metrics.monotony_strain import (
    hooper_index,
    monotony,
    srpe,
    strain,
)
from src.metrics.hrv_features import (
    ln_rmssd,
    rmssd,
    sdnn,
)


# ---------------------------------------------------------------------------
# Monotony 테스트
# ---------------------------------------------------------------------------

class TestMonotony:
    """Monotony 산출 테스트 모음."""

    def test_동일_부하이면_sd_0이므로_cap_적용(self):
        """7일 동일 부하 → sd=0 → cap(10.0) 적용."""
        loads = pd.Series([500.0] * 10)
        result = monotony(loads, window=7, cap=10.0)

        # 인덱스 6(7일째)부터 유효, sd=0이므로 cap=10.0
        assert result.iloc[6] == pytest.approx(10.0)

    def test_사용자_정의_cap(self):
        """cap 값을 변경하면 해당 값이 반영되어야 한다."""
        loads = pd.Series([300.0] * 7)
        result = monotony(loads, window=7, cap=5.0)

        assert result.iloc[6] == pytest.approx(5.0)

    def test_변동_있는_부하의_monotony(self):
        """변동이 있는 부하의 Monotony를 직접 계산하여 비교한다."""
        # 7일: [100, 200, 300, 400, 500, 600, 700]
        loads = pd.Series([100, 200, 300, 400, 500, 600, 700], dtype=float)
        result = monotony(loads, window=7)

        expected_mean = 400.0
        expected_std = np.std([100, 200, 300, 400, 500, 600, 700], ddof=1)
        expected_monotony = expected_mean / expected_std

        assert result.iloc[6] == pytest.approx(expected_monotony, rel=1e-6)

    def test_결측_2일_이상이면_nan(self):
        """7일 윈도우 내 결측이 2일 이상이면 NaN."""
        loads = pd.Series([100.0, np.nan, np.nan, 400.0, 500.0, 600.0, 700.0])
        result = monotony(loads, window=7)

        # 유효값 5개 < min_valid(6) → NaN
        assert np.isnan(result.iloc[6])


# ---------------------------------------------------------------------------
# Strain 테스트
# ---------------------------------------------------------------------------

class TestStrain:
    """Strain 산출 테스트 모음."""

    def test_기본_strain_계산(self):
        """Strain = WeeklyLoad * Monotony 공식을 직접 검증한다."""
        loads = pd.Series([100, 200, 300, 400, 500, 600, 700], dtype=float)
        result = strain(loads, window=7)

        weekly_load = sum([100, 200, 300, 400, 500, 600, 700])
        expected_mean = 400.0
        expected_std = np.std([100, 200, 300, 400, 500, 600, 700], ddof=1)
        expected_monotony = expected_mean / expected_std
        expected_strain = weekly_load * expected_monotony

        assert result.iloc[6] == pytest.approx(expected_strain, rel=1e-6)

    def test_monotony_nan이면_strain도_nan(self):
        """Monotony가 NaN이면 Strain도 NaN이어야 한다."""
        # 결측 3개 → monotony NaN → strain NaN
        loads = pd.Series([np.nan, np.nan, np.nan, 400.0, 500.0, 600.0, 700.0])
        result = strain(loads, window=7)

        assert np.isnan(result.iloc[6])


# ---------------------------------------------------------------------------
# sRPE 테스트
# ---------------------------------------------------------------------------

class TestSrpe:
    """sRPE 산출 테스트 모음."""

    def test_기본_계산(self):
        """sRPE = RPE * Duration."""
        rpe_vals = pd.Series([5.0, 7.0, 3.0])
        dur_vals = pd.Series([60.0, 90.0, 45.0])
        result = srpe(rpe_vals, dur_vals)

        assert result.iloc[0] == pytest.approx(300.0)
        assert result.iloc[1] == pytest.approx(630.0)
        assert result.iloc[2] == pytest.approx(135.0)

    def test_rpe_결측이면_nan(self):
        """RPE가 결측이면 sRPE는 NaN."""
        rpe_vals = pd.Series([np.nan, 7.0])
        dur_vals = pd.Series([60.0, 90.0])
        result = srpe(rpe_vals, dur_vals)

        assert np.isnan(result.iloc[0])
        assert result.iloc[1] == pytest.approx(630.0)

    def test_duration_결측이면_nan(self):
        """Duration이 결측이면 sRPE는 NaN."""
        rpe_vals = pd.Series([5.0, 7.0])
        dur_vals = pd.Series([60.0, np.nan])
        result = srpe(rpe_vals, dur_vals)

        assert result.iloc[0] == pytest.approx(300.0)
        assert np.isnan(result.iloc[1])


# ---------------------------------------------------------------------------
# Hooper Index 테스트
# ---------------------------------------------------------------------------

class TestHooperIndex:
    """Hooper Index 산출 테스트 모음."""

    def test_기본_합산(self):
        """4개 항목의 정상적인 합산을 검증한다."""
        fatigue = pd.Series([3.0, 5.0])
        stress = pd.Series([2.0, 4.0])
        doms = pd.Series([4.0, 6.0])
        sleep = pd.Series([3.0, 7.0])

        result = hooper_index(fatigue, stress, doms, sleep)

        # 3+2+4+3=12, 5+4+6+7=22
        assert result.iloc[0] == pytest.approx(12.0)
        assert result.iloc[1] == pytest.approx(22.0)

    def test_하나라도_결측이면_nan(self):
        """4개 항목 중 1개라도 결측이면 Hooper Index = NaN."""
        fatigue = pd.Series([3.0, np.nan])
        stress = pd.Series([2.0, 4.0])
        doms = pd.Series([4.0, 6.0])
        sleep = pd.Series([3.0, 7.0])

        result = hooper_index(fatigue, stress, doms, sleep)

        assert result.iloc[0] == pytest.approx(12.0)
        assert np.isnan(result.iloc[1])

    def test_전부_결측이면_nan(self):
        """모든 항목이 결측이면 NaN."""
        s = pd.Series([np.nan])
        result = hooper_index(s, s, s, s)

        assert np.isnan(result.iloc[0])


# ---------------------------------------------------------------------------
# HRV: rMSSD / SDNN 최소 카운트 테스트
# ---------------------------------------------------------------------------

class TestHrvMinCount:
    """HRV 지표의 최소 데이터 카운트 검증."""

    def test_sdnn_150개_미만이면_none(self):
        """유효 NN 간격이 150개 미만이면 SDNN = None."""
        nn = np.random.normal(800, 50, size=100)  # 100개 < 150
        assert sdnn(nn, min_count=150) is None

    def test_sdnn_150개_이상이면_유효(self):
        """유효 NN 간격이 150개 이상이면 SDNN은 float을 반환한다."""
        nn = np.random.normal(800, 50, size=200)
        result = sdnn(nn, min_count=150)

        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    def test_rmssd_150개_미만이면_none(self):
        """유효 NN 간격이 150개 미만이면 rMSSD = None."""
        nn = np.random.normal(800, 50, size=149)
        assert rmssd(nn, min_count=150) is None

    def test_rmssd_150개_이상이면_유효(self):
        """유효 NN 간격이 150개 이상이면 rMSSD은 float을 반환한다."""
        nn = np.random.normal(800, 50, size=200)
        result = rmssd(nn, min_count=150)

        assert result is not None
        assert isinstance(result, float)
        assert result > 0

    def test_ln_rmssd_150개_미만이면_none(self):
        """유효 NN 간격이 150개 미만이면 ln(rMSSD) = None."""
        nn = np.random.normal(800, 50, size=100)
        assert ln_rmssd(nn, min_count=150) is None

    def test_ln_rmssd_정상_계산(self):
        """150개 이상인 경우 ln(rMSSD) = ln(rMSSD값)."""
        nn = np.random.normal(800, 50, size=200)
        result = ln_rmssd(nn, min_count=150)

        assert result is not None
        assert isinstance(result, float)

        # rmssd 값의 자연로그와 일치해야 한다
        rmssd_val = rmssd(nn, min_count=150)
        assert result == pytest.approx(np.log(rmssd_val))

    def test_sdnn_수치_정확성(self):
        """알려진 배열에 대해 SDNN을 직접 계산하여 비교한다."""
        nn = np.array([800.0, 810.0, 790.0, 805.0, 795.0] * 40)  # 200개
        result = sdnn(nn, min_count=150)

        expected = float(np.std(nn, ddof=1))
        assert result == pytest.approx(expected, rel=1e-6)

    def test_rmssd_수치_정확성(self):
        """알려진 배열에 대해 rMSSD를 직접 계산하여 비교한다."""
        nn = np.array([800.0, 810.0, 790.0, 805.0, 795.0] * 40)  # 200개
        result = rmssd(nn, min_count=150)

        diffs = np.diff(nn)
        expected = float(np.sqrt(np.mean(diffs ** 2)))
        assert result == pytest.approx(expected, rel=1e-6)

    def test_nan_포함_배열은_nan_제외_후_카운트(self):
        """NaN이 포함된 배열에서 NaN을 제외한 유효 간격 수로 판단한다."""
        # 160개 유효 + 40개 NaN = 200개 총합이지만 유효는 160개
        valid_part = np.random.normal(800, 50, size=160)
        nan_part = np.full(40, np.nan)
        nn = np.concatenate([valid_part, nan_part])

        # 160 >= 150 이므로 유효
        assert sdnn(nn, min_count=150) is not None

        # 유효 간격을 150 미만으로 만들면 None
        nn_few = np.concatenate([np.random.normal(800, 50, size=100),
                                  np.full(100, np.nan)])
        assert sdnn(nn_few, min_count=150) is None
