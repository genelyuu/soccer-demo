"""
HRV (심박 변이도) 시간 영역 지표 산출 모듈.

SDNN, rMSSD, ln(rMSSD) 및 ln(rMSSD) 7일 Rolling Average를 계산한다.
수식 정의: docs/METRICS_FORMULAS.md 참조.
근거: Task Force (1996) [Ref #22].
"""

from typing import Optional

import numpy as np
import pandas as pd


def sdnn(nn_intervals: np.ndarray, min_count: int = 150) -> Optional[float]:
    """
    SDNN (Standard Deviation of NN intervals)을 계산한다.

    SDNN = sqrt( (1/(N-1)) * sum((NN_i - mean(NN))^2) )

    규칙:
    - 유효 NN 간격이 min_count(기본 150개) 미만이면 None을 반환한다.

    Parameters
    ----------
    nn_intervals : np.ndarray
        NN(Normal-to-Normal) R-R 간격 배열 (단위: ms).
    min_count : int, optional
        최소 유효 NN 간격 수 (기본값 150).

    Returns
    -------
    float | None
        SDNN 값 (ms). 데이터 부족 시 None.
    """
    # NaN 제거
    valid = nn_intervals[~np.isnan(nn_intervals)]

    if len(valid) < min_count:
        return None

    # 표본 표준편차 (ddof=1)
    return float(np.std(valid, ddof=1))


def rmssd(nn_intervals: np.ndarray, min_count: int = 150) -> Optional[float]:
    """
    rMSSD (Root Mean Square of Successive Differences)를 계산한다.

    rMSSD = sqrt( (1/(N-1)) * sum((NN_{i+1} - NN_i)^2) )

    규칙:
    - 유효 NN 간격이 min_count(기본 150개) 미만이면 None을 반환한다.

    Parameters
    ----------
    nn_intervals : np.ndarray
        NN 간격 배열 (단위: ms).
    min_count : int, optional
        최소 유효 NN 간격 수 (기본값 150).

    Returns
    -------
    float | None
        rMSSD 값 (ms). 데이터 부족 시 None.
    """
    valid = nn_intervals[~np.isnan(nn_intervals)]

    if len(valid) < min_count:
        return None

    # 인접 간격 차이 계산
    diffs = np.diff(valid)

    # rMSSD = sqrt( mean( diffs^2 ) ) — 수식 문서에 1/(N-1)이지만
    # N-1은 diff 개수이므로 mean(diffs^2)와 동일
    return float(np.sqrt(np.mean(diffs ** 2)))


def ln_rmssd(nn_intervals: np.ndarray, min_count: int = 150) -> Optional[float]:
    """
    ln(rMSSD) — rMSSD의 자연 로그 변환값을 계산한다.

    분포 정규화 및 변이 계수 감소를 위해 사용된다 (Plews et al., 2013).

    규칙:
    - rMSSD가 None이면 None을 반환한다.
    - rMSSD <= 0 이면 None을 반환한다 (로그 정의역 위반).

    Parameters
    ----------
    nn_intervals : np.ndarray
        NN 간격 배열 (단위: ms).
    min_count : int, optional
        최소 유효 NN 간격 수 (기본값 150).

    Returns
    -------
    float | None
        ln(rMSSD) 값. 데이터 부족 또는 rMSSD <= 0 시 None.
    """
    val = rmssd(nn_intervals, min_count=min_count)

    if val is None or val <= 0:
        return None

    return float(np.log(val))


def ln_rmssd_rolling(daily_ln_rmssd: pd.Series, window: int = 7) -> pd.Series:
    """
    ln(rMSSD)의 7일 Rolling Average를 계산한다.

    ln_rMSSD_7d(t) = (1/7) * sum(ln_rMSSD(t-i), i=0..6)

    일상적 변동을 완화하고 추세를 파악하기 위해 사용된다.

    Parameters
    ----------
    daily_ln_rmssd : pd.Series
        일별 ln(rMSSD) 시계열.
    window : int, optional
        Rolling 윈도우 크기 (기본값 7).

    Returns
    -------
    pd.Series
        ln(rMSSD) Rolling Average 시계열. 윈도우 미만 구간은 NaN.
    """
    return daily_ln_rmssd.rolling(window=window, min_periods=window).mean()
