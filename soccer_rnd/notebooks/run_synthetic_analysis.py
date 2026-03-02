#!/usr/bin/env python3
"""
합성 데이터 기반 통합 분석 스크립트 (Track A + Track B)

목적: 파이프라인 검증용 합성 데이터로 혼합효과모형의 정합성을 확인한다.
재현성: np.random.seed(42) 고정.
AIC/BIC: reml=False (ML 추정)로 적합하여 NaN 방지.

사용법:
    cd notebooks
    python run_synthetic_analysis.py
"""

import sys
sys.path.insert(0, '..')

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.metrics.acwr import acwr_rolling, acwr_ewma
from src.metrics.monotony_strain import monotony, strain

np.random.seed(42)


# ============================================================================
# 유틸리티 함수
# ============================================================================

def pseudo_r2(y_true, y_pred):
    """Pseudo R-squared (1 - SS_res / SS_tot)."""
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    ss_res = np.sum((y_true - y_pred) ** 2)
    if ss_tot == 0:
        return np.nan
    return 1.0 - ss_res / ss_tot


def cohens_f2_from_r2(r2):
    """R-squared -> Cohen's f-squared."""
    if r2 >= 1.0 or np.isnan(r2):
        return np.nan
    return r2 / (1.0 - r2)


def cohens_f2_incremental(r2_full, r2_reduced):
    """증분 Cohen's f-squared (full vs reduced)."""
    denom = 1.0 - r2_full
    if denom <= 0 or np.isnan(r2_full) or np.isnan(r2_reduced):
        return np.nan
    return (r2_full - r2_reduced) / denom


def safe_aic_bic(result, n):
    """혼합효과모형에서 AIC/BIC를 안전하게 추출 (NaN 폴백 포함)."""
    aic_val = result.aic
    bic_val = result.bic
    if np.isnan(aic_val) or np.isnan(bic_val):
        llf = result.llf
        k = result.df_modelwc
        aic_val = -2.0 * llf + 2.0 * k
        bic_val = -2.0 * llf + np.log(n) * k
    return float(aic_val), float(bic_val)


# ============================================================================
# TRACK A: HRV 반응 분석 (합성 데이터)
# ============================================================================

print("=" * 80)
print("TRACK A: 합성 데이터 기반 ACWR → HRV 모형 비교")
print("=" * 80)

# --- 파라미터 ---
N_SUBJECTS = 8
N_DAYS = 90
BETA_0_A = 4.0
BETA_1_A = -0.5
SIGMA_SUBJECT_A = 0.3
SIGMA_NOISE_A = 0.4

# --- 합성 데이터 생성 ---
records_a = []
for subj in range(1, N_SUBJECTS + 1):
    u_j = np.random.normal(0, SIGMA_SUBJECT_A)
    daily_loads = np.random.normal(400, 150, N_DAYS)
    daily_loads = np.clip(daily_loads, 50, 900)
    for d in range(N_DAYS):
        if d % 7 in [5, 6]:
            daily_loads[d] *= 0.5

    loads_series = pd.Series(daily_loads)
    acwr_roll = acwr_rolling(loads_series)
    acwr_ew = acwr_ewma(loads_series)

    for d in range(N_DAYS):
        acwr_val = acwr_roll.iloc[d]
        acwr_ew_val = acwr_ew.iloc[d]
        if pd.isna(acwr_val) or pd.isna(acwr_ew_val):
            continue
        noise = np.random.normal(0, SIGMA_NOISE_A)
        ln_rmssd = BETA_0_A + BETA_1_A * acwr_val + u_j + noise
        records_a.append({
            'subject_id': f'S{subj:02d}',
            'day': d,
            'daily_load': daily_loads[d],
            'acwr_rolling': acwr_val,
            'acwr_ewma': acwr_ew_val,
            'ln_rmssd_next': ln_rmssd,
        })

df_a = pd.DataFrame(records_a)
n_a = len(df_a)
y_a = df_a['ln_rmssd_next'].values

print(f"\n데이터 크기: {df_a.shape}")
print(f"피험자 수: {df_a['subject_id'].nunique()}")
print(f"피험자당 관측 수: {df_a.groupby('subject_id').size().unique()}")
print()
print("--- 기술통계량 ---")
print(df_a[['daily_load', 'acwr_rolling', 'acwr_ewma', 'ln_rmssd_next']].describe().round(4))

# --- 모형 1: OLS (Rolling ACWR) ---
print("\n" + "=" * 60)
print("Track A 모형 1: OLS (ln_rmssd_next ~ acwr_rolling)")
print("=" * 60)

ols_a = smf.ols("ln_rmssd_next ~ acwr_rolling", data=df_a).fit()
ols_a_pred = ols_a.predict(df_a)
ols_a_r2 = ols_a.rsquared
ols_a_aic = ols_a.aic
ols_a_bic = ols_a.bic
ols_a_coef = ols_a.params['acwr_rolling']
ols_a_pval = ols_a.pvalues['acwr_rolling']
ols_a_mae = mean_absolute_error(y_a, ols_a_pred)
ols_a_rmse = np.sqrt(mean_squared_error(y_a, ols_a_pred))
ols_a_f2 = cohens_f2_from_r2(ols_a_r2)

print(f"  R-squared:    {ols_a_r2:.4f}")
print(f"  AIC:          {ols_a_aic:.2f}")
print(f"  BIC:          {ols_a_bic:.2f}")
print(f"  ACWR 계수:    {ols_a_coef:.4f}")
print(f"  p-value:      {ols_a_pval:.4e}")
print(f"  MAE:          {ols_a_mae:.4f}")
print(f"  RMSE:         {ols_a_rmse:.4f}")
print(f"  Cohen's f2:   {ols_a_f2:.4f}")
print(f"  Intercept:    {ols_a.params['Intercept']:.4f}")

# --- 모형 2: Mixed (Rolling ACWR) ---
print("\n" + "=" * 60)
print("Track A 모형 2: Mixed (ln_rmssd_next ~ acwr_rolling + (1|subject_id))")
print("=" * 60)

mixed_roll_a = smf.mixedlm(
    "ln_rmssd_next ~ acwr_rolling",
    data=df_a,
    groups=df_a["subject_id"]
).fit(reml=False)

mr_a_pred = mixed_roll_a.fittedvalues
mr_a_aic, mr_a_bic = safe_aic_bic(mixed_roll_a, n_a)
mr_a_coef = mixed_roll_a.fe_params['acwr_rolling']
mr_a_pval = mixed_roll_a.pvalues['acwr_rolling']
mr_a_mae = mean_absolute_error(y_a, mr_a_pred)
mr_a_rmse = np.sqrt(mean_squared_error(y_a, mr_a_pred))
mr_a_r2 = pseudo_r2(y_a, mr_a_pred.values)
mr_a_f2 = cohens_f2_from_r2(mr_a_r2)
mr_a_re_var = mixed_roll_a.cov_re.iloc[0, 0] if hasattr(mixed_roll_a.cov_re, 'iloc') else float(mixed_roll_a.cov_re)

print(mixed_roll_a.summary())
print(f"\n  AIC:          {mr_a_aic:.2f}")
print(f"  BIC:          {mr_a_bic:.2f}")
print(f"  ACWR 계수:    {mr_a_coef:.4f}")
print(f"  p-value:      {mr_a_pval:.4e}")
print(f"  MAE:          {mr_a_mae:.4f}")
print(f"  RMSE:         {mr_a_rmse:.4f}")
print(f"  R2 (pseudo):  {mr_a_r2:.4f}")
print(f"  Cohen's f2:   {mr_a_f2:.4f}")
print(f"  RE Var:       {mr_a_re_var:.4f}")
print(f"  Intercept:    {mixed_roll_a.fe_params['Intercept']:.4f}")

# --- 모형 3: Mixed (EWMA ACWR) ---
print("\n" + "=" * 60)
print("Track A 모형 3: Mixed (ln_rmssd_next ~ acwr_ewma + (1|subject_id))")
print("=" * 60)

mixed_ewma_a = smf.mixedlm(
    "ln_rmssd_next ~ acwr_ewma",
    data=df_a,
    groups=df_a["subject_id"]
).fit(reml=False)

me_a_pred = mixed_ewma_a.fittedvalues
me_a_aic, me_a_bic = safe_aic_bic(mixed_ewma_a, n_a)
me_a_coef = mixed_ewma_a.fe_params['acwr_ewma']
me_a_pval = mixed_ewma_a.pvalues['acwr_ewma']
me_a_mae = mean_absolute_error(y_a, me_a_pred)
me_a_rmse = np.sqrt(mean_squared_error(y_a, me_a_pred))
me_a_r2 = pseudo_r2(y_a, me_a_pred.values)
me_a_f2 = cohens_f2_from_r2(me_a_r2)
me_a_re_var = mixed_ewma_a.cov_re.iloc[0, 0] if hasattr(mixed_ewma_a.cov_re, 'iloc') else float(mixed_ewma_a.cov_re)

print(mixed_ewma_a.summary())
print(f"\n  AIC:          {me_a_aic:.2f}")
print(f"  BIC:          {me_a_bic:.2f}")
print(f"  ACWR 계수:    {me_a_coef:.4f}")
print(f"  p-value:      {me_a_pval:.4e}")
print(f"  MAE:          {me_a_mae:.4f}")
print(f"  RMSE:         {me_a_rmse:.4f}")
print(f"  R2 (pseudo):  {me_a_r2:.4f}")
print(f"  Cohen's f2:   {me_a_f2:.4f}")
print(f"  RE Var:       {me_a_re_var:.4f}")
print(f"  Intercept:    {mixed_ewma_a.fe_params['Intercept']:.4f}")

# --- Track A 비교 요약표 ---
print("\n" + "=" * 80)
print("TRACK A: 모형 비교 요약표")
print("=" * 80)

comp_a = pd.DataFrame({
    'Model': ['OLS (Rolling)', 'Mixed (Rolling)', 'Mixed (EWMA)'],
    'AIC': [ols_a_aic, mr_a_aic, me_a_aic],
    'BIC': [ols_a_bic, mr_a_bic, me_a_bic],
    'MAE': [ols_a_mae, mr_a_mae, me_a_mae],
    'RMSE': [ols_a_rmse, mr_a_rmse, me_a_rmse],
    'Coef_ACWR': [ols_a_coef, mr_a_coef, me_a_coef],
    'p_value': [ols_a_pval, mr_a_pval, me_a_pval],
    'R2': [ols_a_r2, mr_a_r2, me_a_r2],
    'Cohens_f2': [ols_a_f2, mr_a_f2, me_a_f2],
})

print(comp_a.to_string(index=False, float_format='%.4f'))


# ============================================================================
# TRACK B: 부하-웰니스 분석 (합성 데이터)
# ============================================================================

print("\n\n" + "=" * 80)
print("TRACK B: 합성 데이터 기반 ACWR+Monotony → Hooper 모형 비교")
print("=" * 80)

# --- 파라미터 ---
N_ATHLETES = 12
N_DAYS_B = 120
BETA_0_B = 12.0
BETA_ACWR_B = 2.5
BETA_MONO_B = 1.5
SIGMA_ATHLETE_B = 1.5
SIGMA_NOISE_B = 1.8

# --- 합성 데이터 생성 ---
athlete_ids = [f'A{i+1:02d}' for i in range(N_ATHLETES)]
athlete_effects = {aid: np.random.normal(0, SIGMA_ATHLETE_B) for aid in athlete_ids}

records_b = []
for aid in athlete_ids:
    base_load = np.random.normal(400, 80, size=N_DAYS_B).clip(50)
    days = np.arange(N_DAYS_B)
    day_of_week = days % 7
    weekend_mask = (day_of_week >= 5)
    base_load[weekend_mask] *= 0.5

    loads_series = pd.Series(base_load, name='daily_load')

    acwr_r = acwr_rolling(loads_series)
    acwr_e = acwr_ewma(loads_series)
    mono = monotony(loads_series)
    strn = strain(loads_series)

    for d in range(N_DAYS_B):
        acwr_r_val = acwr_r.iloc[d]
        acwr_e_val = acwr_e.iloc[d]
        mono_val = mono.iloc[d]
        strn_val = strn.iloc[d]

        if np.isnan(acwr_r_val) or np.isnan(mono_val):
            hooper_next = np.nan
        else:
            hooper_next = (
                BETA_0_B
                + BETA_ACWR_B * acwr_r_val
                + BETA_MONO_B * mono_val
                + athlete_effects[aid]
                + np.random.normal(0, SIGMA_NOISE_B)
            )

        records_b.append({
            'athlete_id': aid,
            'day': d,
            'daily_load': base_load[d],
            'acwr_rolling': acwr_r_val,
            'acwr_ewma': acwr_e_val,
            'monotony': mono_val,
            'strain': strn_val,
            'hooper_next': hooper_next,
        })

df_b = pd.DataFrame(records_b)
df_b_clean = df_b.dropna(subset=['acwr_rolling', 'acwr_ewma', 'monotony', 'hooper_next']).copy()
df_b_clean.reset_index(drop=True, inplace=True)
n_b = len(df_b_clean)
y_b = df_b_clean['hooper_next'].values

print(f"\n전체 레코드: {len(df_b)}  |  분석 대상 (워밍업 제거 후): {n_b}")
print(f"선수 수: {df_b_clean['athlete_id'].nunique()}")
print()
print("--- 기술통계량 ---")
print(df_b_clean[['daily_load', 'acwr_rolling', 'acwr_ewma', 'monotony', 'strain', 'hooper_next']].describe().round(4))

# --- 모형 1 (M1): OLS (ACWR Rolling) ---
print("\n" + "=" * 60)
print("Track B M1: OLS (hooper_next ~ acwr_rolling)")
print("=" * 60)

m1_b = smf.ols('hooper_next ~ acwr_rolling', data=df_b_clean).fit()
m1_b_pred = m1_b.predict(df_b_clean)
m1_b_r2 = m1_b.rsquared
m1_b_aic = m1_b.aic
m1_b_bic = m1_b.bic
m1_b_coef = m1_b.params['acwr_rolling']
m1_b_pval = m1_b.pvalues['acwr_rolling']
m1_b_mae = mean_absolute_error(y_b, m1_b_pred)
m1_b_rmse = np.sqrt(mean_squared_error(y_b, m1_b_pred))
m1_b_f2 = cohens_f2_from_r2(m1_b_r2)

print(f"  R-squared:    {m1_b_r2:.4f}")
print(f"  AIC:          {m1_b_aic:.2f}")
print(f"  BIC:          {m1_b_bic:.2f}")
print(f"  ACWR 계수:    {m1_b_coef:.4f}")
print(f"  p-value:      {m1_b_pval:.4e}")
print(f"  MAE:          {m1_b_mae:.4f}")
print(f"  RMSE:         {m1_b_rmse:.4f}")
print(f"  Cohen's f2:   {m1_b_f2:.4f}")
print(f"  Intercept:    {m1_b.params['Intercept']:.4f}")

# --- 모형 2 (M2): Mixed (ACWR Rolling) ---
print("\n" + "=" * 60)
print("Track B M2: Mixed (hooper_next ~ acwr_rolling + (1|athlete_id))")
print("=" * 60)

m2_b = smf.mixedlm(
    'hooper_next ~ acwr_rolling',
    data=df_b_clean,
    groups='athlete_id',
).fit(reml=False)

m2_b_pred = m2_b.fittedvalues
m2_b_aic, m2_b_bic = safe_aic_bic(m2_b, n_b)
m2_b_coef = m2_b.fe_params['acwr_rolling']
m2_b_pval = m2_b.pvalues['acwr_rolling']
m2_b_mae = mean_absolute_error(y_b, m2_b_pred)
m2_b_rmse = np.sqrt(mean_squared_error(y_b, m2_b_pred))
m2_b_r2 = pseudo_r2(y_b, m2_b_pred.values)
m2_b_f2 = cohens_f2_from_r2(m2_b_r2)
m2_b_re_var = m2_b.cov_re.iloc[0, 0] if hasattr(m2_b.cov_re, 'iloc') else float(m2_b.cov_re)

print(m2_b.summary())
print(f"\n  AIC:          {m2_b_aic:.2f}")
print(f"  BIC:          {m2_b_bic:.2f}")
print(f"  ACWR 계수:    {m2_b_coef:.4f}")
print(f"  p-value:      {m2_b_pval:.4e}")
print(f"  MAE:          {m2_b_mae:.4f}")
print(f"  RMSE:         {m2_b_rmse:.4f}")
print(f"  R2 (pseudo):  {m2_b_r2:.4f}")
print(f"  Cohen's f2:   {m2_b_f2:.4f}")
print(f"  RE Var:       {m2_b_re_var:.4f}")
print(f"  Intercept:    {m2_b.fe_params['Intercept']:.4f}")

# --- 모형 3 (M3): Mixed (ACWR Rolling + Monotony) ---
print("\n" + "=" * 60)
print("Track B M3: Mixed (hooper_next ~ acwr_rolling + monotony + (1|athlete_id))")
print("=" * 60)

m3_b = smf.mixedlm(
    'hooper_next ~ acwr_rolling + monotony',
    data=df_b_clean,
    groups='athlete_id',
).fit(reml=False)

m3_b_pred = m3_b.fittedvalues
m3_b_aic, m3_b_bic = safe_aic_bic(m3_b, n_b)
m3_b_acwr_coef = m3_b.fe_params['acwr_rolling']
m3_b_acwr_pval = m3_b.pvalues['acwr_rolling']
m3_b_mono_coef = m3_b.fe_params['monotony']
m3_b_mono_pval = m3_b.pvalues['monotony']
m3_b_mae = mean_absolute_error(y_b, m3_b_pred)
m3_b_rmse = np.sqrt(mean_squared_error(y_b, m3_b_pred))
m3_b_r2 = pseudo_r2(y_b, m3_b_pred.values)
m3_b_f2 = cohens_f2_from_r2(m3_b_r2)
m3_b_re_var = m3_b.cov_re.iloc[0, 0] if hasattr(m3_b.cov_re, 'iloc') else float(m3_b.cov_re)

print(m3_b.summary())
print(f"\n  AIC:              {m3_b_aic:.2f}")
print(f"  BIC:              {m3_b_bic:.2f}")
print(f"  ACWR 계수:        {m3_b_acwr_coef:.4f}")
print(f"  ACWR p-value:     {m3_b_acwr_pval:.4e}")
print(f"  Monotony 계수:    {m3_b_mono_coef:.4f}")
print(f"  Monotony p-value: {m3_b_mono_pval:.4e}")
print(f"  MAE:              {m3_b_mae:.4f}")
print(f"  RMSE:             {m3_b_rmse:.4f}")
print(f"  R2 (pseudo):      {m3_b_r2:.4f}")
print(f"  Cohen's f2:       {m3_b_f2:.4f}")
print(f"  RE Var:           {m3_b_re_var:.4f}")
print(f"  Intercept:        {m3_b.fe_params['Intercept']:.4f}")

# --- 모형 4 (M4): Mixed (EWMA ACWR + Monotony) ---
print("\n" + "=" * 60)
print("Track B M4: Mixed (hooper_next ~ acwr_ewma + monotony + (1|athlete_id))")
print("=" * 60)

m4_b = smf.mixedlm(
    'hooper_next ~ acwr_ewma + monotony',
    data=df_b_clean,
    groups='athlete_id',
).fit(reml=False)

m4_b_pred = m4_b.fittedvalues
m4_b_aic, m4_b_bic = safe_aic_bic(m4_b, n_b)
m4_b_acwr_coef = m4_b.fe_params['acwr_ewma']
m4_b_acwr_pval = m4_b.pvalues['acwr_ewma']
m4_b_mono_coef = m4_b.fe_params['monotony']
m4_b_mono_pval = m4_b.pvalues['monotony']
m4_b_mae = mean_absolute_error(y_b, m4_b_pred)
m4_b_rmse = np.sqrt(mean_squared_error(y_b, m4_b_pred))
m4_b_r2 = pseudo_r2(y_b, m4_b_pred.values)
m4_b_f2 = cohens_f2_from_r2(m4_b_r2)
m4_b_re_var = m4_b.cov_re.iloc[0, 0] if hasattr(m4_b.cov_re, 'iloc') else float(m4_b.cov_re)

print(m4_b.summary())
print(f"\n  AIC:              {m4_b_aic:.2f}")
print(f"  BIC:              {m4_b_bic:.2f}")
print(f"  ACWR(EWMA) 계수:  {m4_b_acwr_coef:.4f}")
print(f"  ACWR p-value:     {m4_b_acwr_pval:.4e}")
print(f"  Monotony 계수:    {m4_b_mono_coef:.4f}")
print(f"  Monotony p-value: {m4_b_mono_pval:.4e}")
print(f"  MAE:              {m4_b_mae:.4f}")
print(f"  RMSE:             {m4_b_rmse:.4f}")
print(f"  R2 (pseudo):      {m4_b_r2:.4f}")
print(f"  Cohen's f2:       {m4_b_f2:.4f}")
print(f"  RE Var:           {m4_b_re_var:.4f}")
print(f"  Intercept:        {m4_b.fe_params['Intercept']:.4f}")

# --- Track B 비교 요약표 ---
print("\n" + "=" * 80)
print("TRACK B: 모형 비교 요약표")
print("=" * 80)

comp_b = pd.DataFrame({
    'Model': ['M1: OLS(ACWR)', 'M2: Mixed(ACWR)', 'M3: Mixed(ACWR+Mono)', 'M4: Mixed(EWMA+Mono)'],
    'AIC': [m1_b_aic, m2_b_aic, m3_b_aic, m4_b_aic],
    'BIC': [m1_b_bic, m2_b_bic, m3_b_bic, m4_b_bic],
    'MAE': [m1_b_mae, m2_b_mae, m3_b_mae, m4_b_mae],
    'RMSE': [m1_b_rmse, m2_b_rmse, m3_b_rmse, m4_b_rmse],
    'R2': [m1_b_r2, m2_b_r2, m3_b_r2, m4_b_r2],
    'ACWR_coef': [m1_b_coef, m2_b_coef, m3_b_acwr_coef, m4_b_acwr_coef],
    'ACWR_p': [m1_b_pval, m2_b_pval, m3_b_acwr_pval, m4_b_acwr_pval],
    'Mono_coef': [np.nan, np.nan, m3_b_mono_coef, m4_b_mono_coef],
    'Mono_p': [np.nan, np.nan, m3_b_mono_pval, m4_b_mono_pval],
    'f2_vs_null': [m1_b_f2, m2_b_f2, m3_b_f2, m4_b_f2],
    'f2_vs_M1': [0.0,
                 cohens_f2_incremental(m2_b_r2, m1_b_r2),
                 cohens_f2_incremental(m3_b_r2, m1_b_r2),
                 cohens_f2_incremental(m4_b_r2, m1_b_r2)],
})

print(comp_b.to_string(index=False, float_format='%.4f'))


# ============================================================================
# 최종 요약
# ============================================================================

print("\n\n" + "=" * 80)
print("최종 요약: 전체 수치 목록 (보고서 기입용)")
print("=" * 80)

print("\n[Track A]")
print(f"  참값: beta_0={BETA_0_A}, beta_1={BETA_1_A}, sigma_subject={SIGMA_SUBJECT_A}, sigma_noise={SIGMA_NOISE_A}")
print(f"  관측수={n_a}, 피험자수={N_SUBJECTS}")
print(f"  OLS:    AIC={ols_a_aic:.2f}, BIC={ols_a_bic:.2f}, R2={ols_a_r2:.4f}, MAE={ols_a_mae:.4f}, RMSE={ols_a_rmse:.4f}, coef={ols_a_coef:.4f}, p={ols_a_pval:.4e}, f2={ols_a_f2:.4f}, intercept={ols_a.params['Intercept']:.4f}")
print(f"  Mixed(Roll): AIC={mr_a_aic:.2f}, BIC={mr_a_bic:.2f}, R2={mr_a_r2:.4f}, MAE={mr_a_mae:.4f}, RMSE={mr_a_rmse:.4f}, coef={mr_a_coef:.4f}, p={mr_a_pval:.4e}, f2={mr_a_f2:.4f}, RE_var={mr_a_re_var:.4f}, intercept={mixed_roll_a.fe_params['Intercept']:.4f}")
print(f"  Mixed(EWMA): AIC={me_a_aic:.2f}, BIC={me_a_bic:.2f}, R2={me_a_r2:.4f}, MAE={me_a_mae:.4f}, RMSE={me_a_rmse:.4f}, coef={me_a_coef:.4f}, p={me_a_pval:.4e}, f2={me_a_f2:.4f}, RE_var={me_a_re_var:.4f}, intercept={mixed_ewma_a.fe_params['Intercept']:.4f}")

print("\n[Track B]")
print(f"  참값: beta_0={BETA_0_B}, beta_acwr={BETA_ACWR_B}, beta_monotony={BETA_MONO_B}, sigma_athlete={SIGMA_ATHLETE_B}, sigma_noise={SIGMA_NOISE_B}")
print(f"  관측수={n_b}, 선수수={N_ATHLETES}")
print(f"  M1(OLS):          AIC={m1_b_aic:.2f}, BIC={m1_b_bic:.2f}, R2={m1_b_r2:.4f}, MAE={m1_b_mae:.4f}, RMSE={m1_b_rmse:.4f}, ACWR_coef={m1_b_coef:.4f}, p={m1_b_pval:.4e}, f2={m1_b_f2:.4f}, intercept={m1_b.params['Intercept']:.4f}")
print(f"  M2(Mixed ACWR):   AIC={m2_b_aic:.2f}, BIC={m2_b_bic:.2f}, R2={m2_b_r2:.4f}, MAE={m2_b_mae:.4f}, RMSE={m2_b_rmse:.4f}, ACWR_coef={m2_b_coef:.4f}, p={m2_b_pval:.4e}, f2={m2_b_f2:.4f}, RE_var={m2_b_re_var:.4f}, intercept={m2_b.fe_params['Intercept']:.4f}")
print(f"  M3(Mixed ACWR+M): AIC={m3_b_aic:.2f}, BIC={m3_b_bic:.2f}, R2={m3_b_r2:.4f}, MAE={m3_b_mae:.4f}, RMSE={m3_b_rmse:.4f}, ACWR_coef={m3_b_acwr_coef:.4f}(p={m3_b_acwr_pval:.4e}), Mono_coef={m3_b_mono_coef:.4f}(p={m3_b_mono_pval:.4e}), f2={m3_b_f2:.4f}, RE_var={m3_b_re_var:.4f}, intercept={m3_b.fe_params['Intercept']:.4f}")
print(f"  M4(Mixed EWMA+M): AIC={m4_b_aic:.2f}, BIC={m4_b_bic:.2f}, R2={m4_b_r2:.4f}, MAE={m4_b_mae:.4f}, RMSE={m4_b_rmse:.4f}, ACWR_coef={m4_b_acwr_coef:.4f}(p={m4_b_acwr_pval:.4e}), Mono_coef={m4_b_mono_coef:.4f}(p={m4_b_mono_pval:.4e}), f2={m4_b_f2:.4f}, RE_var={m4_b_re_var:.4f}, intercept={m4_b.fe_params['Intercept']:.4f}")

print("\n스크립트 완료.")
