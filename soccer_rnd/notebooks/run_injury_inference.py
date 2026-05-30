#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
부상예측 게이트 P3 — 주 추론·삼각검증 실행 스크립트 (Stage 8)

SoccerMon 데이터셋(Midoglu et al., 2024)의 부상 onset 라벨을 기준으로
ACWR–부상 위험 연관을 **세 가지 독립 설계**(이산시간 생존 cloglog,
case-crossover 조건부 로지스틱, 벌점 L2 로지스틱)로 추정하고 방향
일관성(triangulation)을 관찰한다. 추가로 gap 3 vs 7 라벨 민감도와
시간분리(2020→2021) 벌점 로지스틱 PR-AUC를 산출한다.

라벨/평가 로직은 검증된 P0 API를 재사용한다:
  - src.data.injury_label  : onset 라벨, 발생률, 패널 결합
  - src.stats.injury_eval  : 시간분리, PR-AUC, 기저 PR-AUC, gap 민감도
  - src.stats.survival_models : 세 설계 적합 및 삼각검증(P3 신규)

인과 단정 금지(reviewer-safe). 피로(wellness)는 매개변수이므로 ACWR
총효과 모형에 공변량으로 투입하지 않는다(과조정 편향 방지).

실행: venv/Scripts/python.exe notebooks/run_injury_inference.py
"""
import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT_PATH))

import os
import warnings

import numpy as np
import pandas as pd

from src.data.injury_label import build_injury_onset_label, compute_incidence, merge_onset_panel
from src.stats.injury_eval import baseline_pr_auc, pr_auc, time_split
from src.stats.survival_models import (
    fit_case_crossover,
    fit_discrete_time_survival,
    fit_penalized_glmm,
    triangulate,
)

warnings.filterwarnings("ignore")
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 경로·상수
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = str(PROJECT_ROOT_PATH)
INJURY_CSV = os.path.join(BASE_DIR, "data/raw/track_B/subjective/injury/injury.csv")
PANEL_CSV = os.path.join(BASE_DIR, "data/processed/track_B_merged.csv")

GAP_PRIMARY = 7          # 주 onset 판정 간격(ADR-014)
HORIZON = 7              # 선행 위험창(일)
ACWR_CAP_NOTE = "ACWR은 전처리에서 4.0 캡핑됨; 본 추론은 원척도 ACWR 사용"


def _fmt_effect(res: dict) -> str:
    """효과추정 결과 dict를 한 줄 문자열로 포맷."""
    if not res["converged"] or not np.isfinite(res["effect"]):
        return f"  [{res['design']}] 추정 불가 — {res['note']}"
    eff = res["effect_name"]
    p = res["pvalue"]
    p_str = f"{p:.4f}" if np.isfinite(p) else "NA(근사)"
    return (
        f"  [{res['design']}] {eff}={res['effect']:.3f} "
        f"(95% CI {res['ci_low']:.3f}~{res['ci_high']:.3f}), "
        f"p={p_str}, n={res['n_obs']:,}, 이벤트={res['n_events']}"
    )


# ═════════════════════════════════════════════════════════════════════════════
#  0. 데이터 적재
# ═════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("  부상예측 게이트 P3 — 주 추론·삼각검증")
print("  SoccerMon (Midoglu et al., 2024)")
print("=" * 80)

injury_raw = pd.read_csv(INJURY_CSV)
panel = pd.read_csv(PANEL_CSV)
panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()

print("\n[0단계] 데이터 적재")
print(f"  분석 패널: {len(panel):,} athlete-days, {panel['athlete_id'].nunique()}명")
print(f"  패널 기간: {panel['date'].min().date()} ~ {panel['date'].max().date()}")
print(f"  {ACWR_CAP_NOTE}")
print("  변수예산: EPV<=4 → 주 모형은 ACWR 단독 총효과(매개변수 wellness 미투입)")

onset = build_injury_onset_label(injury_raw, gap_days=GAP_PRIMARY)
incidence = compute_incidence(onset, panel)
print(f"\n  onset 사건(gap={GAP_PRIMARY}): {incidence['n_onset']}건, "
      f"{incidence['n_injured_players']}명, "
      f"발생률 {incidence['rate_per_1000']:.3f}/1000 athlete-days")

# ═════════════════════════════════════════════════════════════════════════════
#  1. 세 설계 적합 — ACWR 효과추정/CI
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [1단계] 세 설계 적합 — ACWR 효과추정 및 95% CI (원척도 ACWR)")
print("=" * 80)

res_dt = fit_discrete_time_survival(panel, onset, standardize=False)
res_cc = fit_case_crossover(panel, onset, standardize=False)
res_pl = fit_penalized_glmm(panel, onset, horizon=HORIZON, standardize=True, alpha=1.0)

print("\n  (1) 이산시간 생존 (cloglog, 선수 군집 robust SE) — HR")
print(_fmt_effect(res_dt))
print("\n  (2) case-crossover (조건부 로지스틱, 동일 선수 자기대조) — OR")
print(_fmt_effect(res_cc))
print("\n  (3) 벌점 로지스틱 (L2 ridge, onset_next_7, z-ACWR) — coef(log-odds)")
print(_fmt_effect(res_pl))
print(f"      비고: {res_pl['note']}")

# 효과추정 요약 표
eff_tbl = pd.DataFrame([
    {"설계": r["design"], "효과": r["effect_name"],
     "추정치": round(r["effect"], 3) if np.isfinite(r["effect"]) else np.nan,
     "CI하한": round(r["ci_low"], 3) if np.isfinite(r["ci_low"]) else np.nan,
     "CI상한": round(r["ci_high"], 3) if np.isfinite(r["ci_high"]) else np.nan,
     "p": round(r["pvalue"], 4) if np.isfinite(r["pvalue"]) else np.nan,
     "n": r["n_obs"], "이벤트": r["n_events"], "수렴": r["converged"]}
    for r in (res_dt, res_cc, res_pl)
])
print("\n  [효과추정 요약 표]")
print(eff_tbl.to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════════
#  2. 방향 일관성 판정 (삼각검증)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [2단계] 방향 일관성 판정 (triangulation)")
print("=" * 80)

tri = triangulate(panel, onset, horizon=HORIZON, standardize=False,
                  penalized_standardize=True, penalized_alpha=1.0)
print()
print(tri[["design", "effect_name", "effect", "ci_low", "ci_high",
           "pvalue", "direction_up"]].round(3).to_string(index=False))

summary = tri[tri["design"] == "consistency_summary"].iloc[0]
print(f"\n  방향 일관성: {summary['note']}")

# ═════════════════════════════════════════════════════════════════════════════
#  3. gap 3 vs 7 민감도 (라벨 재생성 후 재적합)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [3단계] gap 3 vs 7 민감도 — 라벨 재생성 후 세 설계 재적합")
print("=" * 80)

gap_rows = []
for gap in (3, 7):
    onset_g = build_injury_onset_label(injury_raw, gap_days=gap)
    inc_g = compute_incidence(onset_g, panel)
    dt_g = fit_discrete_time_survival(panel, onset_g, standardize=False)
    cc_g = fit_case_crossover(panel, onset_g, standardize=False)
    pl_g = fit_penalized_glmm(panel, onset_g, horizon=HORIZON, standardize=True)
    gap_rows.append({
        "gap": gap,
        "onset수": inc_g["n_onset"],
        "발생률/1000": round(inc_g["rate_per_1000"], 3),
        "HR(생존)": round(dt_g["effect"], 3) if np.isfinite(dt_g["effect"]) else np.nan,
        "OR(교차)": round(cc_g["effect"], 3) if np.isfinite(cc_g["effect"]) else np.nan,
        "coef(벌점)": round(pl_g["coef"], 3) if np.isfinite(pl_g["coef"]) else np.nan,
    })
gap_tbl = pd.DataFrame(gap_rows)
print()
print(gap_tbl.to_string(index=False))
print("\n  관찰: gap 3↔7 간 효과 방향이 유지되는지(부호 일관성)를 확인한다.")
print("  주의: 이산시간 생존 HR은 선수별 '최초' onset만 사용하므로 gap 변경(재발 사건 병합 기준)에")
print("        둔감할 수 있다 — 첫 사건 타이밍이 gap에 영향받지 않는 선수가 많기 때문으로 관찰된다.")

# ═════════════════════════════════════════════════════════════════════════════
#  4. 시간분리 검정(2020→2021) — 벌점 로지스틱 PR-AUC
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [4단계] 시간분리(2020 학습 → 2021 검정) — 벌점 로지스틱 PR-AUC")
print("=" * 80)

# 라벨 결합(주 gap=7, horizon=7) 후 연도 분리
print("\n  merge_onset_panel 실행 중(라벨 결합, 수십 초 소요 가능)...")
labeled = merge_onset_panel(panel, onset, horizons=(HORIZON,))
target = f"onset_next_{HORIZON}"

train_df, test_df = time_split(labeled, date_col="date", train_year=2020, test_year=2021)

# 학습셋에서 z-표준화 파라미터 산출 → 검정셋에 동일 적용(누수 차단)
feat = "acwr"
tr = train_df.dropna(subset=[feat, target]).copy()
te = test_df.dropna(subset=[feat, target]).copy()

import statsmodels.api as sm  # noqa: E402

mu, sd = tr[feat].mean(), tr[feat].std(ddof=0)
sd = sd if sd and not np.isnan(sd) else 1.0
Xtr = sm.add_constant(pd.DataFrame({feat: (tr[feat] - mu) / sd}), has_constant="add")
Xte = sm.add_constant(pd.DataFrame({feat: (te[feat] - mu) / sd}), has_constant="add")
ytr = tr[target].to_numpy().astype(int)
yte = te[target].to_numpy().astype(int)

print(f"  학습(2020): n={len(tr):,}, 양성={int(ytr.sum())} "
      f"({ytr.mean()*100:.3f}%)")
print(f"  검정(2021): n={len(te):,}, 양성={int(yte.sum())} "
      f"({yte.mean()*100:.3f}%)")

pr_test = float("nan")
try:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = sm.Logit(ytr, Xtr).fit_regularized(alpha=1.0, L1_wt=0.0, disp=0, maxiter=200)
    yscore = np.asarray(fit.predict(Xte))
    pr_test = pr_auc(yte, yscore)
    base_test = baseline_pr_auc(yte)
    print(f"\n  검정셋 PR-AUC(벌점 로지스틱, ACWR 단독): {pr_test:.4f}")
    print(f"  검정셋 기저 PR-AUC(양성률 하한):         {base_test:.4f}")
    if np.isfinite(pr_test) and np.isfinite(base_test):
        lift = pr_test / base_test if base_test > 0 else float("nan")
        print(f"  기저 대비 배율(lift): {lift:.2f}×")
        print("  관찰: ACWR 단독 모형의 시간외삽 변별력이 기저선 대비 "
              f"{'상회' if pr_test > base_test else '동등/하회'}하는 것으로 관찰된다.")
except Exception as exc:  # noqa: BLE001
    print(f"\n  시간분리 PR-AUC 산출 실패(관용 처리): {exc}")

# ═════════════════════════════════════════════════════════════════════════════
#  5. 요약
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [요약] 게이트 P3 주 추론·삼각검증")
print("=" * 80)
print(f"""
  - onset {incidence['n_onset']}건 / {incidence['rate_per_1000']:.3f}/1000 (gap={GAP_PRIMARY})
  - 이산시간 생존 HR  = {res_dt['effect']:.3f} (95% CI {res_dt['ci_low']:.3f}~{res_dt['ci_high']:.3f}), p={res_dt['pvalue']:.4f}
  - case-crossover OR = {res_cc['effect']:.3f} (95% CI {res_cc['ci_low']:.3f}~{res_cc['ci_high']:.3f}), p={res_cc['pvalue']:.4f}
  - 벌점 로지스틱 coef= {res_pl['coef']:.3f} (z-ACWR, L2)
  - 방향 일관성: {summary['effect_name']}
  - 시간분리(2021) 벌점 로지스틱 PR-AUC = {pr_test:.4f}
  - reviewer-safe: ACWR 상승이 부상 위험 증가와 연관된다는 신호가 설계 전반에서
    {'일관되게' if bool(summary['direction_up']) else '부분적으로'} 관찰되나, 인과로 단정하지 않는다.
""")
print("  게이트 P3 주 추론 완료.")
