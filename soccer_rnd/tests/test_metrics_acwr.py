"""
ACWR 모듈 단위 테스트.

ATL/CTL Rolling·EWMA 및 ACWR 산출 로직을 검증한다.
"""

import numpy as np
import pandas as pd
import pytest

from src.metrics.acwr import (
    acwr_ewma,
    acwr_rolling,
    atl_ewma,
    atl_rolling,
    ctl_rolling,
)


# ---------------------------------------------------------------------------
# ATL Rolling 정확성 테스트
# ---------------------------------------------------------------------------

class TestAtlRolling:
    """ATL Rolling Average 테스트 모음."""

    def test_동일_부하_7일이면_atl은_부하값과_같다(self):
        """7일 동안 동일한 부하(500)를 넣으면 ATL = 500."""
        loads = pd.Series([500.0] * 7)
        result = atl_rolling(loads, window=7)

        # 인덱스 6(7번째 날)에서 최초 유효값
        assert result.iloc[6] == pytest.approx(500.0)

    def test_7일_미만은_nan(self):
        """윈도우(7일) 미만 구간은 NaN이어야 한다."""
        loads = pd.Series([100.0] * 10)
        result = atl_rolling(loads, window=7)

        # 인덱스 0~5(6일차까지)는 NaN
        for i in range(6):
            assert np.isnan(result.iloc[i]), f"인덱스 {i}에서 NaN이 아님"

        # 인덱스 6부터는 유효값
        assert not np.isnan(result.iloc[6])

    def test_수치_정확성(self):
        """간단한 수열의 ATL Rolling을 직접 계산하여 비교한다."""
        loads = pd.Series([100, 200, 300, 400, 500, 600, 700, 800, 900, 1000],
                          dtype=float)
        result = atl_rolling(loads, window=7)

        # 인덱스 6: mean(100..700) = 400.0
        assert result.iloc[6] == pytest.approx(400.0)
        # 인덱스 7: mean(200..800) = 500.0
        assert result.iloc[7] == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# ATL EWMA 초기값 테스트
# ---------------------------------------------------------------------------

class TestAtlEwma:
    """ATL EWMA 테스트 모음."""

    def test_초기값은_첫날_부하와_같다(self):
        """EWMA(1) = Load(1) 규칙 검증."""
        loads = pd.Series([350.0, 400.0, 450.0])
        result = atl_ewma(loads, span=7)

        assert result.iloc[0] == pytest.approx(350.0)

    def test_ewma_감쇠_방향(self):
        """부하가 증가하면 EWMA도 증가 방향이어야 한다."""
        loads = pd.Series([100.0] * 5 + [500.0] * 5)
        result = atl_ewma(loads, span=7)

        # 뒤쪽(고부하 구간)이 앞쪽보다 크다
        assert result.iloc[9] > result.iloc[4]

    def test_ewma_수치_계산(self):
        """alpha=0.25 (span=7)로 2일차 값을 직접 검증한다."""
        loads = pd.Series([100.0, 200.0])
        result = atl_ewma(loads, span=7)

        # EWMA(2) = 200*0.25 + 100*0.75 = 125.0
        assert result.iloc[1] == pytest.approx(125.0)


# ---------------------------------------------------------------------------
# CTL Rolling Warm-up 테스트
# ---------------------------------------------------------------------------

class TestCtlRolling:
    """CTL Rolling Average 테스트 모음."""

    def test_28일_미만은_nan(self):
        """CTL Rolling은 28일 미만 구간에서 NaN을 반환해야 한다."""
        loads = pd.Series([100.0] * 30)
        result = ctl_rolling(loads, window=28)

        # 인덱스 0~26(27일차까지)은 NaN
        for i in range(27):
            assert np.isnan(result.iloc[i]), f"인덱스 {i}에서 NaN이 아님"

        # 인덱스 27(28일차)부터 유효
        assert not np.isnan(result.iloc[27])

    def test_28일_동일_부하(self):
        """28일 동일 부하면 CTL = 해당 부하값."""
        loads = pd.Series([300.0] * 28)
        result = ctl_rolling(loads, window=28)

        assert result.iloc[27] == pytest.approx(300.0)


# ---------------------------------------------------------------------------
# ACWR CTL=0 → None 테스트
# ---------------------------------------------------------------------------

class TestAcwrRolling:
    """ACWR Rolling 테스트 모음."""

    def test_ctl_0이면_acwr은_nan(self):
        """CTL=0일 때 ACWR은 NaN(None)이어야 한다 (division by zero 방지)."""
        # 28일 전부 0 → CTL=0
        loads = pd.Series([0.0] * 28)
        result = acwr_rolling(loads, atl_window=7, ctl_window=28)

        # 마지막 값은 CTL=0이므로 NaN이어야 함
        assert np.isnan(result.iloc[-1])

    def test_warmup_기간은_nan(self):
        """Rolling ACWR은 CTL 윈도우(28일) 미만에서 NaN이어야 한다."""
        loads = pd.Series([100.0] * 30)
        result = acwr_rolling(loads, atl_window=7, ctl_window=28)

        # 인덱스 0~26은 NaN (CTL rolling이 NaN이므로)
        for i in range(27):
            assert np.isnan(result.iloc[i]), f"인덱스 {i}에서 NaN이 아님"

    def test_동일_부하_acwr_1(self):
        """동일 부하 28일이면 ATL=CTL이므로 ACWR=1.0."""
        loads = pd.Series([200.0] * 35)
        result = acwr_rolling(loads, atl_window=7, ctl_window=28)

        # 28일째(인덱스 27)부터 유효, ACWR=1.0
        assert result.iloc[27] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# ACWR EWMA Warm-up 테스트
# ---------------------------------------------------------------------------

class TestAcwrEwma:
    """ACWR EWMA 테스트 모음."""

    def test_warmup_21일_미만은_nan(self):
        """EWMA ACWR은 warmup(21일) 미만에서 NaN이어야 한다."""
        loads = pd.Series([100.0] * 30)
        result = acwr_ewma(loads, atl_span=7, ctl_span=28, warmup=21)

        # 인덱스 0~20(21일 미만)은 NaN
        for i in range(21):
            assert np.isnan(result.iloc[i]), f"인덱스 {i}에서 NaN이 아님"

        # 인덱스 21부터 유효
        assert not np.isnan(result.iloc[21])

    def test_ctl_ewma_0이면_nan(self):
        """CTL EWMA가 0인 경우 ACWR은 NaN이어야 한다."""
        # 모든 부하 0 → ATL=CTL=0
        loads = pd.Series([0.0] * 30)
        result = acwr_ewma(loads, warmup=21)

        # warmup 이후라도 CTL=0이므로 NaN
        assert np.isnan(result.iloc[25])

    def test_동일_부하_ewma_acwr_근사_1(self):
        """동일 부하로 충분히 긴 기간 → ACWR EWMA ≈ 1.0."""
        loads = pd.Series([100.0] * 60)
        result = acwr_ewma(loads, warmup=21)

        # 충분히 수렴한 후 ACWR ≈ 1.0
        assert result.iloc[50] == pytest.approx(1.0, abs=0.01)
