"""
LOSO(Leave-One-Subject-Out) 교차 검증 모듈.

혼합효과모형의 일반화 성능을 평가하기 위한 LOSO 교차 검증을 수행한다.
선수 한 명을 테스트셋으로 남기고 나머지로 모형을 적합하는 방식으로,
과적합 여부를 검증한다.

주요 기능
---------
- loso_cv              : 단일 모형에 대한 LOSO 교차 검증 실행
- loso_summary         : 교차 검증 결과 요약 통계 산출
- loso_cv_multi_model  : 복수 모형에 대한 LOSO 교차 검증 및 비교
- plot_loso_results    : 선수별 MAE 시각화
"""

from __future__ import annotations

import warnings
from typing import Dict

import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import patsy
import statsmodels.formula.api as smf


# ---------------------------------------------------------------------------
# 1) LOSO 교차 검증
# ---------------------------------------------------------------------------

def loso_cv(
    formula: str,
    data: pd.DataFrame,
    group_col: str,
    outcome_col: str,
) -> pd.DataFrame:
    """단일 혼합효과모형에 대해 LOSO 교차 검증을 수행한다.

    각 선수(그룹)를 순차적으로 테스트셋으로 두고, 나머지 선수들로
    mixedlm을 적합한 뒤, 테스트 선수의 예측값을 산출하여
    MAE와 RMSE를 계산한다.

    Parameters
    ----------
    formula : str
        Patsy/R-style 공식 (예: ``"hooper_next ~ acwr_rolling + monotony"``).
    data : pd.DataFrame
        분석에 사용할 데이터프레임.
    group_col : str
        그룹(선수) 식별 컬럼 이름.
    outcome_col : str
        종속변수 컬럼 이름 (MAE/RMSE 계산용).

    Returns
    -------
    pd.DataFrame
        컬럼: [subject, n_train, n_test, mae, rmse].
        각 fold(선수)별 한 행. 적합 실패 시 mae, rmse는 NaN.
    """
    subjects = data[group_col].unique()
    records: list[dict] = []

    for subject in subjects:
        test_mask = data[group_col] == subject
        test_data = data[test_mask].copy()
        train_data = data[~test_mask].copy()

        n_test = len(test_data)
        n_train = len(train_data)

        # 테스트 데이터가 1개 미만이면 스킵
        if n_test < 1:
            continue

        # train 세트에 그룹이 2개 이상이어야 mixedlm 작동
        n_train_groups = train_data[group_col].nunique()
        if n_train_groups < 2:
            warnings.warn(
                f"선수 '{subject}' fold: 학습 데이터의 그룹 수가 {n_train_groups}개로 "
                f"2개 미만이어서 혼합효과모형을 적합할 수 없습니다.",
                stacklevel=2,
            )
            records.append({
                "subject": subject,
                "n_train": n_train,
                "n_test": n_test,
                "mae": np.nan,
                "rmse": np.nan,
            })
            continue

        try:
            # 학습 데이터로 혼합효과모형 적합
            model = smf.mixedlm(formula, train_data, groups=train_data[group_col])
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = model.fit(reml=True)

            # 테스트 데이터 예측: 고정효과만 사용하여 수동 예측
            # patsy로 디자인 행렬 생성
            rhs = formula.split("~")[1].strip()
            test_exog = patsy.dmatrix(rhs, test_data, return_type="dataframe")

            # 고정효과 계수로 예측값 산출
            fe_params = result.fe_params
            # 디자인 행렬 컬럼과 고정효과 파라미터 순서를 맞춤
            y_pred = test_exog[fe_params.index].dot(fe_params).values

            y_true = test_data[outcome_col].values

            mae = float(np.mean(np.abs(y_true - y_pred)))
            rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

            records.append({
                "subject": subject,
                "n_train": n_train,
                "n_test": n_test,
                "mae": mae,
                "rmse": rmse,
            })

        except Exception as exc:  # noqa: BLE001
            warnings.warn(
                f"선수 '{subject}' fold 적합 실패: {exc}",
                stacklevel=2,
            )
            records.append({
                "subject": subject,
                "n_train": n_train,
                "n_test": n_test,
                "mae": np.nan,
                "rmse": np.nan,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 2) LOSO 결과 요약
# ---------------------------------------------------------------------------

def loso_summary(cv_results: pd.DataFrame) -> dict:
    """LOSO 교차 검증 결과의 요약 통계를 산출한다.

    NaN이 포함된 fold는 제외하고 계산한다.

    Parameters
    ----------
    cv_results : pd.DataFrame
        ``loso_cv`` 의 반환 DataFrame.

    Returns
    -------
    dict
        ``mean_mae``, ``std_mae``, ``median_mae``,
        ``mean_rmse``, ``std_rmse``, ``median_rmse``,
        ``n_subjects``, ``n_valid_folds`` 키를 갖는 딕셔너리.
    """
    valid = cv_results.dropna(subset=["mae", "rmse"])

    return {
        "mean_mae": float(valid["mae"].mean()) if len(valid) > 0 else np.nan,
        "std_mae": float(valid["mae"].std(ddof=1)) if len(valid) > 1 else np.nan,
        "median_mae": float(valid["mae"].median()) if len(valid) > 0 else np.nan,
        "mean_rmse": float(valid["rmse"].mean()) if len(valid) > 0 else np.nan,
        "std_rmse": float(valid["rmse"].std(ddof=1)) if len(valid) > 1 else np.nan,
        "median_rmse": float(valid["rmse"].median()) if len(valid) > 0 else np.nan,
        "n_subjects": len(cv_results),
        "n_valid_folds": len(valid),
    }


# ---------------------------------------------------------------------------
# 3) 다중 모형 LOSO 비교
# ---------------------------------------------------------------------------

def loso_cv_multi_model(
    formulas_dict: Dict[str, str],
    data: pd.DataFrame,
    group_col: str,
    outcome_col: str,
) -> pd.DataFrame:
    """복수 모형에 대해 LOSO 교차 검증을 수행하고 결과를 비교한다.

    각 모형에 대해 ``loso_cv`` → ``loso_summary`` 를 실행하여
    일반화 성능 지표를 통합한다.

    Parameters
    ----------
    formulas_dict : dict[str, str]
        ``{"모형이름": "formula_string", ...}`` 형식의 딕셔너리.
    data : pd.DataFrame
        분석에 사용할 데이터프레임.
    group_col : str
        그룹(선수) 식별 컬럼 이름.
    outcome_col : str
        종속변수 컬럼 이름.

    Returns
    -------
    pd.DataFrame
        컬럼: [model_name, mean_mae, std_mae, mean_rmse, std_rmse, n_valid_folds].
        각 모형별 한 행.
    """
    rows: list[dict] = []

    for model_name, formula in formulas_dict.items():
        cv_results = loso_cv(formula, data, group_col, outcome_col)
        summary = loso_summary(cv_results)

        rows.append({
            "model_name": model_name,
            "mean_mae": summary["mean_mae"],
            "std_mae": summary["std_mae"],
            "mean_rmse": summary["mean_rmse"],
            "std_rmse": summary["std_rmse"],
            "n_valid_folds": summary["n_valid_folds"],
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4) LOSO 결과 시각화
# ---------------------------------------------------------------------------

def plot_loso_results(
    cv_results: pd.DataFrame,
    title: str = "",
) -> matplotlib.figure.Figure:
    """선수별 MAE를 수평 막대그래프로 시각화한다.

    평균 MAE를 빨간 점선으로 표시하며, Figure 객체를 반환한다.

    Parameters
    ----------
    cv_results : pd.DataFrame
        ``loso_cv`` 의 반환 DataFrame.
    title : str, optional
        그래프 제목 (기본값 빈 문자열).

    Returns
    -------
    matplotlib.figure.Figure
        생성된 수평 막대 차트 Figure 객체.
    """
    # NaN fold 제외
    valid = cv_results.dropna(subset=["mae"]).copy()

    fig, ax = plt.subplots(figsize=(8, max(4, len(valid) * 0.5)))

    subjects = valid["subject"].astype(str).values
    mae_values = valid["mae"].values

    y_pos = np.arange(len(subjects))
    ax.barh(y_pos, mae_values, color="steelblue", edgecolor="white", height=0.6)

    # 평균 MAE 점선
    mean_mae = float(np.mean(mae_values)) if len(mae_values) > 0 else 0.0
    ax.axvline(x=mean_mae, color="red", linestyle="--", linewidth=1.2,
               label=f"Mean MAE = {mean_mae:.3f}")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(subjects)
    ax.set_xlabel("MAE")
    ax.set_ylabel("Subject")
    ax.set_title(title or "LOSO CV: Subject-level MAE")
    ax.legend(loc="lower right")
    ax.invert_yaxis()  # 첫 번째 선수가 위에 오도록

    fig.tight_layout()
    plt.close(fig)

    return fig
