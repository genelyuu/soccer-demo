"""
다중 시차(multi-lag) 분석 모듈.

예측변수(predictor)와 결과변수(outcome) 사이의 최적 시차를 탐색한다.
lag-0부터 lag-7(기본값)까지 Pearson 상관 및 혼합효과모형(LMM)을 적합하여
최적 lag을 체계적으로 결정한다.

의존성: pandas, numpy, scipy.stats, statsmodels, matplotlib.
"""

from __future__ import annotations

import warnings
from typing import List

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.formula.api import mixedlm


# ---------------------------------------------------------------------------
# 내부 유틸: 그룹별 시차 적용
# ---------------------------------------------------------------------------

def _apply_group_lag(
    df: pd.DataFrame,
    col: str,
    group_col: str,
    lag: int,
) -> pd.Series:
    """
    그룹(group_col) 내에서 col을 lag만큼 시프트한 시리즈를 반환한다.

    Parameters
    ----------
    df : pd.DataFrame
        원본 데이터프레임.
    col : str
        시프트할 컬럼명.
    group_col : str
        그룹 컬럼명 (예: 선수 ID).
    lag : int
        적용할 시차. 양수이면 과거 값을 현재 행에 매핑한다.

    Returns
    -------
    pd.Series
        시프트된 시리즈. 시프트로 인한 결측은 NaN.
    """
    return df.groupby(group_col)[col].shift(lag)


# ---------------------------------------------------------------------------
# 1) lag별 Pearson 상관 테이블
# ---------------------------------------------------------------------------

def lag_correlation_table(
    df: pd.DataFrame,
    predictor_col: str,
    outcome_col: str,
    group_col: str,
    max_lag: int = 7,
) -> pd.DataFrame:
    """
    각 lag(0~max_lag)에 대해 그룹별 shift 적용 후 전체 Pearson 상관계수와 p-value를 계산한다.

    predictor_col을 lag만큼 시프트한 뒤 outcome_col과의 상관을 구한다.
    즉 lag=k 이면 "k일 전의 predictor가 오늘의 outcome과 얼마나 관련되는가"를 측정한다.

    Parameters
    ----------
    df : pd.DataFrame
        패널 데이터. group_col, predictor_col, outcome_col 컬럼을 포함해야 한다.
    predictor_col : str
        예측변수 컬럼명.
    outcome_col : str
        결과변수 컬럼명.
    group_col : str
        그룹(선수) 식별 컬럼명.
    max_lag : int, optional
        탐색할 최대 시차 (기본값 7). lag 0부터 max_lag까지 포함.

    Returns
    -------
    pd.DataFrame
        컬럼: [lag, pearson_r, p_value, n_obs].
        행 수 = max_lag + 1.
    """
    records: list[dict] = []

    for lag in range(0, max_lag + 1):
        shifted = _apply_group_lag(df, predictor_col, group_col, lag)
        mask = shifted.notna() & df[outcome_col].notna()
        x = shifted[mask].values
        y = df.loc[mask, outcome_col].values

        if len(x) < 3:
            # 유효 관측치가 3개 미만이면 상관계수 산출 불가
            records.append({
                "lag": lag,
                "pearson_r": np.nan,
                "p_value": np.nan,
                "n_obs": len(x),
            })
        else:
            r, p = pearsonr(x, y)
            records.append({
                "lag": lag,
                "pearson_r": r,
                "p_value": p,
                "n_obs": len(x),
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 2) lag별 혼합효과모형(LMM) 비교
# ---------------------------------------------------------------------------

def lag_mixed_effects_comparison(
    df: pd.DataFrame,
    outcome_col: str,
    predictor_cols: List[str],
    group_col: str,
    max_lag: int = 7,
) -> pd.DataFrame:
    """
    각 lag(0~max_lag)에 대해 혼합효과모형(Linear Mixed-Effects Model)을 적합하고
    모형 적합도 지표를 비교한다.

    모형 수식: ``outcome_col ~ predictor_col1 + predictor_col2 + ...``
    랜덤 절편: group_col.

    각 predictor를 그룹 내에서 lag만큼 시프트한 뒤 모형을 적합한다.

    Parameters
    ----------
    df : pd.DataFrame
        패널 데이터.
    outcome_col : str
        결과변수 컬럼명.
    predictor_cols : list[str]
        예측변수 컬럼명 리스트.
    group_col : str
        그룹(선수) 식별 컬럼명. 랜덤 절편으로 사용된다.
    max_lag : int, optional
        탐색할 최대 시차 (기본값 7).

    Returns
    -------
    pd.DataFrame
        컬럼: [lag, aic, bic, mae, rmse, coef_<pred>, pvalue_<pred>, ...].
        행 수 = max_lag + 1. 최적 lag = AIC가 최소인 lag.
    """
    records: list[dict] = []

    for lag in range(0, max_lag + 1):
        # 시프트된 예측변수가 담긴 임시 데이터프레임 생성
        tmp = df[[outcome_col, group_col]].copy()

        for col in predictor_cols:
            tmp[col] = _apply_group_lag(df, col, group_col, lag)

        # 결측 제거
        tmp = tmp.dropna(subset=[outcome_col] + predictor_cols)

        if len(tmp) < len(predictor_cols) + 2:
            # 관측치가 부족하면 스킵
            row: dict = {"lag": lag, "aic": np.nan, "bic": np.nan,
                         "mae": np.nan, "rmse": np.nan}
            for col in predictor_cols:
                row[f"coef_{col}"] = np.nan
                row[f"pvalue_{col}"] = np.nan
            records.append(row)
            continue

        formula = f"{outcome_col} ~ {' + '.join(predictor_cols)}"

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = mixedlm(formula, tmp, groups=tmp[group_col])
                result = model.fit(reml=False, method="lbfgs")

            # AIC, BIC
            aic_val = result.aic
            bic_val = result.bic

            # 예측값 기반 MAE, RMSE
            y_true = tmp[outcome_col].values
            y_pred = result.fittedvalues.values
            mae_val = mean_absolute_error(y_true, y_pred)
            rmse_val = float(np.sqrt(mean_squared_error(y_true, y_pred)))

            row = {
                "lag": lag,
                "aic": aic_val,
                "bic": bic_val,
                "mae": mae_val,
                "rmse": rmse_val,
            }

            # 각 예측변수의 계수와 p-value
            for col in predictor_cols:
                row[f"coef_{col}"] = result.fe_params.get(col, np.nan)
                row[f"pvalue_{col}"] = result.pvalues.get(col, np.nan)

            records.append(row)

        except Exception:
            # 모형 적합 실패 시 NaN 처리
            row = {"lag": lag, "aic": np.nan, "bic": np.nan,
                   "mae": np.nan, "rmse": np.nan}
            for col in predictor_cols:
                row[f"coef_{col}"] = np.nan
                row[f"pvalue_{col}"] = np.nan
            records.append(row)

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 3) 최적 lag 선택
# ---------------------------------------------------------------------------

def optimal_lag(
    comparison_df: pd.DataFrame,
    criterion: str = "aic",
) -> int:
    """
    lag_mixed_effects_comparison 결과에서 주어진 기준(criterion)이 최소인 lag을 반환한다.

    Parameters
    ----------
    comparison_df : pd.DataFrame
        lag_mixed_effects_comparison의 반환 DataFrame.
    criterion : str, optional
        최적화 기준 컬럼명 (기본값 ``'aic'``). ``'bic'``도 사용 가능.

    Returns
    -------
    int
        최적 lag 값.

    Raises
    ------
    ValueError
        criterion 컬럼이 DataFrame에 존재하지 않을 때.
    KeyError
        모든 criterion 값이 NaN일 때.
    """
    if criterion not in comparison_df.columns:
        raise ValueError(
            f"기준 컬럼 '{criterion}'이(가) DataFrame에 존재하지 않습니다. "
            f"사용 가능한 컬럼: {list(comparison_df.columns)}"
        )

    valid = comparison_df.dropna(subset=[criterion])
    if valid.empty:
        raise KeyError(
            f"기준 컬럼 '{criterion}'의 모든 값이 NaN입니다. "
            "모형 적합이 모든 lag에서 실패했을 수 있습니다."
        )

    best_idx = valid[criterion].idxmin()
    return int(valid.loc[best_idx, "lag"])


# ---------------------------------------------------------------------------
# 4) lag 프로파일 시각화
# ---------------------------------------------------------------------------

def plot_lag_profile(
    corr_table: pd.DataFrame,
    title: str = "",
    significance_level: float = 0.05,
) -> matplotlib.figure.Figure:
    """
    lag별 Pearson 상관계수 프로파일을 시각화한다.

    x축은 lag, y축은 pearson_r이며, 통계적으로 유의한 lag에는 별표(*)를 표시한다.

    Parameters
    ----------
    corr_table : pd.DataFrame
        lag_correlation_table의 반환 DataFrame.
        컬럼: [lag, pearson_r, p_value, n_obs].
    title : str, optional
        그래프 제목 (기본값 빈 문자열).
    significance_level : float, optional
        유의수준 (기본값 0.05). p_value < significance_level이면 유의한 것으로 표시.

    Returns
    -------
    matplotlib.figure.Figure
        생성된 Figure 객체.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    lags = corr_table["lag"].values
    rs = corr_table["pearson_r"].values
    ps = corr_table["p_value"].values

    # 상관계수 바 차트
    colors = [
        "#2196F3" if (not np.isnan(p) and p < significance_level) else "#BDBDBD"
        for p in ps
    ]
    ax.bar(lags, rs, color=colors, edgecolor="black", linewidth=0.5)

    # 유의한 lag에 별표 표시
    for lag_val, r_val, p_val in zip(lags, rs, ps):
        if not np.isnan(p_val) and p_val < significance_level:
            y_offset = 0.02 if r_val >= 0 else -0.04
            ax.text(
                lag_val, r_val + y_offset, "*",
                ha="center", va="bottom", fontsize=14, fontweight="bold",
                color="red",
            )

    ax.set_xlabel("Lag (일)")
    ax.set_ylabel("Pearson r")
    ax.set_title(title or "Lag-Correlation Profile")
    ax.set_xticks(lags)
    ax.axhline(y=0, color="gray", linestyle="--", linewidth=0.8)
    ax.set_ylim(-1.05, 1.05)

    fig.tight_layout()
    plt.close(fig)

    return fig
