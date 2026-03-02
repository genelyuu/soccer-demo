"""
통합 합성 데이터 생성(DGP) 모듈.

한 선수가 daily_load + HRV(rMSSD) + wellness(Hooper) 모두를 가지는
단일 통합 데이터셋을 생성한다.

실제 데이터 분석에서 도출된 세 가지 핵심 발견을 검증하기 위한 DGP:
  (1) 개인화된 기저선 추적 (랜덤 절편)
  (2) 다중 지표 통합 모니터링
  (3) Monotony 독립 효과

구조:
  선수 j (1..N_ATHLETES), 일 t (1..N_DAYS)
  [계층 1] 이변량 정규분포 랜덤효과 → u_j^hrv, u_j^hooper
  [계층 2] 일별 부하: base_load × day_pattern × spike_factor + noise
  [계층 3] 파생 지표: ACWR, Monotony, Strain (기존 src/metrics/ 호출)
  [계층 4] HRV (시점 t): ln_rmssd = 3.8 + β×ACWR(t-1) + β×Mono(t-1) + u_j + ε
  [계층 5] Hooper 결과 (t+1): hooper_next = 10.0 + β×ACWR + β×Mono + β×Strain + β×ln_rmssd + u_j + ε

재현성: seed=2024 (기존 42와 독립)
"""

import numpy as np
import pandas as pd

from src.metrics.acwr import acwr_rolling, acwr_ewma
from src.metrics.monotony_strain import monotony, strain


# ---------------------------------------------------------------------------
# 기본 파라미터
# ---------------------------------------------------------------------------
DEFAULT_PARAMS = {
    "seed": 2024,
    "n_athletes": 30,
    "n_days": 120,
    # 랜덤효과
    "sigma_u_hrv": 0.35,        # Track A ICC≈0.14 역산
    "sigma_u_hooper": 1.25,     # Track B ICC≈0.48 역산
    "cor_u": -0.3,              # HRV-Hooper 랜덤효과 상관
    # HRV 결과 모형 계수
    "intercept_hrv": 3.8,
    "beta_acwr_hrv": -0.15,     # Track A 방향 반영
    "beta_mono_hrv": -0.05,
    "sigma_e_hrv": 0.50,        # Track A 잔차
    # Hooper 결과 모형 계수
    "intercept_hooper": 10.0,
    "beta_acwr_hooper": -0.08,  # Track B M4 실제 계수
    "beta_mono_hooper": 0.14,   # Track B M4 실제 계수
    "beta_strain_hooper": -0.00007,  # Track B M4 실제 계수
    "beta_hrv_hooper": -0.50,   # HRV→Hooper 경로: 낮은 HRV → 높은 Hooper(악화)
    "sigma_e_hooper": 1.35,     # Track B 잔차
    # 부하 생성
    "base_load_mean": 400.0,
    "base_load_sd": 80.0,
    "load_noise_sd": 50.0,
    # 결측 주입
    "mcar_prob": 0.10,
    "mar_intercept": -2.0,
    "mar_slope": 0.005,
    "mnar_intercept": -3.0,
    "mnar_slope": 0.15,
}


# ---------------------------------------------------------------------------
# 계층 1: 선수 랜덤효과
# ---------------------------------------------------------------------------

def generate_athlete_random_effects(
    rng: np.random.Generator,
    n_athletes: int,
    sigma_u_hrv: float,
    sigma_u_hooper: float,
    cor_u: float,
) -> np.ndarray:
    """이변량 정규분포에서 선수별 랜덤효과를 생성한다.

    Parameters
    ----------
    rng : np.random.Generator
    n_athletes : int
    sigma_u_hrv : float
        HRV 랜덤효과 표준편차.
    sigma_u_hooper : float
        Hooper 랜덤효과 표준편차.
    cor_u : float
        HRV-Hooper 랜덤효과 간 상관계수.

    Returns
    -------
    np.ndarray
        (n_athletes, 2) 배열. [:, 0] = u_hrv, [:, 1] = u_hooper.
    """
    cov_12 = cor_u * sigma_u_hrv * sigma_u_hooper
    cov_matrix = np.array([
        [sigma_u_hrv ** 2, cov_12],
        [cov_12, sigma_u_hooper ** 2],
    ])
    mean = np.array([0.0, 0.0])
    return rng.multivariate_normal(mean, cov_matrix, size=n_athletes)


# ---------------------------------------------------------------------------
# 계층 2: 일별 부하
# ---------------------------------------------------------------------------

# 요일별 부하 배수 (월~일: index 0=월, 6=일)
DAY_PATTERN = np.array([1.0, 1.1, 0.9, 1.2, 1.0, 1.3, 0.3])
SPIKE_WEEKS = {3, 8, 14}  # 부하 스파이크 주차 (0-indexed)
SPIKE_FACTOR = 1.5


def generate_daily_load(
    rng: np.random.Generator,
    n_athletes: int,
    n_days: int,
    base_load_mean: float,
    base_load_sd: float,
    load_noise_sd: float,
) -> pd.DataFrame:
    """선수별 일별 부하(daily_load)를 생성한다.

    Parameters
    ----------
    rng : np.random.Generator
    n_athletes : int
    n_days : int
    base_load_mean : float
        개인 기저 부하 평균.
    base_load_sd : float
        개인 기저 부하 표준편차.
    load_noise_sd : float
        일별 부하 잡음 표준편차.

    Returns
    -------
    pd.DataFrame
        컬럼: [athlete, day, daily_load].
    """
    base_loads = rng.normal(base_load_mean, base_load_sd, size=n_athletes)
    base_loads = np.clip(base_loads, 100.0, 800.0)

    records = []
    for j in range(n_athletes):
        for t in range(n_days):
            dow = t % 7  # 0=월, 6=일
            week_idx = t // 7
            pattern = DAY_PATTERN[dow]
            spike = SPIKE_FACTOR if week_idx in SPIKE_WEEKS else 1.0
            noise = rng.normal(0, load_noise_sd)
            load = base_loads[j] * pattern * spike + noise
            load = max(load, 0.0)  # 부하는 음수 불가
            records.append({
                "athlete": f"ATH_{j+1:03d}",
                "day": t,
                "daily_load": load,
            })

    return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# 계층 3: 파생 지표 (기존 모듈 호출)
# ---------------------------------------------------------------------------

def compute_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """기존 src/metrics/ 모듈로 ACWR, Monotony, Strain을 산출한다.

    Parameters
    ----------
    df : pd.DataFrame
        컬럼 [athlete, day, daily_load] 필요.

    Returns
    -------
    pd.DataFrame
        원본에 acwr_ra, acwr_ew, mono, strain_val 컬럼 추가.
    """
    result_frames = []

    for athlete, group in df.groupby("athlete"):
        group = group.sort_values("day").copy()
        loads = group["daily_load"]

        group["acwr_ra"] = acwr_rolling(loads).values
        group["acwr_ew"] = acwr_ewma(loads).values
        group["mono"] = monotony(loads).values
        group["strain_val"] = strain(loads).values

        result_frames.append(group)

    return pd.concat(result_frames, ignore_index=True)


# ---------------------------------------------------------------------------
# 계층 4-5: 결과변수 생성 (HRV + Hooper, lag-1)
# ---------------------------------------------------------------------------

def generate_outcomes(
    df: pd.DataFrame,
    random_effects: np.ndarray,
    rng: np.random.Generator,
    params: dict,
) -> pd.DataFrame:
    """HRV(ln_rmssd), ln_rmssd_next, Hooper(hooper_next) 결과변수를 생성한다.

    2단계 과정:
      1) ln_rmssd(t): 시점 t의 HRV. ACWR(t-1), Mono(t-1) 기반 (또는 warmup 이전은 기저선).
      2) hooper_next(t): 시점 t+1의 Hooper. ACWR(t), Mono(t), Strain(t), ln_rmssd(t) 기반.

    Hooper는 4개 항목(fatigue, stress, doms, sleep) 개별 생성 후 합산.

    Parameters
    ----------
    df : pd.DataFrame
        파생 지표 포함 DataFrame.
    random_effects : np.ndarray
        (n_athletes, 2) 배열. [:, 0] = u_hrv, [:, 1] = u_hooper.
    rng : np.random.Generator
    params : dict
        DGP 파라미터 딕셔너리.

    Returns
    -------
    pd.DataFrame
        ln_rmssd, ln_rmssd_next, hooper_next, fatigue, stress, doms, sleep 컬럼 추가.
    """
    athletes = sorted(df["athlete"].unique())
    athlete_idx = {a: i for i, a in enumerate(athletes)}

    beta_hrv_hooper = params.get("beta_hrv_hooper", 0.0)

    # 결과변수 초기화
    ln_rmssd_arr = np.full(len(df), np.nan)
    ln_rmssd_next = np.full(len(df), np.nan)
    hooper_next = np.full(len(df), np.nan)
    fatigue_arr = np.full(len(df), np.nan)
    stress_arr = np.full(len(df), np.nan)
    doms_arr = np.full(len(df), np.nan)
    sleep_arr = np.full(len(df), np.nan)

    for athlete, group in df.groupby("athlete"):
        j = athlete_idx[athlete]
        u_hrv = random_effects[j, 0]
        u_hooper = random_effects[j, 1]
        idx = group.index.values
        n = len(group)

        acwr_vals = group["acwr_ra"].values
        mono_vals = group["mono"].values
        strain_vals = group["strain_val"].values

        # --- 1단계: ln_rmssd(t) 생성 ---
        # 첫 날은 기저선 HRV (ACWR/Mono 없음)
        ln_rmssd_arr[idx[0]] = (
            params["intercept_hrv"] + u_hrv
            + rng.normal(0, params["sigma_e_hrv"])
        )

        for i in range(1, n):
            # ln_rmssd(t)는 ACWR(t-1), Mono(t-1)에 의존
            acwr_prev = acwr_vals[i - 1]
            mono_prev = mono_vals[i - 1]

            if np.isnan(acwr_prev) or np.isnan(mono_prev):
                # warmup 기간: 기저선 HRV
                ln_rmssd_arr[idx[i]] = (
                    params["intercept_hrv"] + u_hrv
                    + rng.normal(0, params["sigma_e_hrv"])
                )
            else:
                mu_hrv = (
                    params["intercept_hrv"]
                    + params["beta_acwr_hrv"] * acwr_prev
                    + params["beta_mono_hrv"] * mono_prev
                    + u_hrv
                )
                ln_rmssd_arr[idx[i]] = mu_hrv + rng.normal(0, params["sigma_e_hrv"])

        # --- 2단계: ln_rmssd_next(t) = ln_rmssd(t+1) ---
        for i in range(n - 1):
            ln_rmssd_next[idx[i]] = ln_rmssd_arr[idx[i + 1]]

        # --- 3단계: hooper_next(t) 생성 ---
        for i in range(n - 1):
            acwr_t = acwr_vals[i]
            mono_t = mono_vals[i]
            strain_t = strain_vals[i]
            hrv_t = ln_rmssd_arr[idx[i]]

            # NaN 예측변수 → 결과도 NaN (warmup 기간)
            if np.isnan(acwr_t) or np.isnan(mono_t) or np.isnan(strain_t):
                continue

            # Hooper: intercept + β×ACWR + β×Mono + β×Strain + β×ln_rmssd + u_j + ε
            mu_hooper = (
                params["intercept_hooper"]
                + params["beta_acwr_hooper"] * acwr_t
                + params["beta_mono_hooper"] * mono_t
                + params["beta_strain_hooper"] * strain_t
                + beta_hrv_hooper * hrv_t
                + u_hooper
            )
            hooper_total = mu_hooper + rng.normal(0, params["sigma_e_hooper"])

            # 4개 항목으로 분배: 총합 / 4 + 개별 잡음
            item_mean = hooper_total / 4.0
            fat = np.clip(item_mean + rng.normal(0, 0.3), 1, 7)
            strs = np.clip(item_mean + rng.normal(0, 0.3), 1, 7)
            dom = np.clip(item_mean + rng.normal(0, 0.3), 1, 7)
            slp = np.clip(item_mean + rng.normal(0, 0.3), 1, 7)

            hooper_next[idx[i]] = fat + strs + dom + slp
            fatigue_arr[idx[i]] = fat
            stress_arr[idx[i]] = strs
            doms_arr[idx[i]] = dom
            sleep_arr[idx[i]] = slp

    df = df.copy()
    df["ln_rmssd"] = ln_rmssd_arr
    df["ln_rmssd_next"] = ln_rmssd_next
    df["hooper_next"] = hooper_next
    df["fatigue"] = fatigue_arr
    df["stress"] = stress_arr
    df["doms"] = doms_arr
    df["sleep"] = sleep_arr

    return df


# ---------------------------------------------------------------------------
# 결측 주입
# ---------------------------------------------------------------------------

def inject_missingness(
    df: pd.DataFrame,
    rng: np.random.Generator,
    mechanism: str,
    params: dict,
    target_col: str = "hooper_next",
) -> pd.DataFrame:
    """지정된 메커니즘으로 결측을 주입한다.

    Parameters
    ----------
    df : pd.DataFrame
        완전 데이터.
    rng : np.random.Generator
    mechanism : str
        "mcar", "mar", "mnar" 중 하나.
    params : dict
        DGP 파라미터 딕셔너리.
    target_col : str
        결측 주입 대상 컬럼 (기본값 "hooper_next").

    Returns
    -------
    pd.DataFrame
        결측 주입된 복사본.
    """
    df = df.copy()
    valid_mask = df[target_col].notna()
    valid_idx = df.index[valid_mask]

    if mechanism == "mcar":
        prob = params["mcar_prob"]
        missing_mask = rng.random(len(valid_idx)) < prob

    elif mechanism == "mar":
        # P(missing | load) = logistic(intercept + slope × load)
        loads = df.loc[valid_idx, "daily_load"].values
        logit = params["mar_intercept"] + params["mar_slope"] * loads
        prob = 1.0 / (1.0 + np.exp(-logit))
        missing_mask = rng.random(len(valid_idx)) < prob

    elif mechanism == "mnar":
        # P(missing | hooper) = logistic(intercept + slope × hooper)
        hooper_vals = df.loc[valid_idx, target_col].values
        logit = params["mnar_intercept"] + params["mnar_slope"] * hooper_vals
        prob = 1.0 / (1.0 + np.exp(-logit))
        missing_mask = rng.random(len(valid_idx)) < prob

    else:
        raise ValueError(f"지원하지 않는 결측 메커니즘: {mechanism}")

    drop_idx = valid_idx[missing_mask]
    df.loc[drop_idx, target_col] = np.nan

    # Hooper 항목도 함께 결측 처리
    if target_col == "hooper_next":
        for col in ["fatigue", "stress", "doms", "sleep"]:
            if col in df.columns:
                df.loc[drop_idx, col] = np.nan

    return df


# ---------------------------------------------------------------------------
# 마스터 함수
# ---------------------------------------------------------------------------

def generate_integrated_dataset(
    params: dict | None = None,
    return_complete: bool = False,
) -> pd.DataFrame | tuple:
    """통합 합성 데이터셋을 생성한다.

    Parameters
    ----------
    params : dict, optional
        DGP 파라미터. None이면 DEFAULT_PARAMS 사용.
    return_complete : bool
        True이면 (완전 데이터, 랜덤효과) 튜플 반환.

    Returns
    -------
    pd.DataFrame
        통합 합성 데이터셋.
        return_complete=True일 경우 (df, random_effects) 튜플.
    """
    if params is None:
        params = DEFAULT_PARAMS.copy()

    rng = np.random.default_rng(params["seed"])

    # 계층 1: 랜덤효과
    random_effects = generate_athlete_random_effects(
        rng,
        params["n_athletes"],
        params["sigma_u_hrv"],
        params["sigma_u_hooper"],
        params["cor_u"],
    )

    # 계층 2: 일별 부하
    df = generate_daily_load(
        rng,
        params["n_athletes"],
        params["n_days"],
        params["base_load_mean"],
        params["base_load_sd"],
        params["load_noise_sd"],
    )

    # 계층 3: 파생 지표
    df = compute_derived_metrics(df)

    # 계층 4-5: 결과변수
    df = generate_outcomes(df, random_effects, rng, params)

    if return_complete:
        return df, random_effects

    return df
