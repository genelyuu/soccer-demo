"""
ACWR (Acute:Chronic Workload Ratio) 지표 산출 모듈.

ATL(급성 훈련 부하), CTL(만성 훈련 부하), ACWR을 Rolling Average 및 EWMA 방식으로 계산한다.
수식 정의: docs/METRICS_FORMULAS.md 참조.
"""

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# ATL (Acute Training Load)
# ---------------------------------------------------------------------------

def atl_rolling(loads: pd.Series, window: int = 7) -> pd.Series:
    """
    Rolling Average 방식의 급성 훈련 부하(ATL)를 계산한다.

    ATL_rolling(t) = (1/n) * sum(Load(t-i), i=0..n-1)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열. 인덱스는 날짜 순서를 가정한다.
    window : int, optional
        급성 부하 윈도우 크기 (기본값 7일).

    Returns
    -------
    pd.Series
        ATL 시계열. 윈도우 미만 구간은 NaN.
    """
    return loads.rolling(window=window, min_periods=window).mean()


def atl_ewma(loads: pd.Series, span: int = 7) -> pd.Series:
    """
    EWMA 방식의 급성 훈련 부하(ATL)를 계산한다.

    ATL_ewma(t) = Load(t) * alpha + ATL_ewma(t-1) * (1 - alpha)
    alpha = 2 / (span + 1)
    초기값: ATL_ewma(1) = Load(1)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    span : int, optional
        EWMA 스팬 (기본값 7). alpha = 2/(span+1).

    Returns
    -------
    pd.Series
        ATL EWMA 시계열. 첫 번째 값은 Load(1)과 동일하다.
    """
    alpha = 2.0 / (span + 1)
    result = np.empty(len(loads), dtype=np.float64)

    values = loads.values.astype(np.float64)

    # 첫 번째 유효값을 초기값으로 설정
    result[0] = values[0]

    for i in range(1, len(values)):
        if np.isnan(values[i]):
            # 결측일 경우 전일 값 유지
            result[i] = result[i - 1]
        else:
            result[i] = values[i] * alpha + result[i - 1] * (1 - alpha)

    return pd.Series(result, index=loads.index, name="atl_ewma")


# ---------------------------------------------------------------------------
# CTL (Chronic Training Load)
# ---------------------------------------------------------------------------

def ctl_rolling(loads: pd.Series, window: int = 28) -> pd.Series:
    """
    Rolling Average 방식의 만성 훈련 부하(CTL)를 계산한다.

    CTL_rolling(t) = (1/n) * sum(Load(t-i), i=0..n-1)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    window : int, optional
        만성 부하 윈도우 크기 (기본값 28일).

    Returns
    -------
    pd.Series
        CTL 시계열. 윈도우 미만 구간은 NaN.
    """
    return loads.rolling(window=window, min_periods=window).mean()


def ctl_ewma(loads: pd.Series, span: int = 28) -> pd.Series:
    """
    EWMA 방식의 만성 훈련 부하(CTL)를 계산한다.

    CTL_ewma(t) = Load(t) * alpha + CTL_ewma(t-1) * (1 - alpha)
    alpha = 2 / (span + 1)
    초기값: CTL_ewma(1) = Load(1)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    span : int, optional
        EWMA 스팬 (기본값 28). alpha = 2/(span+1).

    Returns
    -------
    pd.Series
        CTL EWMA 시계열.
    """
    alpha = 2.0 / (span + 1)
    result = np.empty(len(loads), dtype=np.float64)

    values = loads.values.astype(np.float64)

    result[0] = values[0]

    for i in range(1, len(values)):
        if np.isnan(values[i]):
            result[i] = result[i - 1]
        else:
            result[i] = values[i] * alpha + result[i - 1] * (1 - alpha)

    return pd.Series(result, index=loads.index, name="ctl_ewma")


# ---------------------------------------------------------------------------
# ACWR (Acute:Chronic Workload Ratio)
# ---------------------------------------------------------------------------

def acwr_rolling(
    loads: pd.Series,
    atl_window: int = 7,
    ctl_window: int = 28,
) -> pd.Series:
    """
    Rolling Average 방식의 ACWR을 계산한다.

    ACWR_rolling(t) = ATL_rolling(t) / CTL_rolling(t)

    규칙:
    - CTL = 0 이면 ACWR = NaN (None).
    - Warm-up: ctl_window(28일) 미만 구간은 NaN.

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    atl_window : int, optional
        ATL 윈도우 (기본값 7).
    ctl_window : int, optional
        CTL 윈도우 (기본값 28).

    Returns
    -------
    pd.Series
        ACWR 시계열.
    """
    atl = atl_rolling(loads, window=atl_window)
    ctl = ctl_rolling(loads, window=ctl_window)

    # CTL=0 인 경우 NaN 처리
    ratio = atl / ctl.replace(0, np.nan)

    return ratio


def acwr_ewma(
    loads: pd.Series,
    atl_span: int = 7,
    ctl_span: int = 28,
    warmup: int = 21,
) -> pd.Series:
    """
    EWMA 방식의 ACWR을 계산한다.

    ACWR_ewma(t) = ATL_ewma(t) / CTL_ewma(t)

    규칙:
    - CTL_ewma = 0 이면 ACWR = NaN.
    - Warm-up: warmup(기본 21일) 미만 구간은 NaN.

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    atl_span : int, optional
        ATL EWMA 스팬 (기본값 7).
    ctl_span : int, optional
        CTL EWMA 스팬 (기본값 28).
    warmup : int, optional
        ACWR 산출을 위한 최소 워밍업 일수 (기본값 21).

    Returns
    -------
    pd.Series
        ACWR EWMA 시계열. warmup 기간 내 값은 NaN.
    """
    atl = atl_ewma(loads, span=atl_span)
    ctl = ctl_ewma(loads, span=ctl_span)

    # CTL=0 → NaN 처리
    ctl_safe = ctl.replace(0, np.nan)
    ratio = atl / ctl_safe

    # warmup 기간 내 값은 NaN 처리 (인덱스 0부터 warmup-1까지)
    ratio.iloc[:warmup] = np.nan

    return ratio
