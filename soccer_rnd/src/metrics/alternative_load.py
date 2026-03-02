"""
ACWR 대안 부하 지표 모듈.

Impellizzeri (2020), Wang (2020), Lolli (2019) 등의 ACWR 비판 문헌을 반영하여
비율(ratio) 기반 ACWR의 한계를 보완하는 대안 지표를 제공한다.

대안 지표 목록:
- DCWR (Differential Chronic Workload Ratio): ATL - CTL (차이 기반, division-free)
- TSB (Training Stress Balance): CTL - ATL (Banister 모형, 체력-피로 균형)
- ACWR Uncoupled: 급성 기간을 만성 기간에서 제외한 비결합 비율

참고 문헌:
- Wang et al. (2020) "분모 0 문제 없이 부하 변화를 포착하는 차이 기반 접근"
- Impellizzeri et al. (2020) "ACWR의 수학적·통계적 한계"
- Lolli et al. (2019) "결합(coupled) ACWR의 허위 상관 문제"
"""

import numpy as np
import pandas as pd

from src.metrics.acwr import (
    atl_rolling,
    atl_ewma,
    ctl_rolling,
    ctl_ewma,
    acwr_rolling as _acwr_rolling,
    acwr_ewma as _acwr_ewma,
)


# ---------------------------------------------------------------------------
# DCWR (Differential Chronic Workload Ratio) — Wang et al. (2020)
# ---------------------------------------------------------------------------

def dcwr_rolling(
    loads: pd.Series,
    atl_window: int = 7,
    ctl_window: int = 28,
) -> pd.Series:
    """
    Rolling Average 방식의 DCWR을 계산한다.

    DCWR_rolling(t) = ATL_rolling(t) - CTL_rolling(t)

    Wang et al. (2020) 제안. 비율이 아닌 차이(difference)를 사용하여
    CTL=0 일 때 발생하는 division-by-zero 문제를 근본적으로 회피한다.

    양수: 급성 부하 > 만성 부하 (부하 급등 상태)
    음수: 급성 부하 < 만성 부하 (부하 감소 상태)
    0: 급성 부하 = 만성 부하 (안정 상태)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열. 인덱스는 날짜 순서를 가정한다.
    atl_window : int, optional
        급성 부하 윈도우 크기 (기본값 7일).
    ctl_window : int, optional
        만성 부하 윈도우 크기 (기본값 28일).

    Returns
    -------
    pd.Series
        DCWR Rolling 시계열. ctl_window 미만 구간은 NaN.
    """
    atl = atl_rolling(loads, window=atl_window)
    ctl = ctl_rolling(loads, window=ctl_window)
    result = atl - ctl
    result.name = "dcwr_rolling"
    return result


def dcwr_ewma(
    loads: pd.Series,
    atl_span: int = 7,
    ctl_span: int = 28,
) -> pd.Series:
    """
    EWMA 방식의 DCWR을 계산한다.

    DCWR_ewma(t) = ATL_ewma(t) - CTL_ewma(t)

    EWMA 특성상 첫 번째 값부터 유효하지만, 초기 구간은 안정화되지
    않았으므로 해석에 주의가 필요하다.

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    atl_span : int, optional
        ATL EWMA 스팬 (기본값 7).
    ctl_span : int, optional
        CTL EWMA 스팬 (기본값 28).

    Returns
    -------
    pd.Series
        DCWR EWMA 시계열.
    """
    atl = atl_ewma(loads, span=atl_span)
    ctl = ctl_ewma(loads, span=ctl_span)
    result = atl - ctl
    result.name = "dcwr_ewma"
    return result


# ---------------------------------------------------------------------------
# TSB (Training Stress Balance) — Banister 모형 기반
# ---------------------------------------------------------------------------

def tsb_rolling(
    loads: pd.Series,
    atl_window: int = 7,
    ctl_window: int = 28,
) -> pd.Series:
    """
    Rolling Average 방식의 TSB(Training Stress Balance)를 계산한다.

    TSB_rolling(t) = CTL_rolling(t) - ATL_rolling(t)

    Banister 피트니스-피로 모형에서 유래한 지표로, DCWR의 부호를 반전한 것이다.
    양수: 체력(fitness) > 피로(fatigue) → 선수가 상쾌한(fresh) 상태
    음수: 피로(fatigue) > 체력(fitness) → 선수가 피곤한(fatigued) 상태

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    atl_window : int, optional
        급성 부하 윈도우 크기 (기본값 7일).
    ctl_window : int, optional
        만성 부하 윈도우 크기 (기본값 28일).

    Returns
    -------
    pd.Series
        TSB Rolling 시계열. ctl_window 미만 구간은 NaN.
    """
    atl = atl_rolling(loads, window=atl_window)
    ctl = ctl_rolling(loads, window=ctl_window)
    result = ctl - atl
    result.name = "tsb_rolling"
    return result


def tsb_ewma(
    loads: pd.Series,
    atl_span: int = 7,
    ctl_span: int = 28,
) -> pd.Series:
    """
    EWMA 방식의 TSB(Training Stress Balance)를 계산한다.

    TSB_ewma(t) = CTL_ewma(t) - ATL_ewma(t)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    atl_span : int, optional
        ATL EWMA 스팬 (기본값 7).
    ctl_span : int, optional
        CTL EWMA 스팬 (기본값 28).

    Returns
    -------
    pd.Series
        TSB EWMA 시계열.
    """
    atl = atl_ewma(loads, span=atl_span)
    ctl = ctl_ewma(loads, span=ctl_span)
    result = ctl - atl
    result.name = "tsb_ewma"
    return result


# ---------------------------------------------------------------------------
# ACWR Uncoupled — Lolli et al. (2019) 비판 반영
# ---------------------------------------------------------------------------

def acwr_uncoupled(
    loads: pd.Series,
    atl_window: int = 7,
    ctl_window: int = 28,
) -> pd.Series:
    """
    비결합(Uncoupled) ACWR을 계산한다.

    ACWR_uncoupled(t) = ATL_rolling(t) / CTL_rolling(t - atl_window)

    Lolli et al. (2019)가 지적한 결합(coupled) ACWR의 문제를 해결한다.
    기존 ACWR에서는 급성 기간(최근 7일)이 만성 기간(최근 28일)에 포함되어
    허위 상관(spurious correlation)이 발생한다. 비결합 방식은 만성 기간을
    atl_window만큼 과거로 이동시켜 급성 기간과 만성 기간의 중복을 제거한다.

    규칙:
    - CTL_rolling(t - atl_window) = 0 이면 NaN 처리 (division-by-zero 방지)
    - ctl_window + atl_window 미만 구간은 NaN (warm-up)

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    atl_window : int, optional
        급성 부하 윈도우 크기 (기본값 7일).
    ctl_window : int, optional
        만성 부하 윈도우 크기 (기본값 28일).

    Returns
    -------
    pd.Series
        ACWR Uncoupled 시계열.
    """
    atl = atl_rolling(loads, window=atl_window)
    ctl = ctl_rolling(loads, window=ctl_window)

    # 만성 부하를 atl_window만큼 과거로 shift하여 급성 기간과의 중복 제거
    ctl_shifted = ctl.shift(atl_window)

    # CTL=0 → NaN 처리
    ctl_safe = ctl_shifted.replace(0, np.nan)

    result = atl / ctl_safe
    result.name = "acwr_uncoupled"
    return result


# ---------------------------------------------------------------------------
# 비교 모듈: 모든 부하 지표 일괄 산출
# ---------------------------------------------------------------------------

# 지원 지표 레지스트리 (지표명 → 산출 함수 매핑)
_METRIC_REGISTRY: dict[str, callable] = {
    "acwr_rolling": lambda loads: _acwr_rolling(loads),
    "acwr_ewma": lambda loads: _acwr_ewma(loads),
    "dcwr_rolling": lambda loads: dcwr_rolling(loads),
    "dcwr_ewma": lambda loads: dcwr_ewma(loads),
    "tsb_rolling": lambda loads: tsb_rolling(loads),
    "tsb_ewma": lambda loads: tsb_ewma(loads),
    "acwr_uncoupled": lambda loads: acwr_uncoupled(loads),
}

# 기본 지표 목록 (compare_load_metrics에서 metrics=None일 때 사용)
DEFAULT_METRICS: list[str] = list(_METRIC_REGISTRY.keys())


def compare_load_metrics(
    loads: pd.Series,
    metrics: list[str] | None = None,
) -> pd.DataFrame:
    """
    여러 부하 지표를 일괄 산출하여 하나의 DataFrame으로 반환한다.

    ACWR과 대안 지표(DCWR, TSB, ACWR Uncoupled)를 동일 부하 데이터에 대해
    동시에 계산하여 직접 비교할 수 있게 한다. Impellizzeri (2020)가 권장한
    "다중 지표 병렬 비교" 접근법을 코드로 구현한 것이다.

    Parameters
    ----------
    loads : pd.Series
        일별 훈련 부하 시계열.
    metrics : list[str] | None, optional
        산출할 지표명 목록. None이면 아래 7개 지표 전부 산출:
        ['acwr_rolling', 'acwr_ewma', 'dcwr_rolling', 'dcwr_ewma',
         'tsb_rolling', 'tsb_ewma', 'acwr_uncoupled']

    Returns
    -------
    pd.DataFrame
        각 컬럼이 지표명인 DataFrame. 인덱스는 loads의 인덱스와 동일.

    Raises
    ------
    ValueError
        지원하지 않는 지표명이 포함된 경우.
    """
    if metrics is None:
        metrics = DEFAULT_METRICS

    # 유효성 검사: 지원하지 않는 지표명 확인
    unsupported = set(metrics) - set(_METRIC_REGISTRY.keys())
    if unsupported:
        raise ValueError(
            f"지원하지 않는 지표: {unsupported}. "
            f"사용 가능한 지표: {list(_METRIC_REGISTRY.keys())}"
        )

    result = pd.DataFrame(index=loads.index)
    for metric_name in metrics:
        result[metric_name] = _METRIC_REGISTRY[metric_name](loads)

    return result
