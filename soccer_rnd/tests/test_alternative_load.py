"""
대안 부하 지표 모듈 단위 테스트.

DCWR, TSB, ACWR Uncoupled 및 compare_load_metrics 함수의 정확성을 검증한다.
"""

import numpy as np
import pandas as pd
import pytest

from src.metrics.alternative_load import (
    acwr_uncoupled,
    compare_load_metrics,
    dcwr_ewma,
    dcwr_rolling,
    tsb_ewma,
    tsb_rolling,
)


# ---------------------------------------------------------------------------
# DCWR Rolling 테스트
# ---------------------------------------------------------------------------

class TestDcwrRolling:
    """DCWR Rolling Average 테스트 모음."""

    def test_동일_부하이면_dcwr은_0(self):
        """동일 부하를 충분히 오래 입력하면 ATL=CTL이므로 DCWR=0이어야 한다."""
        loads = pd.Series([500.0] * 35)
        result = dcwr_rolling(loads)

        # ctl_window(28일) 이후부터 유효, ATL=CTL=500이므로 DCWR=0
        valid_values = result.dropna()
        for val in valid_values:
            assert val == pytest.approx(0.0), (
                f"동일 부하에서 DCWR이 0이 아님: {val}"
            )

    def test_부하_급등_구간에서_dcwr_양수(self):
        """
        만성 기간에 낮은 부하, 급성 기간에 높은 부하를 넣으면
        ATL > CTL이므로 DCWR > 0이어야 한다.
        """
        # 28일 동안 낮은 부하(100) 후 7일 동안 높은 부하(800)
        loads = pd.Series([100.0] * 28 + [800.0] * 7)
        result = dcwr_rolling(loads)

        # 마지막 값: ATL=800, CTL에는 아직 100 비중이 높으므로 DCWR > 0
        last_valid = result.iloc[-1]
        assert not np.isnan(last_valid), "마지막 값이 NaN"
        assert last_valid > 0, (
            f"부하 급등 구간에서 DCWR이 양수가 아님: {last_valid}"
        )

    def test_ctl_window_미만은_nan(self):
        """ctl_window(28일) 미만 구간은 NaN이어야 한다."""
        loads = pd.Series([300.0] * 35)
        result = dcwr_rolling(loads)

        # 인덱스 0~26(27일차까지)은 NaN (CTL rolling이 NaN이므로)
        for i in range(27):
            assert np.isnan(result.iloc[i]), f"인덱스 {i}에서 NaN이 아님"


# ---------------------------------------------------------------------------
# DCWR EWMA 테스트
# ---------------------------------------------------------------------------

class TestDcwrEwma:
    """DCWR EWMA 테스트 모음."""

    def test_동일_부하_충분히_길면_dcwr_근사_0(self):
        """
        동일 부하를 충분히 오래 입력하면 EWMA 기반 ATL과 CTL이 수렴하여
        DCWR ≈ 0 이어야 한다.
        """
        loads = pd.Series([400.0] * 100)
        result = dcwr_ewma(loads)

        # 충분히 수렴한 후반부에서 DCWR ≈ 0
        assert result.iloc[-1] == pytest.approx(0.0, abs=0.5), (
            f"수렴 후 DCWR EWMA가 0에 가깝지 않음: {result.iloc[-1]}"
        )


# ---------------------------------------------------------------------------
# TSB 테스트
# ---------------------------------------------------------------------------

class TestTsbRolling:
    """TSB Rolling 테스트 모음."""

    def test_tsb는_dcwr의_부호_반전(self):
        """TSB = -DCWR 관계를 검증한다. (TSB = CTL - ATL = -(ATL - CTL) = -DCWR)"""
        loads = pd.Series([100.0] * 21 + [500.0] * 14)
        result_tsb = tsb_rolling(loads)
        result_dcwr = dcwr_rolling(loads)

        # 유효한 값(NaN이 아닌)에 대해 TSB = -DCWR 확인
        valid_mask = result_tsb.notna() & result_dcwr.notna()
        tsb_vals = result_tsb[valid_mask]
        dcwr_vals = result_dcwr[valid_mask]

        for tsb_val, dcwr_val in zip(tsb_vals, dcwr_vals):
            assert tsb_val == pytest.approx(-dcwr_val), (
                f"TSB({tsb_val}) != -DCWR({dcwr_val})"
            )

    def test_부하_급등_구간에서_tsb_음수(self):
        """
        만성 기간에 낮은 부하, 급성 기간에 높은 부하를 넣으면
        피로 > 체력이므로 TSB < 0이어야 한다.
        """
        # 28일 동안 낮은 부하(100) 후 7일 동안 높은 부하(800)
        loads = pd.Series([100.0] * 28 + [800.0] * 7)
        result = tsb_rolling(loads)

        # 마지막 값: CTL에 100 비중이 높고 ATL=800이므로 TSB < 0
        last_valid = result.iloc[-1]
        assert not np.isnan(last_valid), "마지막 값이 NaN"
        assert last_valid < 0, (
            f"부하 급등 구간에서 TSB가 음수가 아님: {last_valid}"
        )


class TestTsbEwma:
    """TSB EWMA 테스트 모음."""

    def test_tsb_ewma는_dcwr_ewma의_부호_반전(self):
        """TSB EWMA = -DCWR EWMA 관계를 검증한다."""
        loads = pd.Series([200.0] * 10 + [600.0] * 20)
        result_tsb = tsb_ewma(loads)
        result_dcwr = dcwr_ewma(loads)

        for i in range(len(result_tsb)):
            assert result_tsb.iloc[i] == pytest.approx(-result_dcwr.iloc[i]), (
                f"인덱스 {i}: TSB EWMA({result_tsb.iloc[i]}) != "
                f"-DCWR EWMA({result_dcwr.iloc[i]})"
            )


# ---------------------------------------------------------------------------
# ACWR Uncoupled 테스트
# ---------------------------------------------------------------------------

class TestAcwrUncoupled:
    """ACWR Uncoupled (비결합) 테스트 모음."""

    def test_warmup_기간은_nan(self):
        """
        ACWR Uncoupled는 ctl_window + atl_window(28+7=35일) 미만에서
        NaN이어야 한다. CTL이 atl_window만큼 shift되므로 유효값 시작이 늦어진다.
        """
        loads = pd.Series([100.0] * 50)
        result = acwr_uncoupled(loads, atl_window=7, ctl_window=28)

        # CTL rolling은 인덱스 27부터 유효, shift(7)이므로 인덱스 34부터 유효
        # ATL rolling은 인덱스 6부터 유효
        # 따라서 둘 다 유효한 최초 인덱스는 34 (= 27 + 7)
        for i in range(34):
            assert np.isnan(result.iloc[i]), (
                f"인덱스 {i}에서 NaN이 아님: {result.iloc[i]}"
            )

        # 인덱스 34부터는 유효
        assert not np.isnan(result.iloc[34]), (
            f"인덱스 34에서 유효값이어야 하지만 NaN"
        )

    def test_ctl_0이면_nan(self):
        """shifted CTL이 0이면 ACWR Uncoupled는 NaN이어야 한다."""
        # 앞 28일은 0 (CTL=0), 이후 부하 발생
        # shift(7)이므로 실제 CTL_shifted가 0인 구간이 더 길어짐
        loads = pd.Series([0.0] * 35 + [500.0] * 7)
        result = acwr_uncoupled(loads)

        # 인덱스 34: CTL_shifted는 인덱스 27의 CTL = 0이므로 NaN
        assert np.isnan(result.iloc[34]), (
            f"CTL=0인데 NaN이 아님: {result.iloc[34]}"
        )

    def test_동일_부하_uncoupled_acwr_1(self):
        """동일 부하를 충분히 넣으면 ACWR Uncoupled ≈ 1.0."""
        loads = pd.Series([300.0] * 50)
        result = acwr_uncoupled(loads)

        # 인덱스 34 이후부터 유효, 동일 부하이므로 ATL=CTL → ACWR=1.0
        assert result.iloc[40] == pytest.approx(1.0), (
            f"동일 부하에서 ACWR Uncoupled이 1.0이 아님: {result.iloc[40]}"
        )


# ---------------------------------------------------------------------------
# compare_load_metrics 테스트
# ---------------------------------------------------------------------------

class TestCompareLoadMetrics:
    """compare_load_metrics 함수 테스트 모음."""

    def test_기본_7개_지표_컬럼_존재(self):
        """metrics=None이면 7개 기본 지표 컬럼이 모두 존재해야 한다."""
        loads = pd.Series([200.0] * 50)
        result = compare_load_metrics(loads)

        expected_columns = [
            "acwr_rolling",
            "acwr_ewma",
            "dcwr_rolling",
            "dcwr_ewma",
            "tsb_rolling",
            "tsb_ewma",
            "acwr_uncoupled",
        ]
        for col in expected_columns:
            assert col in result.columns, f"'{col}' 컬럼이 없음"

        assert len(result.columns) == 7, (
            f"컬럼 수가 7이 아님: {len(result.columns)}"
        )

    def test_지원하지_않는_지표_요청시_에러(self):
        """존재하지 않는 지표명을 넣으면 ValueError가 발생해야 한다."""
        loads = pd.Series([200.0] * 50)

        with pytest.raises(ValueError, match="지원하지 않는 지표"):
            compare_load_metrics(loads, metrics=["acwr_rolling", "없는_지표"])

    def test_선택적_지표_산출(self):
        """metrics에 일부 지표만 지정하면 해당 컬럼만 반환해야 한다."""
        loads = pd.Series([200.0] * 50)
        result = compare_load_metrics(
            loads, metrics=["dcwr_rolling", "tsb_rolling"]
        )

        assert list(result.columns) == ["dcwr_rolling", "tsb_rolling"]
        assert len(result) == len(loads)
