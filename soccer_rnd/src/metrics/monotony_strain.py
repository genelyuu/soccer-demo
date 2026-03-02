"""
Monotony, Strain, sRPE, Hooper Index 지표 산출 모듈.

Foster(1998) 기반의 훈련 단조성/부담 지표 및 주관적 부하/웰니스 지표를 계산한다.
수식 정의: docs/METRICS_FORMULAS.md 참조.
"""

import numpy as np
import pandas as pd


def monotony(loads: pd.Series, window: int = 7, cap: float = 10.0) -> pd.Series:
    """
    7일 윈도우 기반 Monotony(훈련 단조성)를 계산한다.

    Monotony(t) = mean(Load(t-6..t)) / sd(Load(t-6..t))
    sd는 표본 표준편차(ddof=1)를 사용한다.

    규칙:
    - sd = 0 이면 cap 값(기본 10.0)으로 대체한다.
    - 7일 윈도우 내 결측이 2일 이상이면 NaN.
      (min_periods = window - 1, 즉 최소 6개의 유효값 필요)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    window : int, optional
        윈도우 크기 (기본값 7).
    cap : float, optional
        sd=0일 때 적용할 상한값 (기본값 10.0).

    Returns
    -------
    pd.Series
        Monotony 시계열.
    """
    # 결측 2일 이상이면 NaN → 유효값이 (window - 1) 이상 필요
    min_valid = window - 1

    roll_mean = loads.rolling(window=window, min_periods=min_valid).mean()
    roll_std = loads.rolling(window=window, min_periods=min_valid).std(ddof=1)

    # sd=0 → cap 처리
    result = roll_mean / roll_std
    result = result.where(roll_std != 0, cap)

    # min_periods 조건에 의해 이미 NaN인 구간은 그대로 유지
    # roll_mean 또는 roll_std가 NaN이면 result도 NaN
    mask_nan = roll_mean.isna() | roll_std.isna()
    result = result.where(~mask_nan, np.nan)

    return result


def strain(loads: pd.Series, window: int = 7, cap: float = 10.0) -> pd.Series:
    """
    7일 윈도우 기반 Strain(훈련 부담)을 계산한다.

    Strain(t) = WeeklyLoad(t) * Monotony(t)
    WeeklyLoad(t) = sum(Load(t-6..t))

    규칙:
    - Monotony = NaN 이면 Strain = NaN.
    - 7일 윈도우 내 결측 2일 이상이면 NaN.

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    window : int, optional
        윈도우 크기 (기본값 7).
    cap : float, optional
        Monotony 산출 시 sd=0에 대한 cap 값 (기본값 10.0).

    Returns
    -------
    pd.Series
        Strain 시계열.
    """
    min_valid = window - 1
    weekly_load = loads.rolling(window=window, min_periods=min_valid).sum()
    mono = monotony(loads, window=window, cap=cap)

    return weekly_load * mono


def srpe(rpe: pd.Series, duration: pd.Series) -> pd.Series:
    """
    sRPE (Session RPE)를 계산한다.

    sRPE = RPE * Duration(분)

    규칙:
    - RPE 또는 Duration 중 하나라도 결측이면 sRPE = NaN.

    Parameters
    ----------
    rpe : pd.Series
        RPE 값 시계열 (Borg CR-10, 0-10).
    duration : pd.Series
        훈련 시간(분) 시계열.

    Returns
    -------
    pd.Series
        sRPE 시계열.
    """
    # pandas 곱셈은 어느 한쪽이 NaN이면 결과도 NaN
    return rpe * duration


def hooper_index(
    fatigue: pd.Series,
    stress: pd.Series,
    doms: pd.Series,
    sleep: pd.Series,
) -> pd.Series:
    """
    Hooper Index를 계산한다.

    Hooper Index = Fatigue + Stress + DOMS + Sleep Quality
    각 항목은 1-7 스케일.

    규칙:
    - 4개 항목 중 1개라도 결측이면 Hooper Index = NaN.
      부분 합산하지 않는다.

    Parameters
    ----------
    fatigue : pd.Series
        피로도 (1-7).
    stress : pd.Series
        스트레스 (1-7).
    doms : pd.Series
        근육통 (1-7).
    sleep : pd.Series
        수면 질 (1-7).

    Returns
    -------
    pd.Series
        Hooper Index 시계열.
    """
    # pd.DataFrame으로 묶어 하나라도 NaN이면 합산 결과 NaN 유지
    df = pd.DataFrame({
        "fatigue": fatigue,
        "stress": stress,
        "doms": doms,
        "sleep": sleep,
    })
    # sum(axis=1)에서 min_count=4로 설정하면 4개 모두 유효해야 합산
    return df.sum(axis=1, min_count=4)
