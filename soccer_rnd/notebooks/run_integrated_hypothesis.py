"""
통합 합성 데이터 가설 검증 실행 스크립트.

실제 데이터 분석에서 도출된 세 가지 핵심 발견을 합성 데이터로 검증한다:
  H1: 개인화된 기저선 추적의 중요성 (OLS vs Mixed)
  H2: 다중 지표 통합 모니터링 우위 (부하 단독 vs 부하+HRV)
  H3: Monotony 독립 효과 및 억제변수 재현
  H4: 결측 민감도 분석 (100회 Monte Carlo)

실행 방법:
  python notebooks/run_integrated_hypothesis.py
"""

import sys
import os
import warnings
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data.synthetic_integrated import (
    DEFAULT_PARAMS,
    generate_integrated_dataset,
    inject_missingness,
)
from src.stats.mixed_effects import (
    fit_random_intercept,
    extract_model_metrics,
    compare_models,
)
from src.stats.cross_validation import loso_cv, loso_summary

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

# ---------------------------------------------------------------------------
# 0. 파라미터 및 데이터 생성
# ---------------------------------------------------------------------------

PARAMS = DEFAULT_PARAMS.copy()
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("통합 합성 데이터 가설 검증 실험")
print("=" * 70)
print(f"선수 수: {PARAMS['n_athletes']}, 기간: {PARAMS['n_days']}일, seed: {PARAMS['seed']}")
print()

print("[0] 통합 데이터셋 생성 중...")
df_complete, random_effects = generate_integrated_dataset(PARAMS, return_complete=True)
print(f"  총 행수: {len(df_complete)}")
print(f"  선수 수: {df_complete['athlete'].nunique()}")

# 분석용 데이터: warmup 제거 + 완전 관측
df_valid = df_complete.dropna(subset=[
    "acwr_ra", "mono", "strain_val",
    "hooper_next", "ln_rmssd", "ln_rmssd_next",
]).copy().reset_index(drop=True)
print(f"  유효 관측수 (warmup 제거): {len(df_valid)}")
print()


# ===========================================================================
# H1: 개인화된 기저선 추적의 중요성
# ===========================================================================

print("=" * 70)
print("[H1] 개인화된 기저선 추적의 중요성")
print("=" * 70)

# --- H1a: Hooper 모형 ---
print("\n--- H1a: Hooper 결과변수 ---")

# OLS
ols_hooper = sm.OLS.from_formula(
    "hooper_next ~ acwr_ra + mono + strain_val",
    data=df_valid,
).fit()
ols_aic_hooper = ols_hooper.aic
ols_r2_hooper = ols_hooper.rsquared

# Mixed (Random Intercept)
mixed_hooper = fit_random_intercept(
    "hooper_next ~ acwr_ra + mono + strain_val",
    df_valid,
    "athlete",
)
mixed_metrics_hooper = extract_model_metrics(mixed_hooper, df_valid, "hooper_next")
mixed_aic_hooper = mixed_metrics_hooper["aic"]

# Mixed R² 계산
y_true_hooper = df_valid["hooper_next"].values
y_pred_hooper = mixed_hooper.fittedvalues.values
ss_res_hooper = np.sum((y_true_hooper - y_pred_hooper) ** 2)
ss_tot_hooper = np.sum((y_true_hooper - y_true_hooper.mean()) ** 2)
mixed_r2_hooper = 1.0 - ss_res_hooper / ss_tot_hooper

# ICC 계산
re_var_hooper = float(np.diag(np.atleast_2d(mixed_hooper.cov_re))[0])
resid_var_hooper = mixed_hooper.scale
icc_hooper = re_var_hooper / (re_var_hooper + resid_var_hooper)

print(f"  OLS AIC:   {ols_aic_hooper:.1f},  R²: {ols_r2_hooper:.4f}")
print(f"  Mixed AIC: {mixed_aic_hooper:.1f},  R²: {mixed_r2_hooper:.4f}")
print(f"  ΔAIC:      {ols_aic_hooper - mixed_aic_hooper:.1f}")
print(f"  ICC(Hooper): {icc_hooper:.4f}")

# --- H1b: HRV 모형 ---
print("\n--- H1b: HRV 결과변수 ---")

ols_hrv = sm.OLS.from_formula(
    "ln_rmssd_next ~ acwr_ra + mono",
    data=df_valid,
).fit()
ols_aic_hrv = ols_hrv.aic
ols_r2_hrv = ols_hrv.rsquared

mixed_hrv = fit_random_intercept(
    "ln_rmssd_next ~ acwr_ra + mono",
    df_valid,
    "athlete",
)
mixed_metrics_hrv = extract_model_metrics(mixed_hrv, df_valid, "ln_rmssd_next")
mixed_aic_hrv = mixed_metrics_hrv["aic"]

y_true_hrv = df_valid["ln_rmssd_next"].values
y_pred_hrv = mixed_hrv.fittedvalues.values
ss_res_hrv = np.sum((y_true_hrv - y_pred_hrv) ** 2)
ss_tot_hrv = np.sum((y_true_hrv - y_true_hrv.mean()) ** 2)
mixed_r2_hrv = 1.0 - ss_res_hrv / ss_tot_hrv

re_var_hrv = float(np.diag(np.atleast_2d(mixed_hrv.cov_re))[0])
resid_var_hrv = mixed_hrv.scale
icc_hrv = re_var_hrv / (re_var_hrv + resid_var_hrv)

print(f"  OLS AIC:   {ols_aic_hrv:.1f},  R²: {ols_r2_hrv:.4f}")
print(f"  Mixed AIC: {mixed_aic_hrv:.1f},  R²: {mixed_r2_hrv:.4f}")
print(f"  ΔAIC:      {ols_aic_hrv - mixed_aic_hrv:.1f}")
print(f"  ICC(HRV):  {icc_hrv:.4f}")

# --- H1c: LOSO 교차 검증 ---
print("\n--- H1c: LOSO 교차 검증 ---")

loso_mixed_hooper = loso_cv(
    "hooper_next ~ acwr_ra + mono + strain_val",
    df_valid, "athlete", "hooper_next",
)
loso_mixed_summary = loso_summary(loso_mixed_hooper)

# OLS 전체 데이터 MAE
ols_mae_hooper = float(np.mean(np.abs(ols_hooper.resid)))

print(f"  OLS 전체 MAE:     {ols_mae_hooper:.4f}")
print(f"  Mixed LOSO MAE:   {loso_mixed_summary['mean_mae']:.4f}")

# --- H1 Pass/Fail 판정 ---
print("\n--- H1 판정 ---")
h1_results = {}

# ΔAIC > 100 (Hooper)
h1_delta_aic = ols_aic_hooper - mixed_aic_hooper
h1_results["AIC_차이_Hooper"] = {
    "값": f"{h1_delta_aic:.1f}",
    "기준": "ΔAIC > 100",
    "판정": "PASS" if h1_delta_aic > 100 else "FAIL",
}

# R² 도약
h1_results["R2_도약"] = {
    "값": f"OLS={ols_r2_hooper:.4f}, Mixed={mixed_r2_hooper:.4f}",
    "기준": "OLS R² < 0.05 AND Mixed R² > 0.30",
    "판정": "PASS" if ols_r2_hooper < 0.05 and mixed_r2_hooper > 0.30 else "FAIL",
}

# ICC 순서
h1_results["ICC_순서"] = {
    "값": f"Hooper={icc_hooper:.4f}, HRV={icc_hrv:.4f}",
    "기준": "ICC_hooper > ICC_hrv",
    "판정": "PASS" if icc_hooper > icc_hrv else "FAIL",
}

# LOSO MAE
h1_results["LOSO_MAE"] = {
    "값": f"Mixed LOSO={loso_mixed_summary['mean_mae']:.4f}, OLS 전체={ols_mae_hooper:.4f}",
    "기준": "Mixed LOSO MAE > OLS 전체 MAE",
    "판정": "PASS" if loso_mixed_summary["mean_mae"] > ols_mae_hooper else "FAIL",
}

for name, res in h1_results.items():
    print(f"  [{res['판정']}] {name}: {res['값']} (기준: {res['기준']})")

h1_pass_count = sum(1 for r in h1_results.values() if r["판정"] == "PASS")
print(f"\n  H1 종합: {h1_pass_count}/{len(h1_results)} PASS")


# ===========================================================================
# H2: 다중 지표 통합 모니터링 우위
# ===========================================================================

print("\n" + "=" * 70)
print("[H2] 다중 지표 통합 모니터링 우위")
print("=" * 70)

# M_load: 부하 단독
m_load = fit_random_intercept(
    "hooper_next ~ acwr_ra + mono + strain_val",
    df_valid,
    "athlete",
)
m_load_metrics = extract_model_metrics(m_load, df_valid, "hooper_next")

# M_integrated: 부하 + HRV
m_integrated = fit_random_intercept(
    "hooper_next ~ acwr_ra + mono + strain_val + ln_rmssd",
    df_valid,
    "athlete",
)
m_integrated_metrics = extract_model_metrics(m_integrated, df_valid, "hooper_next")

# R² 계산
y_true = df_valid["hooper_next"].values
ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))

y_pred_load = m_load.fittedvalues.values
r2_load = 1.0 - np.sum((y_true - y_pred_load) ** 2) / ss_tot

y_pred_int = m_integrated.fittedvalues.values
r2_int = 1.0 - np.sum((y_true - y_pred_int) ** 2) / ss_tot

# 증분 Cohen's f²
cohens_f2 = (r2_int - r2_load) / (1.0 - r2_int) if r2_int < 1.0 else np.nan

print(f"  M_load AIC:       {m_load_metrics['aic']:.1f},  R²: {r2_load:.4f}")
print(f"  M_integrated AIC: {m_integrated_metrics['aic']:.1f},  R²: {r2_int:.4f}")
print(f"  ΔAIC:             {m_load_metrics['aic'] - m_integrated_metrics['aic']:.1f}")
print(f"  증분 Cohen's f²:  {cohens_f2:.4f}")

# LOSO CV 비교
print("\n--- H2 LOSO CV 비교 ---")
loso_load = loso_cv(
    "hooper_next ~ acwr_ra + mono + strain_val",
    df_valid, "athlete", "hooper_next",
)
loso_load_summary = loso_summary(loso_load)

loso_int = loso_cv(
    "hooper_next ~ acwr_ra + mono + strain_val + ln_rmssd",
    df_valid, "athlete", "hooper_next",
)
loso_int_summary = loso_summary(loso_int)

mae_improvement = (
    (loso_load_summary["mean_mae"] - loso_int_summary["mean_mae"])
    / loso_load_summary["mean_mae"] * 100
)

print(f"  M_load LOSO MAE:       {loso_load_summary['mean_mae']:.4f}")
print(f"  M_integrated LOSO MAE: {loso_int_summary['mean_mae']:.4f}")
print(f"  MAE 개선율:             {mae_improvement:.1f}%")

# --- H2 Pass/Fail 판정 ---
print("\n--- H2 판정 ---")
h2_results = {}

h2_delta_aic = m_load_metrics["aic"] - m_integrated_metrics["aic"]
h2_results["AIC_차이"] = {
    "값": f"{h2_delta_aic:.1f}",
    "기준": "ΔAIC > 4",
    "판정": "PASS" if h2_delta_aic > 4 else "FAIL",
}

h2_results["Cohen_f2"] = {
    "값": f"{cohens_f2:.4f}",
    "기준": "f² > 0.02",
    "판정": "PASS" if cohens_f2 > 0.02 else "FAIL",
}

h2_results["LOSO_MAE_개선"] = {
    "값": f"{mae_improvement:.1f}%",
    "기준": "MAE 5% 이상 개선",
    "판정": "PASS" if mae_improvement > 5 else "FAIL",
}

for name, res in h2_results.items():
    print(f"  [{res['판정']}] {name}: {res['값']} (기준: {res['기준']})")

h2_pass_count = sum(1 for r in h2_results.values() if r["판정"] == "PASS")
print(f"\n  H2 종합: {h2_pass_count}/{len(h2_results)} PASS")


# ===========================================================================
# H3: Monotony 독립 효과 및 억제변수 재현
# ===========================================================================

print("\n" + "=" * 70)
print("[H3] Monotony 독립 효과 및 억제변수 재현")
print("=" * 70)

# 순차 투입 (ln_rmssd는 DGP에 포함된 예측변수이므로 모형에 포함)
# Step 1: ACWR only
m_step1 = fit_random_intercept(
    "hooper_next ~ acwr_ra + ln_rmssd",
    df_valid,
    "athlete",
)

# Step 2: ACWR + Monotony
m_step2 = fit_random_intercept(
    "hooper_next ~ acwr_ra + mono + ln_rmssd",
    df_valid,
    "athlete",
)

# Step 3: ACWR + Monotony + Strain (full model)
m_step3 = fit_random_intercept(
    "hooper_next ~ acwr_ra + mono + strain_val + ln_rmssd",
    df_valid,
    "athlete",
)

# Step 4: EWMA 변형
m_step4 = fit_random_intercept(
    "hooper_next ~ acwr_ew + mono + strain_val + ln_rmssd",
    df_valid,
    "athlete",
)

# 결과 추출
beta_mono_step2 = m_step2.fe_params.get("mono", np.nan)
beta_mono_step3 = m_step3.fe_params.get("mono", np.nan)
p_mono_step3 = m_step3.pvalues.get("mono", np.nan)

print(f"  Step 1 (ACWR+HRV):                ACWR β = {m_step1.fe_params.get('acwr_ra', np.nan):.4f}")
print(f"  Step 2 (ACWR+Mono+HRV):           Mono β = {beta_mono_step2:.4f}")
print(f"  Step 3 (ACWR+Mono+Strain+HRV):    Mono β = {beta_mono_step3:.4f}, p = {p_mono_step3:.4f}")
print(f"  Step 4 (EWMA+Mono+Strain+HRV):    Mono β = {m_step4.fe_params.get('mono', np.nan):.4f}")
print(f"  HRV β (Step 3):                   {m_step3.fe_params.get('ln_rmssd', np.nan):.4f}")

# 억제변수 효과: Strain 투입 전/후 Mono 계수 변화
if beta_mono_step2 != 0:
    suppressor_effect = abs(beta_mono_step3 - beta_mono_step2) / abs(beta_mono_step2) * 100
else:
    suppressor_effect = 0.0

# 참값 복원
true_mono = PARAMS["beta_mono_hooper"]
recovery_error = abs(beta_mono_step3 - true_mono) / abs(true_mono) if true_mono != 0 else np.nan

print(f"\n  억제변수 효과 (Mono 계수 변화): {suppressor_effect:.1f}%")
print(f"  참값 복원 오차: |{beta_mono_step3:.4f} - {true_mono}| / |{true_mono}| = {recovery_error:.2%}")

# VIF 점검
print("\n--- VIF 점검 ---")
X_vif = df_valid[["acwr_ra", "mono", "strain_val", "ln_rmssd"]].copy()
X_vif = sm.add_constant(X_vif)
for i, col in enumerate(X_vif.columns):
    if col == "const":
        continue
    vif = variance_inflation_factor(X_vif.values, i)
    flag = " ⚠ VIF>10" if vif > 10 else ""
    print(f"  {col}: VIF = {vif:.2f}{flag}")

# --- H3 Pass/Fail 판정 ---
print("\n--- H3 판정 ---")
h3_results = {}

h3_results["Mono_유의성"] = {
    "값": f"p = {p_mono_step3:.4f}",
    "기준": "p < 0.05",
    "판정": "PASS" if p_mono_step3 < 0.05 else "FAIL",
}

h3_results["억제변수_효과"] = {
    "값": f"{suppressor_effect:.1f}%",
    "기준": "Strain 전/후 Mono 계수 변화 > 50%",
    "판정": "PASS" if suppressor_effect > 50 else "FAIL",
}

h3_results["참값_복원"] = {
    "값": f"{recovery_error:.2%}",
    "기준": "|β_mono - 0.14| / 0.14 < 0.30",
    "판정": "PASS" if recovery_error < 0.30 else "FAIL",
}

for name, res in h3_results.items():
    print(f"  [{res['판정']}] {name}: {res['값']} (기준: {res['기준']})")

h3_pass_count = sum(1 for r in h3_results.values() if r["판정"] == "PASS")
print(f"\n  H3 종합: {h3_pass_count}/{len(h3_results)} PASS")


# ===========================================================================
# H4: 결측 민감도 분석 (100회 Monte Carlo)
# ===========================================================================

print("\n" + "=" * 70)
print("[H4] 결측 민감도 분석 (100회 Monte Carlo)")
print("=" * 70)

N_MC = 100
TRUE_MONO = PARAMS["beta_mono_hooper"]
MECHANISMS = ["complete", "mcar", "mar", "mnar"]

mc_results = {m: {"beta_mono": [], "beta_acwr": [], "ci_lower": [], "ci_upper": []}
              for m in MECHANISMS}

print(f"  시뮬레이션 횟수: {N_MC}")
print(f"  메커니즘: {MECHANISMS}")
print()

for i in range(N_MC):
    if (i + 1) % 20 == 0:
        print(f"  진행: {i + 1}/{N_MC}...")

    # 각 반복마다 다른 seed로 데이터 생성
    iter_params = PARAMS.copy()
    iter_params["seed"] = PARAMS["seed"] + i
    df_iter = generate_integrated_dataset(iter_params)
    df_iter_valid = df_iter.dropna(subset=[
        "acwr_ra", "mono", "strain_val", "hooper_next", "ln_rmssd",
    ]).copy()

    for mechanism in MECHANISMS:
        if mechanism == "complete":
            df_analysis = df_iter_valid
        else:
            mc_rng = np.random.default_rng(PARAMS["seed"] * 1000 + i)
            df_analysis = inject_missingness(
                df_iter_valid, mc_rng, mechanism, PARAMS,
            )
            df_analysis = df_analysis.dropna(subset=["hooper_next"])

        if len(df_analysis) < 100:
            continue

        try:
            model = smf.mixedlm(
                "hooper_next ~ acwr_ra + mono + strain_val + ln_rmssd",
                data=df_analysis,
                groups=df_analysis["athlete"],
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = model.fit(reml=False)

            beta_mono_est = result.fe_params.get("mono", np.nan)
            beta_acwr_est = result.fe_params.get("acwr_ra", np.nan)

            # 95% 신뢰구간
            ci = result.conf_int(alpha=0.05)
            if "mono" in ci.index:
                ci_lower = ci.loc["mono", 0]
                ci_upper = ci.loc["mono", 1]
            else:
                ci_lower = np.nan
                ci_upper = np.nan

            mc_results[mechanism]["beta_mono"].append(beta_mono_est)
            mc_results[mechanism]["beta_acwr"].append(beta_acwr_est)
            mc_results[mechanism]["ci_lower"].append(ci_lower)
            mc_results[mechanism]["ci_upper"].append(ci_upper)

        except Exception:
            continue

# 결과 분석
print("\n--- H4 결과 요약 ---")
print(f"{'메커니즘':>10}  {'N':>4}  {'β_mono 평균':>12}  {'편향':>10}  {'편향률':>10}  {'Coverage':>10}")
print("-" * 70)

h4_biases = {}
h4_coverages = {}

for mechanism in MECHANISMS:
    betas = np.array(mc_results[mechanism]["beta_mono"])
    ci_lowers = np.array(mc_results[mechanism]["ci_lower"])
    ci_uppers = np.array(mc_results[mechanism]["ci_upper"])
    n_valid = len(betas)

    if n_valid == 0:
        continue

    mean_beta = np.nanmean(betas)
    bias = mean_beta - TRUE_MONO
    rel_bias = abs(bias) / abs(TRUE_MONO) if TRUE_MONO != 0 else np.nan

    # Coverage: 참값이 95% CI에 포함된 비율
    coverage = np.nanmean((ci_lowers <= TRUE_MONO) & (TRUE_MONO <= ci_uppers))

    h4_biases[mechanism] = rel_bias
    h4_coverages[mechanism] = coverage

    print(f"{mechanism:>10}  {n_valid:>4}  {mean_beta:>12.5f}  {bias:>10.5f}  {rel_bias:>10.2%}  {coverage:>10.2%}")

# --- H4 Pass/Fail 판정 ---
print("\n--- H4 판정 ---")
h4_results = {}

# MCAR 편향
mcar_bias = h4_biases.get("mcar", np.nan)
h4_results["MCAR_편향"] = {
    "값": f"{mcar_bias:.2%}",
    "기준": "|bias|/|true| < 10%",
    "판정": "PASS" if mcar_bias < 0.10 else "FAIL",
}

# 편향 순서: MNAR > MAR > MCAR
bias_mcar = h4_biases.get("mcar", 0)
bias_mar = h4_biases.get("mar", 0)
bias_mnar = h4_biases.get("mnar", 0)
bias_order_ok = bias_mnar > bias_mar > bias_mcar
h4_results["편향_순서"] = {
    "값": f"MNAR={bias_mnar:.2%} > MAR={bias_mar:.2%} > MCAR={bias_mcar:.2%}",
    "기준": "bias_MNAR > bias_MAR > bias_MCAR",
    "판정": "PASS" if bias_order_ok else "FAIL",
}

# Coverage 순서: MNAR < MAR < MCAR
cov_mcar = h4_coverages.get("mcar", 1)
cov_mar = h4_coverages.get("mar", 1)
cov_mnar = h4_coverages.get("mnar", 1)
cov_order_ok = cov_mnar < cov_mar < cov_mcar
h4_results["Coverage_순서"] = {
    "값": f"MNAR={cov_mnar:.2%} < MAR={cov_mar:.2%} < MCAR={cov_mcar:.2%}",
    "기준": "Coverage_MNAR < Coverage_MAR < Coverage_MCAR",
    "판정": "PASS" if cov_order_ok else "FAIL",
}

for name, res in h4_results.items():
    print(f"  [{res['판정']}] {name}: {res['값']} (기준: {res['기준']})")

h4_pass_count = sum(1 for r in h4_results.values() if r["판정"] == "PASS")
print(f"\n  H4 종합: {h4_pass_count}/{len(h4_results)} PASS")


# ===========================================================================
# 5. 통합 결과 요약 + 그림 저장
# ===========================================================================

print("\n" + "=" * 70)
print("[종합] 가설 검증 결과 요약")
print("=" * 70)

all_results = {
    "H1": {"결과": h1_results, "pass": h1_pass_count, "total": len(h1_results)},
    "H2": {"결과": h2_results, "pass": h2_pass_count, "total": len(h2_results)},
    "H3": {"결과": h3_results, "pass": h3_pass_count, "total": len(h3_results)},
    "H4": {"결과": h4_results, "pass": h4_pass_count, "total": len(h4_results)},
}

total_pass = 0
total_tests = 0
for hyp, info in all_results.items():
    status = "PASS" if info["pass"] == info["total"] else "PARTIAL"
    print(f"  {hyp}: {info['pass']}/{info['total']} ({status})")
    total_pass += info["pass"]
    total_tests += info["total"]

print(f"\n  전체: {total_pass}/{total_tests}")

# --- 그림 1: H1 OLS vs Mixed R² 비교 ---
fig1, axes1 = plt.subplots(1, 2, figsize=(10, 5))

# Hooper
labels_h = ["OLS", "Mixed"]
r2_h = [ols_r2_hooper, mixed_r2_hooper]
bars_h = axes1[0].bar(labels_h, r2_h, color=["#e74c3c", "#2ecc71"], edgecolor="white")
for bar, val in zip(bars_h, r2_h):
    axes1[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                  f"{val:.3f}", ha="center", fontsize=10)
axes1[0].set_title("Hooper: OLS vs Mixed R²")
axes1[0].set_ylabel("R²")
axes1[0].set_ylim(0, max(r2_h) * 1.3)

# HRV
r2_hrv_vals = [ols_r2_hrv, mixed_r2_hrv]
bars_hrv = axes1[1].bar(labels_h, r2_hrv_vals, color=["#e74c3c", "#2ecc71"], edgecolor="white")
for bar, val in zip(bars_hrv, r2_hrv_vals):
    axes1[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                  f"{val:.3f}", ha="center", fontsize=10)
axes1[1].set_title("HRV: OLS vs Mixed R²")
axes1[1].set_ylabel("R²")
axes1[1].set_ylim(0, max(r2_hrv_vals) * 1.3)

fig1.suptitle("[H1] 개인화된 기저선 추적의 중요성", fontsize=12, fontweight="bold")
fig1.tight_layout()
fig1.savefig(FIGURES_DIR / "h1_ols_vs_mixed_r2.png", dpi=150)
plt.close(fig1)

# --- 그림 2: H3 순차 투입 Monotony 계수 ---
fig2, ax2 = plt.subplots(figsize=(8, 5))
step_names = ["Step2\n(+Mono)", "Step3\n(+Strain)", "Step4\n(EWMA)"]
mono_coefs = [
    beta_mono_step2,
    beta_mono_step3,
    m_step4.fe_params.get("mono", np.nan),
]
bars2 = ax2.bar(step_names, mono_coefs, color=["#3498db", "#e67e22", "#9b59b6"], edgecolor="white")
ax2.axhline(y=TRUE_MONO, color="red", linestyle="--", linewidth=1.5, label=f"참값 = {TRUE_MONO}")
for bar, val in zip(bars2, mono_coefs):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002,
             f"{val:.4f}", ha="center", fontsize=10)
ax2.set_title("[H3] 순차 투입에 따른 Monotony 계수 변화")
ax2.set_ylabel("β_monotony")
ax2.legend()
fig2.tight_layout()
fig2.savefig(FIGURES_DIR / "h3_monotony_sequential.png", dpi=150)
plt.close(fig2)

# --- 그림 3: H4 Monte Carlo 편향/Coverage ---
fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(12, 5))

# 편향
mech_labels = ["Complete", "MCAR", "MAR", "MNAR"]
biases_plot = [h4_biases.get(m, 0) * 100 for m in MECHANISMS]
bars3a = ax3a.bar(mech_labels, biases_plot,
                   color=["#2ecc71", "#3498db", "#e67e22", "#e74c3c"], edgecolor="white")
for bar, val in zip(bars3a, biases_plot):
    ax3a.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
              f"{val:.1f}%", ha="center", fontsize=10)
ax3a.axhline(y=10, color="red", linestyle="--", linewidth=1, alpha=0.7, label="10% 기준선")
ax3a.set_title("β_mono 상대 편향")
ax3a.set_ylabel("상대 편향 (%)")
ax3a.legend()

# Coverage
coverages_plot = [h4_coverages.get(m, 0) * 100 for m in MECHANISMS]
bars3b = ax3b.bar(mech_labels, coverages_plot,
                   color=["#2ecc71", "#3498db", "#e67e22", "#e74c3c"], edgecolor="white")
for bar, val in zip(bars3b, coverages_plot):
    ax3b.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
              f"{val:.0f}%", ha="center", fontsize=10)
ax3b.axhline(y=95, color="green", linestyle="--", linewidth=1, alpha=0.7, label="95% 명목 수준")
ax3b.set_title("95% CI Coverage")
ax3b.set_ylabel("Coverage (%)")
ax3b.set_ylim(0, 105)
ax3b.legend()

fig3.suptitle("[H4] 결측 민감도 분석 (100회 Monte Carlo)", fontsize=12, fontweight="bold")
fig3.tight_layout()
fig3.savefig(FIGURES_DIR / "h4_missing_sensitivity.png", dpi=150)
plt.close(fig3)

print(f"\n그림 저장 완료: {FIGURES_DIR}")

# --- 결과 테이블 CSV 저장 ---
results_rows = []
for hyp, info in all_results.items():
    for test_name, test_res in info["결과"].items():
        results_rows.append({
            "가설": hyp,
            "검증항목": test_name,
            "측정값": test_res["값"],
            "기준": test_res["기준"],
            "판정": test_res["판정"],
        })

results_df = pd.DataFrame(results_rows)
results_csv_path = PROJECT_ROOT / "reports" / "integrated_hypothesis_results.csv"
results_df.to_csv(results_csv_path, index=False, encoding="utf-8-sig")
print(f"결과 CSV 저장: {results_csv_path}")

print("\n실험 완료.")
