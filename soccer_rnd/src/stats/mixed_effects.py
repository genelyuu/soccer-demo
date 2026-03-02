"""
혼합효과모형(Mixed-Effects Model) 고도화 모듈.

랜덤 절편·기울기 모형 적합, 모형 지표 추출, 다중 모형 비교 유틸리티를 제공한다.

주요 기능
---------
- fit_random_intercept : 랜덤 절편 모형 편의 래퍼
- fit_random_slope     : 랜덤 기울기 모형 (re_formula 활용)
- extract_model_metrics: 적합 결과에서 AIC·BIC·MAE·RMSE 등 추출
- compare_models       : 여러 모형의 지표를 DataFrame으로 비교
- plot_model_comparison: 모형별 지표 막대 차트 시각화
"""

from __future__ import annotations

import warnings
from typing import Dict, Optional

import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLMResults


# ---------------------------------------------------------------------------
# 모형 적합 함수
# ---------------------------------------------------------------------------

def fit_random_intercept(
    formula: str,
    data: pd.DataFrame,
    group_col: str,
) -> MixedLMResults:
    """랜덤 절편(random-intercept-only) 혼합효과모형을 적합한다.

    Parameters
    ----------
    formula : str
        Patsy/R-style 공식 (예: ``"y ~ x1 + x2"``).
    data : pd.DataFrame
        분석에 사용할 데이터프레임.
    group_col : str
        그룹(피험자) 식별 컬럼 이름.

    Returns
    -------
    MixedLMResults
        적합된 모형 결과 객체.
    """
    model = smf.mixedlm(formula, data=data, groups=data[group_col])
    result = model.fit(reml=True)
    return result


def fit_random_slope(
    formula: str,
    data: pd.DataFrame,
    group_col: str,
    slope_var: str,
) -> Optional[MixedLMResults]:
    """랜덤 기울기(random-slope) 혼합효과모형을 적합한다.

    ``re_formula`` 파라미터를 사용하여 지정 변수의 랜덤 기울기를 추정한다.
    수렴에 실패하면 ``None`` 을 반환하고 경고를 출력한다.

    Parameters
    ----------
    formula : str
        Patsy/R-style 공식 (예: ``"y ~ x1 + x2"``).
    data : pd.DataFrame
        분석에 사용할 데이터프레임.
    group_col : str
        그룹(피험자) 식별 컬럼 이름.
    slope_var : str
        랜덤 기울기를 부여할 변수 이름 (예: ``"ACWR"``).

    Returns
    -------
    MixedLMResults 또는 None
        적합 성공 시 결과 객체, 수렴 실패 시 ``None``.
    """
    try:
        model = smf.mixedlm(
            formula,
            data=data,
            groups=data[group_col],
            re_formula=f"~{slope_var}",
        )
        result = model.fit(reml=True)
        return result
    except Exception as exc:  # noqa: BLE001
        warnings.warn(
            f"랜덤 기울기 모형 수렴 실패 (slope_var={slope_var!r}): {exc}",
            stacklevel=2,
        )
        return None


# ---------------------------------------------------------------------------
# 지표 추출
# ---------------------------------------------------------------------------

def extract_model_metrics(
    result: Optional[MixedLMResults],
    data: pd.DataFrame,
    outcome_col: str,
) -> dict:
    """적합된 혼합효과모형에서 주요 지표를 추출한다.

    Parameters
    ----------
    result : MixedLMResults 또는 None
        ``fit_random_intercept`` / ``fit_random_slope`` 의 반환값.
    data : pd.DataFrame
        모형 적합에 사용한 원본 데이터프레임.
    outcome_col : str
        종속변수 컬럼 이름 (MAE·RMSE 계산용).

    Returns
    -------
    dict
        ``aic``, ``bic``, ``mae``, ``rmse``, ``fixed_effects``,
        ``fixed_pvalues``, ``random_effects_var`` 를 키로 갖는 딕셔너리.
        ``result`` 가 ``None`` 이면 모든 값이 ``np.nan`` 인 딕셔너리를 반환한다.
    """
    nan_dict: dict = {
        "aic": np.nan,
        "bic": np.nan,
        "mae": np.nan,
        "rmse": np.nan,
        "fixed_effects": np.nan,
        "fixed_pvalues": np.nan,
        "random_effects_var": np.nan,
    }

    if result is None:
        return nan_dict

    # 잔차 기반 MAE / RMSE 계산
    y_true = data[outcome_col].values
    y_pred = result.fittedvalues.values
    residuals = y_true - y_pred
    mae = float(np.mean(np.abs(residuals)))
    rmse = float(np.sqrt(np.mean(residuals ** 2)))

    # 고정효과 계수 및 p-value
    fixed_effects = result.fe_params.to_dict()
    fixed_pvalues = result.pvalues.to_dict()

    # 랜덤효과 공분산 행렬 → 분산 추출
    # cov_re 는 랜덤효과의 공분산 행렬 (DataFrame 또는 ndarray)
    cov_re = result.cov_re
    if isinstance(cov_re, pd.DataFrame):
        random_effects_var = np.diag(cov_re.values).tolist()
    else:
        random_effects_var = np.diag(np.atleast_2d(cov_re)).tolist()

    # AIC / BIC 계산
    # REML 적합 시 statsmodels가 AIC·BIC를 nan으로 반환하는 경우가 있으므로
    # 로그우도(llf)와 파라미터 수(df_modelwc)로 수동 계산 폴백을 적용한다.
    aic_val = result.aic
    bic_val = result.bic
    if np.isnan(aic_val) or np.isnan(bic_val):
        llf = result.llf
        k = result.df_modelwc
        n = len(data)
        aic_val = -2.0 * llf + 2.0 * k
        bic_val = -2.0 * llf + np.log(n) * k

    return {
        "aic": float(aic_val),
        "bic": float(bic_val),
        "mae": mae,
        "rmse": rmse,
        "fixed_effects": fixed_effects,
        "fixed_pvalues": fixed_pvalues,
        "random_effects_var": random_effects_var,
    }


# ---------------------------------------------------------------------------
# 다중 모형 비교
# ---------------------------------------------------------------------------

def compare_models(
    models: Dict[str, Optional[MixedLMResults]],
    data: pd.DataFrame,
    outcome_col: str,
) -> pd.DataFrame:
    """여러 혼합효과모형의 지표를 하나의 DataFrame으로 비교한다.

    Parameters
    ----------
    models : dict[str, MixedLMResults | None]
        ``{모형_이름: 적합_결과}`` 딕셔너리.
    data : pd.DataFrame
        모형 적합에 사용한 원본 데이터프레임.
    outcome_col : str
        종속변수 컬럼 이름.

    Returns
    -------
    pd.DataFrame
        모형별 AIC, BIC, MAE, RMSE, 고정효과 계수, Cohen's f² 를
        포함하는 비교 테이블.

    Notes
    -----
    Cohen's f² 는 첫 번째 모형(기준 모형) 대비 각 모형의 효과 크기를 나타낸다.
    공식: f² = (R²_A − R²_base) / (1 − R²_A)
    """
    rows: list[dict] = []

    for name, result in models.items():
        metrics = extract_model_metrics(result, data, outcome_col)

        row: dict = {
            "model_name": name,
            "aic": metrics["aic"],
            "bic": metrics["bic"],
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "random_effects_var": metrics["random_effects_var"],
        }

        # 고정효과 계수를 개별 컬럼으로 풀어넣기
        if isinstance(metrics["fixed_effects"], dict):
            for coef_name, coef_val in metrics["fixed_effects"].items():
                row[f"coef_{coef_name}"] = coef_val
            for coef_name, pval in metrics["fixed_pvalues"].items():
                row[f"pval_{coef_name}"] = pval

        rows.append(row)

    comparison_df = pd.DataFrame(rows)

    # -----------------------------------------------------------------
    # Cohen's f² 계산 (첫 번째 모형 대비)
    # -----------------------------------------------------------------
    y_true = data[outcome_col].values
    ss_total = float(np.sum((y_true - np.mean(y_true)) ** 2))

    r_squared_list: list[float] = []
    for name, result in models.items():
        if result is not None and ss_total > 0:
            residuals = y_true - result.fittedvalues.values
            ss_res = float(np.sum(residuals ** 2))
            r2 = 1.0 - ss_res / ss_total
            r_squared_list.append(r2)
        else:
            r_squared_list.append(np.nan)

    comparison_df["r_squared"] = r_squared_list

    # f² = (R²_model − R²_base) / (1 − R²_model)
    base_r2 = r_squared_list[0] if len(r_squared_list) > 0 else np.nan
    cohens_f2: list[float] = []
    for r2 in r_squared_list:
        if np.isnan(r2) or np.isnan(base_r2) or r2 == 1.0:
            cohens_f2.append(np.nan)
        else:
            cohens_f2.append((r2 - base_r2) / (1.0 - r2))
    comparison_df["cohens_f2"] = cohens_f2

    return comparison_df


# ---------------------------------------------------------------------------
# 시각화
# ---------------------------------------------------------------------------

def plot_model_comparison(
    comparison_df: pd.DataFrame,
    metric: str = "aic",
) -> matplotlib.figure.Figure:
    """모형별 지정 지표를 막대 차트로 시각화한다.

    Parameters
    ----------
    comparison_df : pd.DataFrame
        ``compare_models`` 가 반환한 비교 테이블.
    metric : str, default ``"aic"``
        시각화할 지표 컬럼 이름 (예: ``"aic"``, ``"bic"``, ``"rmse"``).

    Returns
    -------
    matplotlib.figure.Figure
        생성된 막대 차트 Figure 객체.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    model_names = comparison_df["model_name"].tolist()
    values = comparison_df[metric].tolist()

    bars = ax.bar(model_names, values, color="steelblue", edgecolor="white")

    # 막대 위에 값 표시
    for bar, val in zip(bars, values):
        if not np.isnan(val):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    ax.set_xlabel("모형")
    ax.set_ylabel(metric.upper())
    ax.set_title(f"모형 비교 — {metric.upper()}")
    fig.tight_layout()

    return fig
