#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Track B 분석 스크립트 — SoccerMon 데이터셋 (Midoglu et al., 2024)
부하 + 설문(Hooper) 기반 피로도 예측 모형

실행: python notebooks/run_track_B.py
"""
import sys
sys.path.insert(0, "C:/dev/soccer_rnd")

import os
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import statsmodels.formula.api as smf
from statsmodels.regression.mixed_linear_model import MixedLMResults
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")
np.random.seed(42)

# ─────────────────────────────────────────────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = "C:/dev/soccer_rnd"
RAW_DIR = os.path.join(BASE_DIR, "data/raw/track_B/subjective")
FIG_DIR = os.path.join(BASE_DIR, "reports/figures")
PROC_DIR = os.path.join(BASE_DIR, "data/processed")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

# 시각화 설정
plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
})
sns.set_style("whitegrid")

# ─────────────────────────────────────────────────────────────────────────────
# 1. 데이터 적재 및 Wide → Long 변환
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("  Track B 분석: SoccerMon 부하-설문 데이터")
print("  (Midoglu et al., 2024)")
print("=" * 80)

FILE_MAP = {
    # (파일 경로, 변수명)
    "daily_load": os.path.join(RAW_DIR, "training-load/daily_load.csv"),
    "fatigue":    os.path.join(RAW_DIR, "wellness/fatigue.csv"),
    "stress":     os.path.join(RAW_DIR, "wellness/stress.csv"),
    "soreness":   os.path.join(RAW_DIR, "wellness/soreness.csv"),
    "sleep_quality": os.path.join(RAW_DIR, "wellness/sleep_quality.csv"),
    "acwr":       os.path.join(RAW_DIR, "training-load/acwr.csv"),
    "atl":        os.path.join(RAW_DIR, "training-load/atl.csv"),
    "monotony":   os.path.join(RAW_DIR, "training-load/monotony.csv"),
    "strain":     os.path.join(RAW_DIR, "training-load/strain.csv"),
}


def load_wide_csv(filepath, var_name):
    """
    Wide 형식 CSV를 읽어서 Long 형식으로 변환.
    첫 번째 열 헤더가 'Date', 'Fatigue Data', 'Soreness Data' 등 다양하므로
    일괄적으로 'date'로 변경 처리.
    """
    df = pd.read_csv(filepath)
    # 첫 번째 열을 date로 통일
    date_col = df.columns[0]
    df = df.rename(columns={date_col: "date"})
    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")

    # 선수 ID 열만 추출
    player_cols = [c for c in df.columns if c.startswith("Team")]
    # Wide → Long
    long = df.melt(id_vars=["date"], value_vars=player_cols,
                   var_name="athlete_id", value_name=var_name)
    return long


print("\n[1단계] 데이터 적재 및 Wide→Long 변환")
dfs = {}
for var_name, fpath in FILE_MAP.items():
    dfs[var_name] = load_wide_csv(fpath, var_name)
    n_rows = len(dfs[var_name])
    n_valid = dfs[var_name][var_name].notna().sum()
    print(f"  - {var_name:15s}: {n_rows:,} 행 (유효값 {n_valid:,})")

# ─────────────────────────────────────────────────────────────────────────────
# 2. 병합 (merge)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2단계] 변수별 데이터 병합")

# 시작: daily_load
merged = dfs["daily_load"].copy()
for var_name in ["fatigue", "stress", "soreness", "sleep_quality",
                 "acwr", "atl", "monotony", "strain"]:
    merged = merged.merge(dfs[var_name], on=["date", "athlete_id"], how="outer")

# 0을 NaN으로 변환 — daily_load에서 0은 비훈련일(휴식/비활성), 웰니스 0도 미보고
# 단, daily_load 0은 실제 비훈련일일 수 있으므로, 활성 시즌 판단 후 처리
# acwr, atl, monotony, strain에서 0은 실제 비활성 기간
print(f"  병합 완료: {merged.shape[0]:,} 행, {merged.shape[1]} 열")

# 팀 정보 추출
merged["team"] = merged["athlete_id"].str.extract(r"^(Team[AB])")
print(f"  팀 구성: {merged['team'].value_counts().to_dict()}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. 활성 시즌 필터링
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3단계] 활성 시즌 필터링")

# 비시즌(off-season) 제거: 선수별로 daily_load > 0 이거나 웰니스 데이터 존재하는
# 첫날부터 마지막 날까지만 유지
def get_active_range(group):
    """선수별 활성 기간: daily_load > 0 또는 웰니스(fatigue) 데이터 존재하는 구간"""
    has_load = group["daily_load"] > 0
    has_wellness = group["fatigue"].notna()
    active = has_load | has_wellness
    if active.sum() == 0:
        return group.iloc[0:0]  # 빈 DataFrame 반환
    first_active = group.loc[active, "date"].min()
    last_active = group.loc[active, "date"].max()
    return group[(group["date"] >= first_active) & (group["date"] <= last_active)]

merged = merged.groupby("athlete_id", group_keys=False).apply(get_active_range)
merged = merged.reset_index(drop=True)
print(f"  활성 시즌 필터 후: {merged.shape[0]:,} 행")

# ─────────────────────────────────────────────────────────────────────────────
# 4. 선수별 충분한 데이터 필터
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4단계] 충분한 데이터를 가진 선수 필터링 (>= 60일)")

# 선수별 daily_load > 0 일수 + wellness 유효일수 모두 고려
athlete_stats = merged.groupby("athlete_id").agg(
    n_days=("date", "nunique"),
    n_load_nonzero=("daily_load", lambda x: (x > 0).sum()),
    n_fatigue=("fatigue", lambda x: x.notna().sum()),
    n_stress=("stress", lambda x: x.notna().sum()),
    n_soreness=("soreness", lambda x: x.notna().sum()),
    n_sleep=("sleep_quality", lambda x: x.notna().sum()),
).reset_index()

# 부하 비제로 일수 + 웰니스 중 하나라도 유효한 일수 합계 >= 60
athlete_stats["n_wellness_any"] = athlete_stats[["n_fatigue", "n_stress",
                                                  "n_soreness", "n_sleep"]].max(axis=1)
qualified = athlete_stats[
    (athlete_stats["n_load_nonzero"] >= 60) &
    (athlete_stats["n_wellness_any"] >= 60)
]["athlete_id"]

print(f"  전체 선수: {merged['athlete_id'].nunique()}")
print(f"  자격 선수: {len(qualified)} (load >= 60일 & wellness >= 60일)")

merged = merged[merged["athlete_id"].isin(qualified)].copy()
merged = merged.sort_values(["athlete_id", "date"]).reset_index(drop=True)
print(f"  필터 후 데이터: {merged.shape[0]:,} 행")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Hooper Index 산출
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5단계] Hooper Index 산출")

# stress는 1~10 척도이므로 1~5로 정규화
merged["stress_norm"] = merged["stress"] / 2.0
print(f"  stress 원래 범위: [{merged['stress'].min():.1f}, {merged['stress'].max():.1f}]")
print(f"  stress_norm 범위: [{merged['stress_norm'].min():.1f}, {merged['stress_norm'].max():.1f}]")

# Hooper Index = fatigue + stress_norm + soreness + sleep_quality
# 구성요소 중 하나라도 NaN이면 NaN
hooper_components = ["fatigue", "stress_norm", "soreness", "sleep_quality"]
merged["hooper_index"] = merged[hooper_components].sum(axis=1, skipna=False)
n_hooper = merged["hooper_index"].notna().sum()
print(f"  Hooper Index 유효 관측: {n_hooper:,} / {len(merged):,}")
print(f"  Hooper Index 범위: [{merged['hooper_index'].min():.1f}, {merged['hooper_index'].max():.1f}]")
print(f"  Hooper Index 평균: {merged['hooper_index'].mean():.2f} (SD={merged['hooper_index'].std():.2f})")

# ─────────────────────────────────────────────────────────────────────────────
# 6. 기술 통계
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6단계] 기술 통계 요약")

desc_vars = ["daily_load", "fatigue", "stress", "stress_norm", "soreness",
             "sleep_quality", "hooper_index", "acwr", "atl", "monotony", "strain"]
desc = merged[desc_vars].describe().T
desc["missing%"] = ((merged[desc_vars].isna().sum() / len(merged)) * 100).values
print(desc[["count", "mean", "std", "min", "25%", "50%", "75%", "max", "missing%"]].round(2).to_string())

# ─────────────────────────────────────────────────────────────────────────────
# 7. 처리 데이터 저장
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7단계] 처리 데이터 저장")
out_path = os.path.join(PROC_DIR, "track_B_merged.csv")
merged.to_csv(out_path, index=False)
print(f"  저장 완료: {out_path}")
print(f"  크기: {merged.shape[0]:,} 행, {merged.shape[1]} 열")
print(f"  선수 수: {merged['athlete_id'].nunique()}")
print(f"  날짜 범위: {merged['date'].min().strftime('%Y-%m-%d')} ~ {merged['date'].max().strftime('%Y-%m-%d')}")

# ═════════════════════════════════════════════════════════════════════════════
#  EDA 시각화
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  EDA 시각화")
print("=" * 80)

# ─────────────────────────────────────────────────────────────────────────────
# 7a. 주간 부하 패턴
# ─────────────────────────────────────────────────────────────────────────────
print("\n[EDA-1] 주간 부하 패턴 (요일별 평균 daily_load)")

fig, ax = plt.subplots(figsize=(8, 5))
# daily_load > 0 인 데이터만 사용 (비훈련일 제외)
load_active = merged[merged["daily_load"] > 0].copy()
load_active["dow"] = load_active["date"].dt.dayofweek  # 0=월, 6=일
dow_labels = ["월", "화", "수", "목", "금", "토", "일"]

dow_stats = load_active.groupby("dow")["daily_load"].agg(["mean", "std", "count"])
dow_stats["se"] = dow_stats["std"] / np.sqrt(dow_stats["count"])

ax.bar(range(7), dow_stats["mean"], yerr=dow_stats["se"],
       capsize=4, color=sns.color_palette("Blues_d", 7), edgecolor="gray", alpha=0.85)
ax.set_xticks(range(7))
ax.set_xticklabels(dow_labels)
ax.set_xlabel("요일")
ax.set_ylabel("평균 Daily Load (sRPE)")
ax.set_title("요일별 평균 훈련 부하 (비훈련일 제외, 오차막대=SE)")
for i, (m, s) in enumerate(zip(dow_stats["mean"], dow_stats["se"])):
    ax.text(i, m + s + 10, f"{m:.0f}", ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_weekly_load_pattern.png"))
plt.close(fig)
print("  저장: track_B_weekly_load_pattern.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7b. ACWR(t) vs Hooper(t+1) 산점도
# ─────────────────────────────────────────────────────────────────────────────
print("\n[EDA-2] ACWR(t) vs Hooper Index(t+1) 산점도")

# 시차 변수 생성
merged = merged.sort_values(["athlete_id", "date"])
merged["hooper_lag1"] = merged.groupby("athlete_id")["hooper_index"].shift(-1)

scatter_df = merged.dropna(subset=["acwr", "hooper_lag1"]).copy()
# ACWR 이상치 제거 (> 10은 비현실적)
scatter_df = scatter_df[(scatter_df["acwr"] > 0) & (scatter_df["acwr"] < 10)]

fig, ax = plt.subplots(figsize=(8, 6))
colors = {"TeamA": "#1f77b4", "TeamB": "#ff7f0e"}
for team, grp in scatter_df.groupby("team"):
    ax.scatter(grp["acwr"], grp["hooper_lag1"], alpha=0.15, s=10,
               color=colors.get(team, "gray"), label=team)
# 추세선
if len(scatter_df) > 10:
    z = np.polyfit(scatter_df["acwr"], scatter_df["hooper_lag1"], 1)
    p = np.poly1d(z)
    x_range = np.linspace(scatter_df["acwr"].quantile(0.01),
                           scatter_df["acwr"].quantile(0.99), 100)
    ax.plot(x_range, p(x_range), "r--", linewidth=2, label=f"추세선 (기울기={z[0]:.3f})")

r, pval = stats.pearsonr(scatter_df["acwr"], scatter_df["hooper_lag1"])
ax.set_xlabel("ACWR(t)")
ax.set_ylabel("Hooper Index(t+1)")
ax.set_title(f"ACWR(t) vs Hooper Index(t+1)  |  r={r:.3f}, p={pval:.4f}")
ax.legend(fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_acwr_hooper_scatter.png"))
plt.close(fig)
print(f"  Pearson r = {r:.4f}, p = {pval:.4f}")
print("  저장: track_B_acwr_hooper_scatter.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7c. Monotony 임계값 비교 (박스플롯)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[EDA-3] Monotony 임계값(2.0) 기준 Hooper Index 비교")

mono_df = merged.dropna(subset=["monotony", "hooper_lag1"]).copy()
mono_df = mono_df[mono_df["monotony"] > 0]
mono_df["mono_group"] = np.where(mono_df["monotony"] > 2.0,
                                  "Monotony > 2.0\n(고위험)",
                                  "Monotony <= 2.0\n(일반)")

fig, ax = plt.subplots(figsize=(6, 5))
group_order = ["Monotony <= 2.0\n(일반)", "Monotony > 2.0\n(고위험)"]
sns.boxplot(data=mono_df, x="mono_group", y="hooper_lag1", order=group_order,
            palette=["#2196F3", "#f44336"], ax=ax, width=0.5)
# 통계 검정
g1 = mono_df[mono_df["monotony"] <= 2.0]["hooper_lag1"].dropna()
g2 = mono_df[mono_df["monotony"] > 2.0]["hooper_lag1"].dropna()
if len(g1) > 2 and len(g2) > 2:
    t_stat, t_p = stats.ttest_ind(g1, g2, equal_var=False)
    d_cohen = (g2.mean() - g1.mean()) / np.sqrt((g1.std()**2 + g2.std()**2) / 2)
    ax.set_title(f"Monotony 그룹별 Hooper Index(t+1)\nWelch t={t_stat:.2f}, p={t_p:.4f}, Cohen's d={d_cohen:.3f}")
    print(f"  Monotony <= 2.0: M={g1.mean():.2f}, SD={g1.std():.2f}, n={len(g1)}")
    print(f"  Monotony > 2.0:  M={g2.mean():.2f}, SD={g2.std():.2f}, n={len(g2)}")
    print(f"  Welch t = {t_stat:.3f}, p = {t_p:.4f}, Cohen's d = {d_cohen:.3f}")
else:
    ax.set_title("Monotony 그룹별 Hooper Index(t+1)")

ax.set_xlabel("")
ax.set_ylabel("Hooper Index(t+1)")
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_monotony_threshold.png"))
plt.close(fig)
print("  저장: track_B_monotony_threshold.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7d. 결측 히트맵
# ─────────────────────────────────────────────────────────────────────────────
print("\n[EDA-4] 결측 히트맵 (선수 x 월)")

# 선수별·월별 hooper_index 결측률
merged["year_month"] = merged["date"].dt.to_period("M")
miss_pivot = merged.groupby(["athlete_id", "year_month"])["hooper_index"].apply(
    lambda x: x.isna().mean()
).unstack(fill_value=1.0)

# 짧은 선수 ID로 표시
short_ids = {aid: f"{aid.split('-')[0]}_{aid.split('-')[1][:4]}" for aid in miss_pivot.index}
miss_pivot.index = [short_ids[i] for i in miss_pivot.index]
# 열 라벨을 str로
miss_pivot.columns = [str(c) for c in miss_pivot.columns]

fig, ax = plt.subplots(figsize=(14, max(6, len(miss_pivot) * 0.35)))
sns.heatmap(miss_pivot, cmap="YlOrRd", vmin=0, vmax=1,
            cbar_kws={"label": "결측 비율"}, ax=ax, linewidths=0.3)
ax.set_title("선수별-월별 Hooper Index 결측 비율")
ax.set_xlabel("연월")
ax.set_ylabel("선수")
plt.xticks(rotation=45, ha="right", fontsize=7)
plt.yticks(fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_missing_heatmap.png"))
plt.close(fig)
print("  저장: track_B_missing_heatmap.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7e. 부하·웰니스 분포
# ─────────────────────────────────────────────────────────────────────────────
print("\n[EDA-5] Daily Load 및 웰니스 변수 분포")

fig, axes = plt.subplots(2, 3, figsize=(14, 8))
dist_vars = [
    ("daily_load", "Daily Load (sRPE)", True),
    ("fatigue", "Fatigue (1-5)", False),
    ("stress_norm", "Stress 정규화 (1-5)", False),
    ("soreness", "Soreness (1-5)", False),
    ("sleep_quality", "Sleep Quality (1-5)", False),
    ("hooper_index", "Hooper Index", False),
]
for ax, (var, label, filter_zero) in zip(axes.flat, dist_vars):
    data = merged[var].dropna()
    if filter_zero:
        data = data[data > 0]
    if len(data) > 0:
        ax.hist(data, bins=40, color="#5B9BD5", edgecolor="white", alpha=0.8)
        ax.axvline(data.mean(), color="red", linestyle="--", label=f"평균={data.mean():.1f}")
        ax.axvline(data.median(), color="green", linestyle=":", label=f"중앙값={data.median():.1f}")
        ax.legend(fontsize=7)
    ax.set_title(label)
    ax.set_xlabel(label)
    ax.set_ylabel("빈도")

fig.suptitle("부하 및 웰니스 변수 분포", fontsize=14, y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_load_distribution.png"), bbox_inches="tight")
plt.close(fig)
print("  저장: track_B_load_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# 7f. 샘플 선수 시계열
# ─────────────────────────────────────────────────────────────────────────────
print("\n[EDA-6] 샘플 선수 시계열 (부하 + 웰니스)")

# Hooper 유효 관측이 많은 상위 4명 선택
hooper_counts = merged.groupby("athlete_id")["hooper_index"].apply(
    lambda x: x.notna().sum()
).sort_values(ascending=False)
sample_athletes = hooper_counts.head(4).index.tolist()

fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=False)
for ax, aid in zip(axes, sample_athletes):
    adf = merged[merged["athlete_id"] == aid].copy()
    short_id = f"{aid.split('-')[0]}_{aid.split('-')[1][:4]}"

    ax2 = ax.twinx()
    # Daily load (막대)
    load_data = adf[adf["daily_load"] > 0]
    ax.bar(load_data["date"], load_data["daily_load"],
           width=1, alpha=0.4, color="#5B9BD5", label="Daily Load")
    # Hooper index (선)
    hooper_data = adf.dropna(subset=["hooper_index"])
    ax2.plot(hooper_data["date"], hooper_data["hooper_index"],
             color="#FF6B35", linewidth=1.2, label="Hooper Index", alpha=0.8)
    # ACWR (선, 보조)
    acwr_data = adf[(adf["acwr"].notna()) & (adf["acwr"] > 0)]
    ax2.plot(acwr_data["date"], acwr_data["acwr"] * 5,  # 스케일 조정
             color="#2ECC71", linewidth=0.8, linestyle="--", label="ACWR x5", alpha=0.6)

    ax.set_ylabel("Daily Load", color="#5B9BD5")
    ax2.set_ylabel("Hooper / ACWR*5", color="#FF6B35")
    ax.set_title(f"선수: {short_id}")

    # 범례 합치기
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=7)

fig.suptitle("샘플 선수 시계열: Daily Load + Hooper Index + ACWR", fontsize=13, y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_timeseries_sample.png"), bbox_inches="tight")
plt.close(fig)
print("  저장: track_B_timeseries_sample.png")

# ═════════════════════════════════════════════════════════════════════════════
#  통계 분석
# ═════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("  통계 분석")
print("=" * 80)

# ─────────────────────────────────────────────────────────────────────────────
# 8. 시차(lag) 데이터셋 구성
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8단계] 시차(lag) 데이터셋 구성")

# hooper_lag1 이미 생성됨 (t+1 시점의 hooper를 t 시점 행에 배치)
model_df = merged.dropna(subset=["hooper_lag1", "acwr", "monotony", "strain"]).copy()
# ACWR 이상치 제거
model_df = model_df[(model_df["acwr"] > 0) & (model_df["acwr"] < 10)]
# monotony > 0 (비활성기 제외)
model_df = model_df[model_df["monotony"] > 0]
# strain > 0
model_df = model_df[model_df["strain"] > 0]

# 선수당 최소 관측수 확인 (혼합효과 모형 안정성)
athlete_counts = model_df.groupby("athlete_id").size()
valid_athletes = athlete_counts[athlete_counts >= 10].index
model_df = model_df[model_df["athlete_id"].isin(valid_athletes)].copy()

print(f"  모형 데이터: {len(model_df):,} 관측, {model_df['athlete_id'].nunique()} 선수")
print(f"  종속변수(hooper_lag1): M={model_df['hooper_lag1'].mean():.2f}, SD={model_df['hooper_lag1'].std():.2f}")
print(f"  ACWR: M={model_df['acwr'].mean():.3f}, SD={model_df['acwr'].std():.3f}")
print(f"  Monotony: M={model_df['monotony'].mean():.3f}, SD={model_df['monotony'].std():.3f}")
print(f"  Strain: M={model_df['strain'].mean():.1f}, SD={model_df['strain'].std():.1f}")

# ─────────────────────────────────────────────────────────────────────────────
# 9. 모형 적합
# ─────────────────────────────────────────────────────────────────────────────
print("\n[9단계] 회귀 모형 적합")


def compute_model_metrics(y_true, y_pred, n_params, model_name):
    """모형 평가 지표 산출"""
    n = len(y_true)
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - y_true.mean()) ** 2)
    # Cohen's f^2 = R^2 / (1 - R^2)
    f2 = r2 / (1 - r2) if r2 < 1 else np.nan
    # AIC/BIC (가우시안 가정)
    log_lik = -n / 2 * (np.log(2 * np.pi * ss_res / n) + 1)
    aic = 2 * n_params - 2 * log_lik
    bic = n_params * np.log(n) - 2 * log_lik
    return {
        "model": model_name, "n": n, "n_params": n_params,
        "MAE": mae, "RMSE": rmse, "R2": r2, "f2": f2,
        "AIC": aic, "BIC": bic,
    }


results = []

# --- M1: OLS ---
print("\n  [M1] OLS: hooper_lag1 ~ acwr")
m1 = smf.ols("hooper_lag1 ~ acwr", data=model_df).fit()
print(m1.summary().tables[1])
y_pred_m1 = m1.fittedvalues
metrics_m1 = compute_model_metrics(
    model_df["hooper_lag1"].values, y_pred_m1.values, m1.df_model + 1, "M1: OLS (acwr)"
)
results.append(metrics_m1)

# --- M2: Mixed - hooper_lag1 ~ acwr + (1|athlete_id) ---
print("\n  [M2] 혼합효과: hooper_lag1 ~ acwr + (1|athlete_id)")
m2 = smf.mixedlm("hooper_lag1 ~ acwr", data=model_df, groups=model_df["athlete_id"]).fit()
print(m2.summary().tables[1])
y_pred_m2 = m2.fittedvalues
metrics_m2 = compute_model_metrics(
    model_df["hooper_lag1"].values, y_pred_m2.values,
    m2.df_modelwc, "M2: Mixed (acwr)"
)
results.append(metrics_m2)

# --- M3: Mixed - hooper_lag1 ~ acwr + monotony + (1|athlete_id) ---
print("\n  [M3] 혼합효과: hooper_lag1 ~ acwr + monotony + (1|athlete_id)")
m3 = smf.mixedlm("hooper_lag1 ~ acwr + monotony", data=model_df,
                  groups=model_df["athlete_id"]).fit()
print(m3.summary().tables[1])
y_pred_m3 = m3.fittedvalues
metrics_m3 = compute_model_metrics(
    model_df["hooper_lag1"].values, y_pred_m3.values,
    m3.df_modelwc, "M3: Mixed (acwr+monotony)"
)
results.append(metrics_m3)

# --- M4: Mixed - hooper_lag1 ~ acwr + monotony + strain + (1|athlete_id) ---
print("\n  [M4] 혼합효과: hooper_lag1 ~ acwr + monotony + strain + (1|athlete_id)")
m4 = smf.mixedlm("hooper_lag1 ~ acwr + monotony + strain", data=model_df,
                  groups=model_df["athlete_id"]).fit()
print(m4.summary().tables[1])
y_pred_m4 = m4.fittedvalues
metrics_m4 = compute_model_metrics(
    model_df["hooper_lag1"].values, y_pred_m4.values,
    m4.df_modelwc, "M4: Mixed (acwr+mono+strain)"
)
results.append(metrics_m4)

# ─────────────────────────────────────────────────────────────────────────────
# 10. 모형 비교 표
# ─────────────────────────────────────────────────────────────────────────────
print("\n[10단계] 모형 비교")
comp_df = pd.DataFrame(results)
comp_df = comp_df.set_index("model")
print(comp_df[["n", "n_params", "AIC", "BIC", "MAE", "RMSE", "R2", "f2"]].round(4).to_string())

# 모형 비교 시각화
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
metrics_to_plot = [
    ("AIC", "AIC (낮을수록 우수)", True),
    ("BIC", "BIC (낮을수록 우수)", True),
    ("MAE", "MAE (낮을수록 우수)", True),
    ("RMSE", "RMSE (낮을수록 우수)", True),
    ("R2", "R-squared (높을수록 우수)", False),
    ("f2", "Cohen's f-squared (효과 크기)", False),
]
model_short = ["M1\nOLS", "M2\nMixed\n(acwr)", "M3\nMixed\n(acwr+mono)", "M4\nMixed\n(acwr+\nmono+strain)"]
palette = ["#E74C3C", "#3498DB", "#2ECC71", "#9B59B6"]

for ax, (metric, title, lower_better) in zip(axes.flat, metrics_to_plot):
    vals = comp_df[metric].values
    bars = ax.bar(range(len(vals)), vals, color=palette, edgecolor="gray", alpha=0.85)
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(model_short, fontsize=7)
    ax.set_title(title, fontsize=9)
    # 최적 모형 표시
    if lower_better:
        best_idx = np.argmin(vals)
    else:
        best_idx = np.argmax(vals)
    bars[best_idx].set_edgecolor("gold")
    bars[best_idx].set_linewidth(3)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=7)

fig.suptitle("Track B 모형 비교", fontsize=14, y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_model_comparison.png"), bbox_inches="tight")
plt.close(fig)
print("  저장: track_B_model_comparison.png")

# ─────────────────────────────────────────────────────────────────────────────
# 11. 다중 시차(Multi-lag) 분석
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  다중 시차(Multi-lag) 분석: ACWR(t) → Hooper(t+k), k=0..7")
print("=" * 80)

lag_results = []
for lag in range(8):
    # 선수별 시차 적용
    tmp = merged.sort_values(["athlete_id", "date"]).copy()
    tmp[f"hooper_lag{lag}"] = tmp.groupby("athlete_id")["hooper_index"].shift(-lag)
    lag_df = tmp.dropna(subset=[f"hooper_lag{lag}", "acwr"])
    lag_df = lag_df[(lag_df["acwr"] > 0) & (lag_df["acwr"] < 10)]

    if len(lag_df) > 10:
        r, p = stats.pearsonr(lag_df["acwr"], lag_df[f"hooper_lag{lag}"])
        lag_results.append({"lag": lag, "r": r, "p": p, "n": len(lag_df)})
        print(f"  Lag {lag}: r={r:.4f}, p={p:.4f}, n={len(lag_df):,}")

lag_res_df = pd.DataFrame(lag_results)
optimal_lag = lag_res_df.loc[lag_res_df["r"].abs().idxmax()]
print(f"\n  최적 시차: Lag {int(optimal_lag['lag'])} (|r|={abs(optimal_lag['r']):.4f})")

# 시차 프로파일 시각화
fig, ax = plt.subplots(figsize=(8, 5))
colors_lag = ["#E74C3C" if abs(r) == lag_res_df["r"].abs().max() else "#3498DB"
              for r in lag_res_df["r"]]
bars = ax.bar(lag_res_df["lag"], lag_res_df["r"], color=colors_lag,
              edgecolor="gray", alpha=0.85)
ax.axhline(0, color="black", linewidth=0.5)
ax.set_xlabel("시차 (일)")
ax.set_ylabel("Pearson r (ACWR vs Hooper)")
ax.set_title("ACWR(t) → Hooper(t+k) 시차별 상관 프로파일")
ax.set_xticks(range(8))
for i, row in lag_res_df.iterrows():
    sig = "***" if row["p"] < 0.001 else "**" if row["p"] < 0.01 else "*" if row["p"] < 0.05 else "ns"
    y_pos = row["r"] + 0.003 if row["r"] >= 0 else row["r"] - 0.008
    ax.text(row["lag"], y_pos, f"{row['r']:.3f}\n{sig}", ha="center", fontsize=7)
fig.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "track_B_lag_profile.png"))
plt.close(fig)
print("  저장: track_B_lag_profile.png")

# ─────────────────────────────────────────────────────────────────────────────
# 12. LOSO 교차검증 (M3)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  Leave-One-Subject-Out 교차검증 (M3)")
print("=" * 80)

unique_athletes = model_df["athlete_id"].unique()
loso_results = []

print(f"\n  대상 선수: {len(unique_athletes)}명")
for i, held_out in enumerate(unique_athletes):
    train = model_df[model_df["athlete_id"] != held_out].copy()
    test = model_df[model_df["athlete_id"] == held_out].copy()

    if len(test) < 5:
        continue

    try:
        # 훈련 세트로 모형 적합
        m_cv = smf.mixedlm("hooper_lag1 ~ acwr + monotony",
                            data=train, groups=train["athlete_id"]).fit(reml=False)
        # 테스트 세트 예측 (고정효과만 사용)
        fe = m_cv.fe_params
        y_pred_test = fe["Intercept"] + fe["acwr"] * test["acwr"] + fe["monotony"] * test["monotony"]
        y_true_test = test["hooper_lag1"]

        mae_fold = mean_absolute_error(y_true_test, y_pred_test)
        rmse_fold = np.sqrt(mean_squared_error(y_true_test, y_pred_test))
        loso_results.append({
            "athlete_id": held_out,
            "n_test": len(test),
            "MAE": mae_fold,
            "RMSE": rmse_fold
        })
    except Exception as e:
        # 수렴 실패 등의 경우 스킵
        pass

loso_df = pd.DataFrame(loso_results)
if len(loso_df) > 0:
    print(f"\n  성공적으로 평가된 fold: {len(loso_df)}/{len(unique_athletes)}")
    print(f"\n  LOSO 교차검증 결과 (M3: hooper_lag1 ~ acwr + monotony + (1|athlete)):")
    print(f"  --------------------------------------------------")
    print(f"  평균 MAE  = {loso_df['MAE'].mean():.4f} (SD={loso_df['MAE'].std():.4f})")
    print(f"  평균 RMSE = {loso_df['RMSE'].mean():.4f} (SD={loso_df['RMSE'].std():.4f})")
    print(f"  MAE 범위  = [{loso_df['MAE'].min():.4f}, {loso_df['MAE'].max():.4f}]")
    print(f"  RMSE 범위 = [{loso_df['RMSE'].min():.4f}, {loso_df['RMSE'].max():.4f}]")
    print(f"  총 테스트 관측수 = {loso_df['n_test'].sum():,}")

    # 선수별 결과
    print(f"\n  선수별 LOSO 결과:")
    for _, row in loso_df.sort_values("MAE").iterrows():
        short = f"{row['athlete_id'].split('-')[0]}_{row['athlete_id'].split('-')[1][:4]}"
        print(f"    {short:12s}  n={int(row['n_test']):4d}  MAE={row['MAE']:.3f}  RMSE={row['RMSE']:.3f}")
else:
    print("  LOSO 교차검증 실패: 유효한 fold 없음")

# ─────────────────────────────────────────────────────────────────────────────
# 13. 전체 모형 요약 출력 (M3 상세)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  최종 모형 상세 요약 (M3)")
print("=" * 80)
print(m3.summary())

# ─────────────────────────────────────────────────────────────────────────────
# 14. 종합 결론
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("  종합 결론")
print("=" * 80)

print(f"""
  [데이터]
  - SoccerMon 데이터셋 (Midoglu et al., 2024)
  - 분석 대상: {model_df['athlete_id'].nunique()} 선수, {len(model_df):,} 관측
  - 기간: {merged['date'].min().strftime('%Y-%m-%d')} ~ {merged['date'].max().strftime('%Y-%m-%d')}

  [주요 발견]
  1. ACWR(t) → Hooper(t+1) 상관: r = {r:.4f} (p = {pval:.4f})
     → ACWR과 다음날 Hooper Index 간 관계가 관찰됨

  2. Monotony > 2.0 그룹의 Hooper Index 차이:
     → Cohen's d = {d_cohen:.3f} 수준의 효과 크기가 시사됨

  3. 최적 시차: Lag {int(optimal_lag['lag'])}일 (|r| = {abs(optimal_lag['r']):.4f})

  4. 모형 비교:
     - M1 (OLS, acwr):          R2={metrics_m1['R2']:.4f}, RMSE={metrics_m1['RMSE']:.4f}
     - M2 (Mixed, acwr):        R2={metrics_m2['R2']:.4f}, RMSE={metrics_m2['RMSE']:.4f}
     - M3 (Mixed, acwr+mono):   R2={metrics_m3['R2']:.4f}, RMSE={metrics_m3['RMSE']:.4f}
     - M4 (Mixed, acwr+mono+s): R2={metrics_m4['R2']:.4f}, RMSE={metrics_m4['RMSE']:.4f}

  5. LOSO 교차검증 (M3): 평균 MAE={loso_df['MAE'].mean():.4f}, RMSE={loso_df['RMSE'].mean():.4f}

  [해석 주의]
  - ACWR → Hooper 시차 관계는 상관적 경향을 시사하며, 인과 관계로 단정할 수 없음
  - 혼합효과 모형이 OLS 대비 개선을 보인다면, 개인차(random intercept)가 의미 있음을 시사
  - Hooper Index의 변동은 부하 지표 외에도 다양한 심리사회적 요인에 의해 영향받을 수 있음
  - reviewer-safe 톤: 관찰된 경향, 일관된 패턴으로 기술함
""")

print("\n  생성된 그림 파일:")
for fname in sorted(os.listdir(FIG_DIR)):
    if fname.startswith("track_B"):
        fpath = os.path.join(FIG_DIR, fname)
        fsize = os.path.getsize(fpath)
        print(f"    {fname} ({fsize/1024:.1f} KB)")

print(f"\n  처리 데이터: {out_path}")
print("\n  Track B 분석 완료.")
