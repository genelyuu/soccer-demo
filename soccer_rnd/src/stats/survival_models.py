# -*- coding: utf-8 -*-
"""
부상예측 게이트 P3 — 주 추론·삼각검증 모듈 (Stage 8).

ACWR과 부상 onset 위험의 연관을 **세 가지 독립 설계**로 추정하여
방향 일관성(triangulation)을 관찰한다. 단일 모형의 가정 위반에 대한
강건성을 확보하기 위함이며, 어느 설계도 인과를 단정하지 않는다.

세 가지 설계
------------
1. fit_discrete_time_survival : 이산시간 생존(complementary log-log).
   person-period(각 athlete-day가 최초 onset까지 at-risk)로 위험집합을
   구성하고 GLM(Binomial, link=cloglog)로 hazard ~ ACWR을 적합한다.
   exp(coef) = hazard ratio(HR) + 95% CI를 반환한다.
2. fit_case_crossover : case-crossover(조건부 로지스틱, ConditionalLogit).
   각 onset(case) athlete-day의 ACWR을 동일 선수 통제기간 ACWR과 비교한다.
   선수가 자기 자신의 대조군이 되므로 시간불변 교란을 설계상 통제한다.
   exp(coef) = odds ratio(OR) + 95% CI를 반환한다.
3. fit_penalized_glmm : 벌점(L2/ridge) 로지스틱. onset_next_k ~ ACWR(+공변량).
   희소 이벤트의 분리(separation)·불안정을 완화한다. coef + 근사 CI 반환.

triangulate : 위 세 설계를 모두 실행해 ACWR 효과의 방향(위험↑/↓)이
일관되는지 판정하는 요약 DataFrame을 반환한다.

인과 구조 주의(ADR / RESEARCH_PROTOCOL)
----------------------------------------
부하(load) → 피로(fatigue/wellness) → 부상의 매개 구조가 가정된다.
피로(wellness)는 **매개변수**이므로 ACWR의 *총효과* 추정 시 공변량으로
투입하면 과조정(over-adjustment) 편향이 발생한다. 따라서 주 모형은
**ACWR 단독(+시간불변 교란만)** 으로 총효과를 추정하며, 매개분석은 분리한다.

검정력·변수예산
---------------
onset=43건, 발생률 1.748/1000 athlete-days. EPV(events-per-variable)≤4
제약으로 **동시 예측변수는 최대 4개**. 주 모형은 ACWR 단독부터 시작한다.

척도·전처리
-----------
ACWR은 전처리에서 4.0으로 캡핑되어 있다(track_B_merged.csv). 본 모듈은
기본적으로 **원척도(raw)** ACWR을 사용하며(효과를 ACWR 1단위 변화로 해석),
``standardize=True`` 시 z-score 표준화하여 1 표준편차 변화로 해석한다.

군집(선수) 처리
---------------
(1) 이산시간 생존: 선수 군집 robust(sandwich) 표준오차를 사용한다
    (frailty 랜덤효과의 GLM 근사 대안). docstring·반환 dict에 명시한다.
(2) case-crossover: ConditionalLogit의 ``groups``(선수)로 층화하여
    선수 내 비교만 사용한다(군집을 설계에 내재화).
(3) 벌점 로지스틱: 군집 보정 없음(벌점에 의한 안정화가 우선). 한계로 명시.
"""

from __future__ import annotations

import warnings
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.discrete.conditional_models import ConditionalLogit
from statsmodels.genmod.families.links import CLogLog

# 기본 설정 상수
DEFAULT_ACWR_COL = "acwr"
DEFAULT_ATHLETE_COL = "athlete_id"
DEFAULT_DATE_COL = "date"
DEFAULT_HORIZON = 7
# case-crossover 통제기간 lag(일). 동일 선수의 onset 이전 시점을 대조로 사용.
DEFAULT_CONTROL_LAGS: tuple[int, ...] = (14, 21, 28)


# ---------------------------------------------------------------------------
# 내부 유틸
# ---------------------------------------------------------------------------

def _maybe_standardize(series: pd.Series, standardize: bool) -> pd.Series:
    """필요 시 z-score 표준화. 표준편차 0이면 원본 유지."""
    if not standardize:
        return series.astype(float)
    sd = series.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return series.astype(float)
    return (series - series.mean()) / sd


def _nan_result(design: str, effect_name: str, message: str) -> dict:
    """수렴 실패·분리 등으로 추정 불가 시 일관된 NaN 결과 dict."""
    return {
        "design": design,
        "effect_name": effect_name,
        "coef": np.nan,
        "effect": np.nan,
        "ci_low": np.nan,
        "ci_high": np.nan,
        "pvalue": np.nan,
        "n_obs": 0,
        "n_events": 0,
        "converged": False,
        "note": message,
    }


# ---------------------------------------------------------------------------
# (1) 이산시간 생존 (cloglog)
# ---------------------------------------------------------------------------

def build_person_period(
    panel: pd.DataFrame,
    onset_df: pd.DataFrame,
    acwr_col: str = DEFAULT_ACWR_COL,
    athlete_col: str = DEFAULT_ATHLETE_COL,
    date_col: str = DEFAULT_DATE_COL,
) -> pd.DataFrame:
    """person-period(이산시간 위험집합) DataFrame을 구성한다.

    각 athlete-day는 해당 선수의 **최초 onset일까지** at-risk 상태이며,
    최초 onset일에 event=1, 그 이후 athlete-day는 위험집합에서 제거(검열)한다.
    onset이 없는 선수는 관찰 전 기간이 event=0으로 남는다.

    Parameters
    ----------
    panel : pd.DataFrame
        athlete-day 패널(``athlete_id``, ``date``, ``acwr`` 포함).
    onset_df : pd.DataFrame
        build_injury_onset_label 결과(``player_name``, ``onset_date``).

    Returns
    -------
    pd.DataFrame
        컬럼 ``athlete_id``, ``date``, ``acwr``, ``event``(0/1).
        최초 onset 이후 행은 제외된다.
    """
    df = panel[[athlete_col, date_col, acwr_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()
    df = df.dropna(subset=[acwr_col]).sort_values([athlete_col, date_col])

    # 선수별 최초 onset일
    first_onset = (
        onset_df.groupby("player_name")["onset_date"].min()
    )
    first_onset = pd.to_datetime(first_onset)

    df["_first_onset"] = df[athlete_col].map(first_onset)
    df["event"] = 0

    # 최초 onset일과 정확히 일치하는 athlete-day = event
    has_onset = df["_first_onset"].notna()
    df.loc[has_onset & (df[date_col] == df["_first_onset"]), "event"] = 1

    # 최초 onset일 이후(>onset) 행은 위험집합에서 제거
    keep = ~(has_onset & (df[date_col] > df["_first_onset"]))
    df = df.loc[keep].copy()

    return df[[athlete_col, date_col, acwr_col, "event"]].reset_index(drop=True)


def fit_discrete_time_survival(
    panel: pd.DataFrame,
    onset_df: pd.DataFrame,
    acwr_col: str = DEFAULT_ACWR_COL,
    athlete_col: str = DEFAULT_ATHLETE_COL,
    date_col: str = DEFAULT_DATE_COL,
    standardize: bool = False,
    cluster_robust: bool = True,
) -> dict:
    """이산시간 생존모형(cloglog)으로 hazard ~ ACWR을 적합한다.

    person-period를 구성한 뒤 GLM(Binomial, link=cloglog)을 적합한다.
    cloglog 링크에서 exp(coef)는 **hazard ratio(HR)** 로 해석된다(비례위험
    가정하 연속시간 Cox와 정합). 선수 군집 robust(sandwich) 표준오차로
    동일 선수 athlete-day 간 상관(frailty)을 근사 보정한다.

    Parameters
    ----------
    panel, onset_df : pd.DataFrame
        패널과 onset 라벨(build_person_period 참조).
    standardize : bool, default False
        True면 ACWR을 z-score 표준화(효과 = 1 표준편차 변화당 HR).
    cluster_robust : bool, default True
        True면 선수 군집 robust SE(권장). False면 모형기반 SE.

    Returns
    -------
    dict
        ``design``, ``effect_name``('HR'), ``coef``(log-HR), ``effect``(HR),
        ``ci_low``/``ci_high``(HR 척도 95% CI), ``pvalue``, ``n_obs``,
        ``n_events``, ``converged``, ``note``.
    """
    design = "discrete_time_cloglog"
    pp = build_person_period(panel, onset_df, acwr_col, athlete_col, date_col)
    if len(pp) == 0 or pp["event"].sum() == 0:
        return _nan_result(design, "HR", "위험집합이 비었거나 이벤트가 없음")

    x = _maybe_standardize(pp[acwr_col], standardize)
    X = sm.add_constant(pd.DataFrame({acwr_col: x.to_numpy()}))
    y = pp["event"].to_numpy()

    try:
        model = sm.GLM(y, X, family=sm.families.Binomial(link=CLogLog()))
        if cluster_robust:
            res = model.fit(
                cov_type="cluster",
                cov_kwds={"groups": pp[athlete_col].to_numpy()},
            )
            se_note = "선수 군집 robust SE(frailty 근사)"
        else:
            res = model.fit()
            se_note = "모형기반 SE"
    except Exception as exc:  # noqa: BLE001
        return _nan_result(design, "HR", f"적합 실패: {exc}")

    if not bool(getattr(res, "converged", True)):
        return _nan_result(design, "HR", "GLM 수렴 실패")

    coef = float(res.params[acwr_col])
    ci = res.conf_int().loc[acwr_col]
    return {
        "design": design,
        "effect_name": "HR",
        "coef": coef,
        "effect": float(np.exp(coef)),
        "ci_low": float(np.exp(ci[0])),
        "ci_high": float(np.exp(ci[1])),
        "pvalue": float(res.pvalues[acwr_col]),
        "n_obs": int(len(pp)),
        "n_events": int(y.sum()),
        "converged": True,
        "note": f"cloglog 이산시간 hazard; {se_note}; "
                f"척도={'z' if standardize else 'raw'} ACWR",
    }


# ---------------------------------------------------------------------------
# (2) case-crossover (조건부 로지스틱)
# ---------------------------------------------------------------------------

def build_case_crossover(
    panel: pd.DataFrame,
    onset_df: pd.DataFrame,
    acwr_col: str = DEFAULT_ACWR_COL,
    athlete_col: str = DEFAULT_ATHLETE_COL,
    date_col: str = DEFAULT_DATE_COL,
    control_lags: Iterable[int] = DEFAULT_CONTROL_LAGS,
) -> pd.DataFrame:
    """case-crossover 위험집합(case-control 짝)을 구성한다.

    각 onset(case)일을 case(1)로, 동일 선수의 ``control_lags``일 이전
    시점들을 control(0)으로 묶어 하나의 strata(set_id)로 만든다.
    선수가 자기 자신의 대조군이므로 시간불변 개인 교란(체격·포지션 등)이
    설계상 상쇄된다.

    Returns
    -------
    pd.DataFrame
        컬럼 ``set_id``, ``athlete_id``, ``case``(0/1), ``acwr``.
        case와 control이 모두 존재하는 strata만 포함된다.
    """
    df = panel[[athlete_col, date_col, acwr_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.normalize()
    df = df.dropna(subset=[acwr_col])
    lookup = df.set_index([athlete_col, date_col])[acwr_col].to_dict()

    control_lags = list(control_lags)
    rows: list[dict] = []
    set_id = 0
    for _, ev in onset_df.iterrows():
        aid = ev["player_name"]
        d0 = pd.Timestamp(ev["onset_date"]).normalize()
        case_val = lookup.get((aid, d0))
        if case_val is None or pd.isna(case_val):
            continue
        controls = []
        for lag in control_lags:
            cv = lookup.get((aid, d0 - pd.Timedelta(days=lag)))
            if cv is not None and pd.notna(cv):
                controls.append(cv)
        if not controls:
            continue
        rows.append({"set_id": set_id, athlete_col: aid, "case": 1, acwr_col: float(case_val)})
        for cv in controls:
            rows.append({"set_id": set_id, athlete_col: aid, "case": 0, acwr_col: float(cv)})
        set_id += 1

    return pd.DataFrame(rows)


def fit_case_crossover(
    panel: pd.DataFrame,
    onset_df: pd.DataFrame,
    acwr_col: str = DEFAULT_ACWR_COL,
    athlete_col: str = DEFAULT_ATHLETE_COL,
    date_col: str = DEFAULT_DATE_COL,
    control_lags: Iterable[int] = DEFAULT_CONTROL_LAGS,
    standardize: bool = False,
) -> dict:
    """case-crossover 조건부 로지스틱(ConditionalLogit)으로 OR을 추정한다.

    onset일(case)의 ACWR을 동일 선수의 이전 통제일(control) ACWR과 비교한다.
    strata(set_id)별 조건부 우도를 사용하므로 시간불변 교란을 통제한다.
    exp(coef) = **odds ratio(OR)**.

    Returns
    -------
    dict
        ``design``, ``effect_name``('OR'), ``coef``(log-OR), ``effect``(OR),
        ``ci_low``/``ci_high``(OR 척도), ``pvalue``, ``n_obs``, ``n_events``,
        ``converged``, ``note``.
    """
    design = "case_crossover_clogit"
    cc = build_case_crossover(
        panel, onset_df, acwr_col, athlete_col, date_col, control_lags
    )
    if len(cc) == 0 or cc["case"].sum() == 0:
        return _nan_result(design, "OR", "case-control 짝을 구성할 수 없음")

    x = _maybe_standardize(cc[acwr_col], standardize)
    exog = pd.DataFrame({acwr_col: x.to_numpy()})
    endog = cc["case"].to_numpy()
    groups = cc["set_id"].to_numpy()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = ConditionalLogit(endog, exog, groups=groups).fit(disp=0)
    except Exception as exc:  # noqa: BLE001
        return _nan_result(design, "OR", f"조건부 로지스틱 적합 실패: {exc}")

    try:
        coef = float(res.params[acwr_col])
        ci = res.conf_int().loc[acwr_col]
        pval = float(res.pvalues[acwr_col])
        ci_low, ci_high = float(ci[0]), float(ci[1])
    except Exception as exc:  # noqa: BLE001
        return _nan_result(design, "OR", f"계수 추출 실패(분리 의심): {exc}")

    if not np.isfinite(coef) or not np.isfinite(ci_low) or not np.isfinite(ci_high):
        return _nan_result(design, "OR", "추정치 비유한(분리 의심)")

    return {
        "design": design,
        "effect_name": "OR",
        "coef": coef,
        "effect": float(np.exp(coef)),
        "ci_low": float(np.exp(ci_low)),
        "ci_high": float(np.exp(ci_high)),
        "pvalue": pval,
        "n_obs": int(len(cc)),
        "n_events": int(cc["case"].sum()),
        "converged": True,
        "note": f"조건부 로지스틱; 통제 lag={list(control_lags)}일; "
                f"척도={'z' if standardize else 'raw'} ACWR",
    }


# ---------------------------------------------------------------------------
# (3) 벌점 로지스틱 (L2/ridge)
# ---------------------------------------------------------------------------

def fit_penalized_glmm(
    panel: pd.DataFrame,
    onset_df: Optional[pd.DataFrame] = None,
    horizon: int = DEFAULT_HORIZON,
    acwr_col: str = DEFAULT_ACWR_COL,
    covariates: Optional[Iterable[str]] = None,
    alpha: float = 1.0,
    standardize: bool = True,
    label_col: Optional[str] = None,
) -> dict:
    """벌점(L2/ridge) 로지스틱으로 onset_next_k ~ ACWR(+공변량)을 적합한다.

    희소 이벤트에서 완전·준완전 분리(separation)와 계수 폭주를 완화하기
    위해 L2 벌점을 적용한다(statsmodels ``Logit.fit_regularized``, L1_wt=0).
    EPV≤4 제약상 ``covariates``를 포함해도 총 예측변수는 4개 이하로 제한한다.

    라벨은 ``label_col``(예: ``onset_next_7``)이 패널에 있으면 그대로 쓰고,
    없으면 ``onset_df``와 ``horizon``으로 merge_onset_panel을 호출해 생성한다.

    벌점 추정의 CI/p-value는 **근사치**이며(벌점에 의한 수축으로 보수적),
    분리·수렴 실패 시 NaN과 메시지를 graceful하게 반환한다.

    Parameters
    ----------
    horizon : int, default 7
        선행 위험창 길이(label_col 미지정 시 onset_next_{horizon} 사용).
    alpha : float, default 1.0
        L2 벌점 강도(클수록 강한 수축).
    standardize : bool, default True
        벌점은 척도 의존적이므로 기본적으로 z-score 표준화를 권장한다.

    Returns
    -------
    dict
        ``design``, ``effect_name``('coef'), ``coef``, ``effect``(=coef),
        ``ci_low``/``ci_high``(근사), ``pvalue``(근사), ``n_obs``,
        ``n_events``, ``converged``, ``note``.
    """
    design = "penalized_logit_ridge"
    effect_name = "coef"

    work = panel.copy()
    target = label_col or f"onset_next_{horizon}"

    if target not in work.columns:
        if onset_df is None:
            return _nan_result(design, effect_name, f"라벨 컬럼 '{target}' 없음 및 onset_df 미제공")
        from src.data.injury_label import merge_onset_panel
        work = merge_onset_panel(work, onset_df, horizons=(horizon,))

    if target not in work.columns:
        return _nan_result(design, effect_name, f"라벨 '{target}' 생성 실패")

    feature_cols = [acwr_col] + (list(covariates) if covariates else [])
    # EPV≤4 변수예산 가드: 예측변수가 4개를 초과하면 거부
    if len(feature_cols) > 4:
        return _nan_result(
            design, effect_name,
            f"EPV<=4 위반: 예측변수 {len(feature_cols)}개(<=4 필요)",
        )

    sub = work.dropna(subset=feature_cols + [target]).copy()
    if len(sub) == 0 or sub[target].sum() == 0:
        return _nan_result(design, effect_name, "유효 표본 없음 또는 양성 0")

    X_raw = sub[feature_cols].astype(float)
    if standardize:
        X_raw = X_raw.apply(lambda c: _maybe_standardize(c, True))
    X = sm.add_constant(X_raw, has_constant="add")
    y = sub[target].to_numpy().astype(int)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = sm.Logit(y, X).fit_regularized(
                alpha=alpha, L1_wt=0.0, disp=0, maxiter=200,
            )
    except Exception as exc:  # noqa: BLE001
        return _nan_result(design, effect_name, f"벌점 로지스틱 적합 실패: {exc}")

    try:
        coef = float(res.params[acwr_col])
    except Exception as exc:  # noqa: BLE001
        return _nan_result(design, effect_name, f"계수 추출 실패: {exc}")

    if not np.isfinite(coef):
        return _nan_result(design, effect_name, "계수 비유한(분리 의심)")

    # 근사 CI/p-value (벌점 추정에서는 정확한 추론이 아니므로 근사로 표기)
    ci_low = ci_high = pval = np.nan
    try:
        ci = res.conf_int().loc[acwr_col]
        ci_low, ci_high = float(ci[0]), float(ci[1])
        pval = float(res.pvalues[acwr_col])
    except Exception:  # noqa: BLE001
        pass

    return {
        "design": design,
        "effect_name": effect_name,
        "coef": coef,
        "effect": coef,  # 로그오즈 척도 계수 자체가 효과 추정치
        "ci_low": ci_low,
        "ci_high": ci_high,
        "pvalue": pval,
        "n_obs": int(len(sub)),
        "n_events": int(y.sum()),
        "converged": True,
        "note": f"L2 벌점(alpha={alpha}); 라벨={target}; "
                f"예측변수={feature_cols}; 척도={'z' if standardize else 'raw'}; "
                "CI/p는 근사",
    }


# ---------------------------------------------------------------------------
# triangulate — 세 설계 통합·방향 일관성 판정
# ---------------------------------------------------------------------------

def triangulate(
    panel: pd.DataFrame,
    onset_df: pd.DataFrame,
    horizon: int = DEFAULT_HORIZON,
    acwr_col: str = DEFAULT_ACWR_COL,
    standardize: bool = False,
    penalized_standardize: bool = True,
    penalized_alpha: float = 1.0,
) -> pd.DataFrame:
    """세 설계를 모두 적합하여 ACWR 효과의 방향 일관성을 판정한다.

    각 설계의 효과추정치·95% CI·p-value와, '위험↑ 방향'(HR/OR>1 또는
    coef>0) 여부를 한 표로 정리한다. 마지막 행은 방향 일관성 요약이다.

    '위험↑ 방향' 판정 기준
    -----------------------
    - HR(이산시간 생존), OR(case-crossover): 효과 추정치 > 1
    - coef(벌점 로지스틱): 로그오즈 계수 > 0
    수렴 실패(NaN) 설계는 방향 판정에서 제외하고 'direction'을 NaN으로 둔다.

    Returns
    -------
    pd.DataFrame
        컬럼 ``design``, ``effect_name``, ``effect``, ``ci_low``, ``ci_high``,
        ``pvalue``, ``n_obs``, ``n_events``, ``converged``, ``direction_up``,
        ``note``. 추가로 'consistency_summary' 행에 일관성 판정 정보를 담는다.
    """
    results = [
        fit_discrete_time_survival(
            panel, onset_df, acwr_col=acwr_col, standardize=standardize
        ),
        fit_case_crossover(
            panel, onset_df, acwr_col=acwr_col, standardize=standardize
        ),
        fit_penalized_glmm(
            panel, onset_df, horizon=horizon, acwr_col=acwr_col,
            standardize=penalized_standardize, alpha=penalized_alpha,
        ),
    ]

    rows: list[dict] = []
    for r in results:
        if r["effect_name"] in ("HR", "OR"):
            direction_up = (r["effect"] > 1.0) if np.isfinite(r["effect"]) else np.nan
        else:  # coef
            direction_up = (r["coef"] > 0.0) if np.isfinite(r["coef"]) else np.nan
        rows.append({
            "design": r["design"],
            "effect_name": r["effect_name"],
            "effect": r["effect"],
            "ci_low": r["ci_low"],
            "ci_high": r["ci_high"],
            "pvalue": r["pvalue"],
            "n_obs": r["n_obs"],
            "n_events": r["n_events"],
            "converged": r["converged"],
            "direction_up": direction_up,
            "note": r["note"],
        })

    df = pd.DataFrame(rows)

    valid = df["direction_up"].dropna()
    n_valid = int(len(valid))
    n_up = int(valid.sum()) if n_valid else 0
    all_consistent = bool(n_valid > 0 and (n_up == n_valid or n_up == 0))
    direction_label = (
        "위험↑(증가)" if (n_valid > 0 and n_up == n_valid)
        else "위험↓(감소)" if (n_valid > 0 and n_up == 0)
        else "혼재" if n_valid > 0 else "판정불가"
    )

    summary_row = {
        "design": "consistency_summary",
        "effect_name": f"{n_up}/{n_valid} 위험↑",
        "effect": np.nan,
        "ci_low": np.nan,
        "ci_high": np.nan,
        "pvalue": np.nan,
        "n_obs": np.nan,
        "n_events": np.nan,
        "converged": all_consistent,
        "direction_up": all_consistent,
        "note": f"방향 일관성={direction_label}; 유효 설계 {n_valid}/3, "
                f"위험↑ {n_up}개; 전원 동일방향={all_consistent}",
    }
    df = pd.concat([df, pd.DataFrame([summary_row])], ignore_index=True)
    return df
