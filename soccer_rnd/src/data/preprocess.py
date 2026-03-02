"""
전처리 파이프라인 모듈.

RR 간격 이상치 필터링, 일별 HRV 산출, 일별 부하 지표 일괄 산출,
시차 분석용 데이터셋 생성 기능을 제공한다.
"""

import numpy as np
import pandas as pd

from src.metrics.acwr import (
    atl_ewma,
    atl_rolling,
    ctl_ewma,
    ctl_rolling,
    acwr_ewma,
    acwr_rolling,
)
from src.metrics.monotony_strain import monotony, strain
from src.metrics.hrv_features import rmssd, sdnn, ln_rmssd


# ---------------------------------------------------------------------------
# RR 간격 이상치 필터링
# ---------------------------------------------------------------------------

def filter_rr_outliers(
    rr_series: pd.Series,
    threshold: float = 0.20,
) -> pd.Series:
    """
    RR 간격에서 중앙값 대비 ±threshold 비율을 벗어나는 값을 NaN으로 대체한다.

    Malik et al. (1996) 기반의 단순 중앙값 필터 방식이다.
    예: threshold=0.20 이면 중앙값의 80%~120% 범위 밖의 값을 이상치로 판정한다.

    Parameters
    ----------
    rr_series : pd.Series
        RR 간격 시계열 (단위: ms).
    threshold : float, optional
        중앙값 대비 허용 비율 (기본값 0.20, 즉 ±20%).

    Returns
    -------
    pd.Series
        이상치가 NaN으로 대체된 RR 간격 시계열.
    """
    median_rr = rr_series.median()
    lower_bound = median_rr * (1.0 - threshold)
    upper_bound = median_rr * (1.0 + threshold)

    filtered = rr_series.copy()
    outlier_mask = (filtered < lower_bound) | (filtered > upper_bound)
    filtered[outlier_mask] = np.nan

    return filtered


# ---------------------------------------------------------------------------
# 일별 HRV 산출 (트랙 A)
# ---------------------------------------------------------------------------

def compute_daily_hrv(
    df: pd.DataFrame,
    subject_col: str = "subject_id",
    rr_col: str = "rr_interval_ms",
    min_nn: int = 150,
) -> pd.DataFrame:
    """
    피험자·세션별 rMSSD, SDNN, ln_rMSSD를 산출한다.

    hrv_features.py 모듈의 rmssd(), sdnn(), ln_rmssd() 함수를 활용하며,
    유효 NN 간격이 min_nn 미만인 세션은 NaN으로 처리된다.

    Parameters
    ----------
    df : pd.DataFrame
        트랙 A 표준 스키마 DataFrame. 최소한 subject_col, 'session_id',
        rr_col 컬럼이 필요하다.
    subject_col : str, optional
        피험자 식별 컬럼명 (기본값 'subject_id').
    rr_col : str, optional
        RR 간격 컬럼명 (기본값 'rr_interval_ms').
    min_nn : int, optional
        HRV 산출에 필요한 최소 유효 NN 간격 수 (기본값 150).

    Returns
    -------
    pd.DataFrame
        컬럼: [subject_col, 'session_id', 'rmssd', 'sdnn', 'ln_rmssd'].
        각 피험자·세션별 한 행.
    """
    records = []

    for (subj, sess), group in df.groupby([subject_col, "session_id"]):
        nn_intervals = group[rr_col].dropna().values

        rmssd_val = rmssd(nn_intervals, min_count=min_nn)
        sdnn_val = sdnn(nn_intervals, min_count=min_nn)
        ln_rmssd_val = ln_rmssd(nn_intervals, min_count=min_nn)

        records.append({
            subject_col: subj,
            "session_id": sess,
            "rmssd": rmssd_val,
            "sdnn": sdnn_val,
            "ln_rmssd": ln_rmssd_val,
        })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 일별 부하 지표 일괄 산출 (트랙 B)
# ---------------------------------------------------------------------------

def compute_daily_load_metrics(
    df: pd.DataFrame,
    athlete_col: str = "athlete_id",
    load_col: str = "srpe",
) -> pd.DataFrame:
    """
    선수별 ATL/CTL/ACWR(Rolling+EWMA), Monotony, Strain을 일괄 산출한다.

    acwr.py 및 monotony_strain.py 모듈의 함수들을 활용한다.
    입력 DataFrame은 날짜 순으로 정렬되어 있어야 하며,
    각 선수별로 독립적으로 지표를 산출한다.

    Parameters
    ----------
    df : pd.DataFrame
        트랙 B 표준 스키마 DataFrame. 최소한 athlete_col, 'date',
        load_col 컬럼이 필요하다.
    athlete_col : str, optional
        선수 식별 컬럼명 (기본값 'athlete_id').
    load_col : str, optional
        일별 훈련 부하 컬럼명 (기본값 'srpe').

    Returns
    -------
    pd.DataFrame
        원본 DataFrame에 다음 컬럼이 추가된 결과:
        atl_rolling, ctl_rolling, acwr_rolling,
        atl_ewma, ctl_ewma, acwr_ewma,
        monotony, strain.
    """
    result_frames = []

    for athlete, group in df.groupby(athlete_col):
        group = group.sort_values("date").copy()
        loads = group[load_col]

        group["atl_rolling"] = atl_rolling(loads).values
        group["ctl_rolling"] = ctl_rolling(loads).values
        group["acwr_rolling"] = acwr_rolling(loads).values
        group["atl_ewma"] = atl_ewma(loads).values
        group["ctl_ewma"] = ctl_ewma(loads).values
        group["acwr_ewma"] = acwr_ewma(loads).values
        group["monotony"] = monotony(loads).values
        group["strain"] = strain(loads).values

        result_frames.append(group)

    if not result_frames:
        return df.copy()

    return pd.concat(result_frames, ignore_index=True)


# ---------------------------------------------------------------------------
# 시차 분석용 데이터셋 생성
# ---------------------------------------------------------------------------

def build_lagged_dataset(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_cols: list[str],
    group_col: str,
    lag: int = 1,
) -> pd.DataFrame:
    """
    그룹별 종속변수를 lag일 후행 이동(shift)하여 시차 분석용 DataFrame을 생성한다.

    예: lag=1이면 오늘의 예측 변수(X_t)로 내일의 결과(Y_{t+1})를 예측하는
    구조를 만든다. 이동 후 발생하는 NaN 행은 제거된다.

    각 그룹(선수 등)별로 독립적으로 shift를 적용하여 그룹 간 데이터 누출을 방지한다.

    Parameters
    ----------
    df : pd.DataFrame
        입력 DataFrame.
    outcome_col : str
        종속변수(결과) 컬럼명. 이 컬럼이 lag만큼 후행 이동된다.
    predictor_cols : list[str]
        예측 변수 컬럼 목록. shift 적용 없이 원본 그대로 유지된다.
    group_col : str
        그룹 식별 컬럼명 (예: 'athlete_id'). 그룹별 독립 shift를 보장한다.
    lag : int, optional
        후행 이동 일수 (기본값 1). 양수: 미래 값을 현재 행에 배치.

    Returns
    -------
    pd.DataFrame
        컬럼: [group_col] + predictor_cols + [outcome_col + '_lag{lag}'].
        NaN 행이 제거된 최종 DataFrame.
    """
    lagged_outcome_name = f"{outcome_col}_lag{lag}"
    result_frames = []

    for _, group in df.groupby(group_col):
        group = group.copy()
        # 양수 shift(-lag): 미래 값을 현재 행에 배치
        group[lagged_outcome_name] = group[outcome_col].shift(-lag)
        result_frames.append(group)

    if not result_frames:
        result_df = df.copy()
        result_df[lagged_outcome_name] = np.nan
    else:
        result_df = pd.concat(result_frames, ignore_index=True)

    # 필요한 컬럼만 선택
    output_cols = [group_col] + predictor_cols + [lagged_outcome_name]
    result_df = result_df[output_cols]

    # NaN 행 제거
    result_df = result_df.dropna().reset_index(drop=True)

    return result_df
