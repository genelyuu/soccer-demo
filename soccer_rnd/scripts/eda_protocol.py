# -*- coding: utf-8 -*-
"""
연구 프로토콜용 실데이터 EDA 산출 스크립트 (read-only).
부상 예측 재설계에 필요한 실측치(onset 이벤트, 불균형비, 결측, 분포)를 계산한다.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_B = ROOT / "data" / "raw" / "track_B" / "subjective"
RAW_A = ROOT / "data" / "raw" / "track_A"
PROC = ROOT / "data" / "processed"

def section(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)

# ───────────────────────── Track B: 병합 패널 ─────────────────────────
section("TRACK B — 병합 패널 (processed/track_B_merged.csv)")
m = pd.read_csv(PROC / "track_B_merged.csv", parse_dates=["date"])
print(f"행 수(athlete-days): {len(m):,}")
print(f"선수 수: {m['athlete_id'].nunique()}  | 팀: {sorted(m['team'].unique())}")
print(f"기간: {m['date'].min().date()} ~ {m['date'].max().date()} "
      f"({(m['date'].max()-m['date'].min()).days}일)")
print(f"선수당 평균 관측일: {len(m)/m['athlete_id'].nunique():.0f}")
cols = ["daily_load", "acwr", "atl", "monotony", "strain",
        "fatigue", "stress", "soreness", "sleep_quality", "hooper_index"]
print("\n주요 변수 요약(분석 패널):")
print(m[cols].describe().T[["count", "mean", "std", "min", "50%", "max"]]
      .round(2).to_string())
print("\n결측률(%):")
print((m[cols].isna().mean() * 100).round(1).to_string())
# 활성일(부하>0) 비율
active = (m["daily_load"] > 0).mean() * 100
print(f"\n활성일(daily_load>0) 비율: {active:.1f}%")
# ACWR 위험구간
acwr_valid = m["acwr"].replace([np.inf, -np.inf], np.nan).dropna()
print(f"ACWR>1.5 비율: {(acwr_valid>1.5).mean()*100:.1f}%  "
      f"| ACWR 0.8~1.3(sweet spot): {((acwr_valid>=0.8)&(acwr_valid<=1.3)).mean()*100:.1f}%")
print(f"Monotony>2.0 비율: {(m['monotony']>2.0).mean()*100:.1f}%")

# ───────────────────────── 부상 라벨 공학 ─────────────────────────
section("TRACK B — 부상 라벨 공학 (injury.csv)")
inj = pd.read_csv(RAW_B / "injury" / "injury.csv")
inj["date"] = pd.to_datetime(inj["timestamp"], format="%d.%m.%Y", errors="coerce")
print(f"원자료 부상-일(injury-days) 총: {len(inj)}")
print(f"부상 기록 보유 선수 수: {inj['player_name'].nunique()}")

# 중증도/부위 파싱
def parse_type(s):
    try:
        d = json.loads(s)
        if isinstance(d, dict):
            region = list(d.keys())[0] if d else "unknown"
            sev = list(d.values())[0] if d else "unknown"
            return region, sev
    except Exception:
        pass
    return "unknown", "unknown"

parsed = inj["type"].apply(parse_type)
inj["region"] = parsed.apply(lambda x: x[0])
inj["severity"] = parsed.apply(lambda x: x[1])
print("\n중증도 분포(부상-일 기준):")
print(inj["severity"].value_counts().to_string())
print("\n부위 상위 8(부상-일 기준):")
print(inj["region"].value_counts().head(8).to_string())

# onset 정의: 선수별 날짜 정렬 후 직전 부상과 gap>=GAP일이면 신규 발생
for GAP in (3, 7):
    onset_count = 0
    for pid, g in inj.dropna(subset=["date"]).groupby("player_name"):
        ds = g["date"].sort_values().drop_duplicates().reset_index(drop=True)
        prev = None
        for d in ds:
            if prev is None or (d - prev).days >= GAP:
                onset_count += 1
            prev = d
    print(f"\nonset 이벤트 수 (gap>={GAP}일 기준): {onset_count}")

# 발생률 (per 1000 athlete-days), gap>=7 기준 재계산
onset_rows = []
for pid, g in inj.dropna(subset=["date"]).groupby("player_name"):
    ds = g["date"].sort_values().drop_duplicates().reset_index(drop=True)
    prev = None
    for d in ds:
        if prev is None or (d - prev).days >= 7:
            onset_rows.append((pid, d))
        prev = d
onset_df = pd.DataFrame(onset_rows, columns=["athlete_id", "date"])
ad = len(m)
print(f"\n총 athlete-days(분석패널): {ad:,}")
print(f"부상 발생률(onset/1000 athlete-days): {len(onset_df)/ad*1000:.2f}")

# 불균형비: 향후 k일 내 onset 발생을 양성으로
section("TRACK B — 클래스 불균형 (향후 k일 내 부상 onset)")
mm = m[["athlete_id", "date"]].copy()
onset_set = set(zip(onset_df["athlete_id"], onset_df["date"].dt.normalize()))
# athlete_id 매칭 가능 여부 점검
match_ids = len(set(onset_df["athlete_id"]) & set(m["athlete_id"]))
print(f"onset 선수 ID 중 패널과 매칭되는 수: {match_ids} / {onset_df['athlete_id'].nunique()}")
for k in (1, 3, 7):
    def has_onset(row):
        a = row["athlete_id"]; d = row["date"]
        for dd in range(1, k + 1):
            if (a, (d + pd.Timedelta(days=dd)).normalize()) in onset_set:
                return 1
        return 0
    y = mm.apply(has_onset, axis=1)
    pos = int(y.sum())
    print(f"k={k}일: 양성 {pos} / {len(y):,}  "
          f"(유병률 {pos/len(y)*100:.2f}%, 불균형비 1:{(len(y)-pos)/max(pos,1):.0f})")

# 질병
section("TRACK B — 질병 (illness.csv)")
ill = pd.read_csv(RAW_B / "illness" / "illness.csv")
print(f"질병 이벤트 총: {len(ill)} (검정력 부족 → 탐색/민감도 한정)")
print(f"질병 기록 보유 선수 수: {ill['player_name'].nunique()}")

# ───────────────────────── Track A ─────────────────────────
section("TRACK A — 피험자/HRV (ACTES)")
si = pd.read_csv(RAW_A / "subject-info.csv")
print(f"피험자 수: {len(si)}")
print(f"연령: {si['age'].min()}~{si['age'].max()} (평균 {si['age'].mean():.1f})")
print(f"종목 분포:\n{si['sport'].value_counts().to_string()}")
print(f"VT1 power 평균: {si['P_vt1'].mean():.0f}W | VT2 power 평균: {si['P_vt2'].mean():.0f}W")

tm = pd.read_csv(RAW_A / "test_measure.csv")
print(f"\nbeat-level 행 수: {len(tm):,}")
print(f"RR(ms) 범위: {tm['RR'].min():.0f}~{tm['RR'].max():.0f}")
print(f"power(W) 범위: {tm['power'].min():.0f}~{tm['power'].max():.0f}")

hz = pd.read_csv(PROC / "track_A_hrv_by_zone.csv")
print("\n파워구간별 HRV(rMSSD/ln_rMSSD) 요약:")
g = hz.groupby("power_zone").agg(
    n=("subject", "count"),
    power=("power_mean", "mean"),
    rmssd=("rmssd", "mean"),
    rmssd_sd=("rmssd", "std"),
    ln_rmssd=("ln_rmssd", "mean"),
).round(2)
order = ["Rest", "Low", "Moderate", "High"]
g = g.reindex([o for o in order if o in g.index])
print(g.to_string())

print("\n[EDA 완료]")
