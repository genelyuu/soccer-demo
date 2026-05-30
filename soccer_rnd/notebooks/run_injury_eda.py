#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
부상예측 게이트 P1 — 기술역학 EDA 스크립트 (Stage 8)

SoccerMon 데이터셋(Midoglu et al., 2024)의 부상 onset 라벨을 기준으로
기술역학(descriptive epidemiology)을 산출한다. 모형 학습 전 단계로서
발생률·선행 위험창 양성률·불균형비·부위/중증도 분포·결측 패턴·노출-결과
시간정렬·생존곡선(KM)을 관찰한다.

라벨/평가 로직은 게이트 P0에서 검증된 API를 재사용한다:
  - src.data.injury_label  : onset 라벨, 발생률, 패널 결합
  - src.stats.injury_eval  : gap 민감도

reviewer-safe 톤('관찰된다/시사한다')으로 기술하며, 인과는 단정하지 않는다.

실행: venv/Scripts/python.exe notebooks/run_injury_eda.py
"""
import sys
from pathlib import Path

PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT_PATH))

import os
import warnings

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter

from src.data.injury_label import (
    build_injury_onset_label,
    compute_incidence,
    merge_onset_panel,
    parse_injury_records,
)
from src.stats.injury_eval import gap_sensitivity

warnings.filterwarnings("ignore")
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = str(PROJECT_ROOT_PATH)
INJURY_CSV = os.path.join(BASE_DIR, "data/raw/track_B/subjective/injury/injury.csv")
PANEL_CSV = os.path.join(BASE_DIR, "data/processed/track_B_merged.csv")
FIG_DIR = os.path.join(BASE_DIR, "reports/figures")
os.makedirs(FIG_DIR, exist_ok=True)

# 그림 파일명 접두어(다른 작업자와 충돌 방지)
FIG_PREFIX = "injury_eda_"

# 분석 상수
GAP_DAYS = 7              # onset 독립 사건 판정 간격(ADR-014)
HORIZONS = (1, 3, 7)      # 선행 위험창 길이(일)

# 시각화 설정
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})
sns.set_style("whitegrid")
from src.viz.fonts import apply_korean_font  # noqa: E402

_font = apply_korean_font()
print(f"[폰트] 적용된 한글 폰트: {_font}")


def fig_path(name: str) -> str:
    return os.path.join(FIG_DIR, f"{FIG_PREFIX}{name}.png")


# ═════════════════════════════════════════════════════════════════════════════
#  0. 데이터 적재
# ═════════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("  부상예측 게이트 P1 — 기술역학 EDA")
print("  SoccerMon (Midoglu et al., 2024)")
print("=" * 80)

print("\n[0단계] 데이터 적재")
injury_raw = pd.read_csv(INJURY_CSV)
panel = pd.read_csv(PANEL_CSV)
panel["date"] = pd.to_datetime(panel["date"]).dt.normalize()
print(f"  원시 부상 기록: {len(injury_raw):,} 행 (부상-일 단위)")
print(f"  분석 패널: {len(panel):,} athlete-days, {panel['athlete_id'].nunique()}명")
print(f"  패널 기간: {panel['date'].min().date()} ~ {panel['date'].max().date()}")
print(f"  팀 구성: {panel['team'].value_counts().to_dict()}")

# 활성일 정의 명시
n_zero_load = int((panel["daily_load"] == 0).sum())
print(
    f"  [활성일 정의] daily_load==0 인 {n_zero_load:,} athlete-days는 "
    "비훈련일(휴식)로 간주하나, 노출 분모(athlete-days)에는 포함한다."
)
print(
    "               발생률 분모는 패널 전체 athlete-days를 노출로 사용하며, "
    "0-부하일을 제외하지 않는다(보수적 노출 정의)."
)

# ═════════════════════════════════════════════════════════════════════════════
#  1. onset 라벨 · 발생률 · gap 민감도
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [1단계] onset 라벨 · 발생률 · gap 민감도")
print("=" * 80)

injury_dedup = parse_injury_records(injury_raw)
n_dedup = len(injury_dedup)
print(f"\n  dedup 후 부상-일: {n_dedup:,} (동일 선수·날짜 중복 제거)")

onset = build_injury_onset_label(injury_raw, gap_days=GAP_DAYS)
incidence = compute_incidence(onset, panel)
print(f"\n  onset 사건 수 (gap={GAP_DAYS}): {incidence['n_onset']}")
print(f"  부상 선수 수: {incidence['n_injured_players']}명")
print(f"  노출 athlete-days: {incidence['athlete_days']:,}")
print(f"  발생률: {incidence['rate_per_1000']:.3f} / 1000 athlete-days")

print("\n  [gap 민감도]")
gap_tbl = gap_sensitivity(injury_raw, panel, gaps=(3, 7))
print(gap_tbl.to_string(index=False))

# ═════════════════════════════════════════════════════════════════════════════
#  2. 선행 위험창 양성률 · 불균형비
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [2단계] 선행 위험창 양성률 · 불균형비 (음성:양성)")
print("=" * 80)
print("\n  merge_onset_panel 실행 중(24,596행 iterrows, 수십 초 소요 가능)...")

labeled = merge_onset_panel(panel, onset, horizons=HORIZONS)
n_rows = len(labeled)

window_rows = []
for k in HORIZONS:
    col = f"onset_next_{k}"
    n_pos = int(labeled[col].sum())
    n_neg = n_rows - n_pos
    pos_rate = n_pos / n_rows * 100.0
    imbalance = (n_neg / n_pos) if n_pos else float("nan")
    window_rows.append({
        "horizon_k": k,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "pos_rate_pct": pos_rate,
        "imbalance_neg_per_pos": imbalance,
    })
    print(
        f"  k={k}일: 양성 {n_pos} / {n_rows:,}  "
        f"양성률 {pos_rate:.3f}%  불균형비 1:{imbalance:.0f}"
    )

window_df = pd.DataFrame(window_rows)

# 당일 onset_event 참고 출력
n_event = int(labeled["onset_event"].sum())
print(f"\n  (참고) 당일 onset_event 표시 athlete-days: {n_event} "
      f"— 패널 날짜와 정확히 일치하는 onset만 카운트됨")

# ═════════════════════════════════════════════════════════════════════════════
#  3. 부위 · 중증도 분포
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [3단계] 부위(body_part) · 중증도(severity) 분포")
print("=" * 80)

body_counts = onset["body_part"].value_counts()
sev_counts = onset["severity"].value_counts()

print("\n  [부위 분포] (대표 부위 = type JSON 첫 항목 기준)")
for bp, c in body_counts.items():
    print(f"    {bp:14s}: {c}")

print("\n  [중증도 분포] (복수 부위 시 major 우선 격상)")
for sv, c in sev_counts.items():
    print(f"    {sv:8s}: {c}")

# ═════════════════════════════════════════════════════════════════════════════
#  4. 결측 패턴 (wellness)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [4단계] wellness 결측 패턴")
print("=" * 80)

wellness_cols = ["fatigue", "stress", "soreness", "sleep_quality", "hooper_index"]
miss_rows = []
for c in wellness_cols:
    miss_pct = panel[c].isna().mean() * 100.0
    miss_rows.append({"variable": c, "missing_pct": miss_pct})
    print(f"    {c:14s}: 결측률 {miss_pct:.2f}%")
miss_df = pd.DataFrame(miss_rows)

# ═════════════════════════════════════════════════════════════════════════════
#  5. 노출-결과 시간정렬 (event-aligned, [-7, +7]일)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [5단계] 노출-결과 시간정렬: onset 기준 [-7, +7]일 부하·ACWR 평균 추이")
print("=" * 80)

panel_idx = panel.set_index(["athlete_id", "date"]).sort_index()
offsets = list(range(-7, 8))
aligned = {off: {"daily_load": [], "acwr": []} for off in offsets}

for _, ev in onset.iterrows():
    aid = ev["player_name"]
    d0 = pd.Timestamp(ev["onset_date"]).normalize()
    for off in offsets:
        key = (aid, d0 + pd.Timedelta(days=off))
        if key in panel_idx.index:
            row = panel_idx.loc[key]
            # 동일 키 중복 방어
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            dl = row["daily_load"]
            ac = row["acwr"]
            if pd.notna(dl):
                aligned[off]["daily_load"].append(dl)
            if pd.notna(ac):
                aligned[off]["acwr"].append(ac)

align_rows = []
for off in offsets:
    dl_arr = np.array(aligned[off]["daily_load"], dtype=float)
    ac_arr = np.array(aligned[off]["acwr"], dtype=float)
    align_rows.append({
        "offset_day": off,
        "n_load": len(dl_arr),
        "mean_daily_load": dl_arr.mean() if len(dl_arr) else np.nan,
        "n_acwr": len(ac_arr),
        "mean_acwr": ac_arr.mean() if len(ac_arr) else np.nan,
    })
align_df = pd.DataFrame(align_rows)
print()
print(align_df.round(3).to_string(index=False))

# 부상 전(-7~-1) vs 부상 후(+1~+7) 평균 비교 관찰
pre = align_df[align_df["offset_day"].between(-7, -1)]
post = align_df[align_df["offset_day"].between(1, 7)]
day0 = align_df[align_df["offset_day"] == 0].iloc[0]
print(
    f"\n  관찰: 부상 전(-7~-1) 평균 부하={pre['mean_daily_load'].mean():.1f}, "
    f"부상일(0) 부하={day0['mean_daily_load']:.1f}, "
    f"부상 후(+1~+7) 평균 부하={post['mean_daily_load'].mean():.1f}"
)
print(
    f"  관찰: 부상 전(-7~-1) 평균 ACWR={pre['mean_acwr'].mean():.3f}, "
    f"부상일(0) ACWR={day0['mean_acwr']:.3f}, "
    f"부상 후(+1~+7) 평균 ACWR={post['mean_acwr'].mean():.3f}"
)

# ═════════════════════════════════════════════════════════════════════════════
#  6. KM 생존곡선 (부상까지 생존)
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [6단계] Kaplan-Meier 생존곡선: '부상까지 생존' (선수별 최초 onset)")
print("=" * 80)

# 선수별 관찰 시작/종료일 (패널 기준)
obs = panel.groupby("athlete_id")["date"].agg(["min", "max"]).reset_index()
obs.columns = ["athlete_id", "start", "end"]

# 선수별 최초 onset
first_onset = (
    onset.groupby("player_name")["onset_date"].min().reset_index()
    .rename(columns={"player_name": "athlete_id", "onset_date": "first_onset"})
)
obs = obs.merge(first_onset, on="athlete_id", how="left")
obs["first_onset"] = pd.to_datetime(obs["first_onset"])

# 생존시간(일) = 최초 onset까지, 미발생자는 관찰종료까지 censoring
def _duration_event(r):
    if pd.notna(r["first_onset"]) and r["first_onset"] >= r["start"]:
        dur = (r["first_onset"] - r["start"]).days
        return pd.Series({"duration": max(dur, 0), "event": 1})
    dur = (r["end"] - r["start"]).days
    return pd.Series({"duration": max(dur, 0), "event": 0})

surv = obs.join(obs.apply(_duration_event, axis=1))
surv["team"] = surv["athlete_id"].str.extract(r"^(Team[AB])")

n_event_surv = int(surv["event"].sum())
n_censored = int((surv["event"] == 0).sum())
print(f"\n  분석 선수: {len(surv)}명 (이벤트 {n_event_surv}, 검열 {n_censored})")
print(f"  관찰 생존시간 중앙값(일): {surv['duration'].median():.0f}")

kmf = KaplanMeierFitter()
kmf.fit(surv["duration"], event_observed=surv["event"], label="전체")
# median survival time (이벤트가 50% 미만이면 inf 가능)
try:
    med = kmf.median_survival_time_
    print(f"  KM 중위 생존시간(일): {med}")
except Exception:
    print("  KM 중위 생존시간: 추정 불가(이벤트 < 50%)")

# 마지막 관찰시점 생존확률
last_t = surv["duration"].max()
surv_at_end = float(kmf.predict(last_t))
print(f"  관찰 종료시점(t={last_t}일) 추정 생존확률: {surv_at_end:.3f}")
print(f"  (해석: 관찰 기간 동안 부상 미경험 확률 추정치 ≈ {surv_at_end:.1%})")

# 팀별 KM
team_km = {}
for tm, grp in surv.groupby("team"):
    if len(grp) == 0:
        continue
    k = KaplanMeierFitter()
    k.fit(grp["duration"], event_observed=grp["event"], label=tm)
    team_km[tm] = (k, grp)
    ev = int(grp["event"].sum())
    print(f"  [{tm}] n={len(grp)}, 이벤트={ev}, "
          f"종료시점 생존확률={float(k.predict(grp['duration'].max())):.3f}")

# ═════════════════════════════════════════════════════════════════════════════
#  7. STROBE 흐름 요약
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [STROBE 흐름 요약]")
print("=" * 80)
print(f"""
  원시 부상-일 기록           : {len(injury_raw):,} 행
        │  동일 (선수,날짜) 중복 제거(dedup)
        ▼
  dedup 부상-일               : {n_dedup:,} 행
        │  gap>={GAP_DAYS}일 규칙으로 독립 onset 사건 도출
        ▼
  onset 사건                  : {incidence['n_onset']} 건  ({incidence['n_injured_players']}명)
        │  패널(athlete-day) 결합 + 선행 위험창 라벨 부여
        ▼
  분석 패널(라벨 결합)        : {n_rows:,} athlete-days
        - 발생률 {incidence['rate_per_1000']:.3f}/1000 athlete-days
        - 선행 위험창 양성률 k=1/3/7: """
      + ", ".join(f"{r['pos_rate_pct']:.2f}%" for r in window_rows))

# ═════════════════════════════════════════════════════════════════════════════
#  8. 그림 저장
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  [그림 생성]")
print("=" * 80)

# (a) 발생률/양성률·불균형 막대 ------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
ax = axes[0]
ks = [f"k={r['horizon_k']}" for r in window_rows]
rates = [r["pos_rate_pct"] for r in window_rows]
bars = ax.bar(ks, rates, color=["#3498DB", "#2ECC71", "#E67E22"],
              edgecolor="gray", alpha=0.85)
for b, r in zip(bars, window_rows):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
            f"{r['pos_rate_pct']:.2f}%\n(n={r['n_pos']})",
            ha="center", va="bottom", fontsize=8)
ax.axhline(incidence["rate_per_1000"] / 10.0, color="red", linestyle="--",
           linewidth=1, label=f"당일 발생률 {incidence['rate_per_1000']:.2f}/1000")
ax.set_ylabel("선행 위험창 양성률 (%)")
ax.set_title("선행 위험창 양성률 (k=1/3/7)")
ax.legend(fontsize=8)

ax = axes[1]
imbs = [r["imbalance_neg_per_pos"] for r in window_rows]
bars = ax.bar(ks, imbs, color=["#3498DB", "#2ECC71", "#E67E22"],
              edgecolor="gray", alpha=0.85)
for b, v in zip(bars, imbs):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
            f"1:{v:.0f}", ha="center", va="bottom", fontsize=9)
ax.set_ylabel("불균형비 (음성:양성, 1:N)")
ax.set_title("클래스 불균형비")
fig.suptitle("부상 선행 위험창 — 양성률 및 불균형", fontsize=13)
fig.tight_layout()
fig.savefig(fig_path("incidence_window"))
plt.close(fig)
print(f"  저장: {FIG_PREFIX}incidence_window.png")

# (b) 부위 · 중증도 분포 -------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
bp_sorted = body_counts.sort_values()
ax.barh(bp_sorted.index, bp_sorted.values, color="#5B9BD5",
        edgecolor="gray", alpha=0.85)
for i, v in enumerate(bp_sorted.values):
    ax.text(v, i, f" {v}", va="center", fontsize=8)
ax.set_xlabel("onset 건수")
ax.set_title("부위(body_part)별 onset 분포")

ax = axes[1]
sev_order = [s for s in ["minor", "major", "unknown"] if s in sev_counts.index]
sev_vals = [sev_counts[s] for s in sev_order]
colors_sev = {"minor": "#2ECC71", "major": "#E74C3C", "unknown": "#95A5A6"}
bars = ax.bar(sev_order, sev_vals,
              color=[colors_sev[s] for s in sev_order],
              edgecolor="gray", alpha=0.85)
for b, v in zip(bars, sev_vals):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
            str(v), ha="center", va="bottom", fontsize=10)
ax.set_ylabel("onset 건수")
ax.set_title("중증도(severity) 분포")
fig.suptitle("부상 onset — 부위 및 중증도 분포", fontsize=13)
fig.tight_layout()
fig.savefig(fig_path("bodypart_severity"))
plt.close(fig)
print(f"  저장: {FIG_PREFIX}bodypart_severity.png")

# (c) event-aligned 부하/ACWR 추이 --------------------------------------------
fig, ax1 = plt.subplots(figsize=(10, 5.5))
ax2 = ax1.twinx()
l1 = ax1.plot(align_df["offset_day"], align_df["mean_daily_load"],
              marker="o", color="#5B9BD5", linewidth=1.8, label="평균 Daily Load")
l2 = ax2.plot(align_df["offset_day"], align_df["mean_acwr"],
              marker="s", color="#E74C3C", linewidth=1.8, label="평균 ACWR")
ax1.axvline(0, color="black", linestyle="--", linewidth=1)
ax1.text(0, ax1.get_ylim()[1], " onset일", color="black", fontsize=8, va="top")
ax1.set_xlabel("onset 기준 상대일 (일)")
ax1.set_ylabel("평균 Daily Load (sRPE)", color="#5B9BD5")
ax2.set_ylabel("평균 ACWR", color="#E74C3C")
ax1.set_title("노출-결과 시간정렬: onset [-7, +7]일 부하·ACWR 평균 추이")
ax1.set_xticks(offsets)
lines = l1 + l2
ax1.legend(lines, [ln.get_label() for ln in lines], loc="upper left", fontsize=9)
fig.tight_layout()
fig.savefig(fig_path("event_aligned"))
plt.close(fig)
print(f"  저장: {FIG_PREFIX}event_aligned.png")

# (d) 결측 히트맵 --------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 4.5))
panel_tmp = panel.copy()
panel_tmp["year_month"] = panel_tmp["date"].dt.to_period("M").astype(str)
miss_pivot = (
    panel_tmp.groupby("year_month")[wellness_cols]
    .apply(lambda g: g.isna().mean())
)
sns.heatmap(miss_pivot.T, cmap="YlOrRd", vmin=0, vmax=1,
            cbar_kws={"label": "결측 비율"}, ax=ax, linewidths=0.3)
ax.set_title("wellness 결측 비율 (월별 × 변수)")
ax.set_xlabel("연월")
ax.set_ylabel("변수")
plt.xticks(rotation=45, ha="right", fontsize=7)
fig.tight_layout()
fig.savefig(fig_path("missing_heatmap"))
plt.close(fig)
print(f"  저장: {FIG_PREFIX}missing_heatmap.png")

# (e) KM 생존곡선 --------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
ax = axes[0]
kmf.plot_survival_function(ax=ax, ci_show=True, color="#34495E")
ax.set_xlabel("관찰 시작 후 경과일")
ax.set_ylabel("부상 미경험 생존확률")
ax.set_title("KM 생존곡선 — 전체(최초 onset까지)")
ax.set_ylim(0, 1.02)
ax.legend(fontsize=9)

ax = axes[1]
team_colors = {"TeamA": "#1f77b4", "TeamB": "#ff7f0e"}
for tm, (k, _grp) in team_km.items():
    k.plot_survival_function(ax=ax, ci_show=False,
                             color=team_colors.get(tm, "gray"))
ax.set_xlabel("관찰 시작 후 경과일")
ax.set_ylabel("부상 미경험 생존확률")
ax.set_title("KM 생존곡선 — 팀별 비교 (TeamA vs TeamB)")
ax.set_ylim(0, 1.02)
ax.legend(fontsize=9)
fig.suptitle("부상까지 생존 — Kaplan-Meier", fontsize=13)
fig.tight_layout()
fig.savefig(fig_path("km_survival"))
plt.close(fig)
print(f"  저장: {FIG_PREFIX}km_survival.png")

# ─────────────────────────────────────────────────────────────────────────────
#  생성 그림 목록
# ─────────────────────────────────────────────────────────────────────────────
print("\n  생성된 그림 파일:")
for fname in sorted(os.listdir(FIG_DIR)):
    if fname.startswith(FIG_PREFIX):
        fp = os.path.join(FIG_DIR, fname)
        print(f"    {fp} ({os.path.getsize(fp) / 1024:.1f} KB)")

print("\n  게이트 P1 기술역학 EDA 완료.")
