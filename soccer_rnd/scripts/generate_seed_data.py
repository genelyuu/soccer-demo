"""
PoV 합성 데이터 생성 스크립트.

15명 × 120일(2025-09-01 ~ 2025-12-29)의 현실적 합성 데이터를 생성한다.
기존 src/ 모듈(acwr.py, monotony_strain.py, hrv_features.py, preprocess.py)을
직접 호출하여 파이프라인 호환성을 보장한다.

재현성: np.random.default_rng(seed=42) — ADR-007 준수
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.metrics.hrv_features import rmssd, sdnn, ln_rmssd, ln_rmssd_rolling
from src.data.preprocess import compute_daily_load_metrics

# ---------------------------------------------------------------------------
# 상수 정의
# ---------------------------------------------------------------------------
SEED = 42
N_USERS = 15
START_DATE = pd.Timestamp("2025-09-01")
END_DATE = pd.Timestamp("2025-12-29")
SPIKE_WEEKS = {3, 8, 14}  # 부하 스파이크 주차 (0-indexed)

# 사용자 UUID 목록 (soccer seed.sql과 동일)
USER_UUIDS = [
    f"00000000-0000-0000-0000-{str(i).zfill(12)}" for i in range(1, N_USERS + 1)
]

# 사용자 이름 (시드 참조)
USER_NAMES = [
    "김철수", "이영희", "박민수", "정수진", "최동현",
    "한지민", "오세훈", "김도윤", "이서연", "박준혁",
    "최예린", "강민준", "윤서아", "임태윤", "조하늘",
]

# 포지션 목록
POSITIONS = [
    "GK", "CB", "ST", "CM", "CAM",
    "LW", "RB", "CDM", "LB", "RW",
    "CF", "CM", "RM", "CB", "WB",
]

TEAM_UUID = "10000000-0000-0000-0000-000000000001"

# 결측 비율
MISSING_RATE = 0.05


def _get_day_type(date: pd.Timestamp) -> str:
    """요일별 세션 타입 반환: 월~금 TRAINING, 토 MATCH, 일 REST."""
    dow = date.dayofweek
    if dow == 6:  # 일요일
        return "REST"
    elif dow == 5:  # 토요일
        return "MATCH"
    else:
        return "TRAINING"


def _week_index(date: pd.Timestamp) -> int:
    """시작일 기준 주차 인덱스 (0-indexed) 반환."""
    return (date - START_DATE).days // 7


def generate_track_b(rng: np.random.Generator) -> pd.DataFrame:
    """
    트랙 B 합성 데이터 생성.

    RPE, duration, Hooper 4항목, next_day_condition 포함.
    개인별 기저 특성(β₀)을 부여하고, ACWR/Monotony에 따라
    Hooper가 현실적으로 변동하도록 설계.
    """
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    records = []

    # 개인별 기저 특성
    base_hooper = rng.normal(3.0, 0.5, size=N_USERS)  # β₀: 개인 Hooper 기저 평균

    for u_idx, user_id in enumerate(USER_UUIDS):
        daily_loads = []

        for date in dates:
            day_type = _get_day_type(date)
            week_idx = _week_index(date)

            if day_type == "REST":
                # 휴식일: sRPE=0, 웰니스만 기록
                rpe = np.nan
                duration = np.nan
                srpe = 0.0
            elif day_type == "MATCH":
                rpe = float(np.clip(rng.normal(7.5, 1.0), 1, 10))
                duration = float(np.clip(rng.normal(90, 5), 60, 120))
                srpe = rpe * duration
            else:  # TRAINING
                rpe = float(np.clip(rng.normal(5.5, 1.5), 1, 10))
                duration = float(np.clip(rng.normal(75, 15), 30, 120))
                srpe = rpe * duration

            # 부하 스파이크 주차: RPE ×1.5
            if week_idx in SPIKE_WEEKS and day_type != "REST":
                rpe = float(np.clip(rpe * 1.5, 1, 10))
                srpe = rpe * duration if not np.isnan(duration) else 0.0

            daily_loads.append(srpe)

            records.append({
                "user_id": user_id,
                "athlete_id": user_id,
                "date": date,
                "session_type": day_type,
                "rpe": round(rpe, 1) if not np.isnan(rpe) else np.nan,
                "duration_min": round(duration, 1) if not np.isnan(duration) else np.nan,
                "srpe": round(srpe, 1),
                "_user_idx": u_idx,
            })

        # ACWR/Monotony 산출을 위한 임시 DataFrame
        user_df = pd.DataFrame({
            "athlete_id": [user_id] * len(dates),
            "date": dates,
            "srpe": daily_loads,
        })
        user_df = compute_daily_load_metrics(user_df, athlete_col="athlete_id", load_col="srpe")

        # Hooper 생성: ACWR/Monotony에 의존
        for i, date in enumerate(dates):
            rec = records[u_idx * len(dates) + i]

            acwr_val = user_df.iloc[i].get("acwr_rolling", np.nan)
            mono_val = user_df.iloc[i].get("monotony", np.nan)

            acwr_eff = acwr_val if not np.isnan(acwr_val) else 1.0
            mono_eff = mono_val if not np.isnan(mono_val) else 1.0

            # hooper_mean = β₀ + 2.5 * acwr + 1.5 * monotony
            hooper_mean = base_hooper[u_idx] + 2.5 * acwr_eff + 1.5 * mono_eff
            item_mean = hooper_mean / 4.0

            fatigue = int(np.clip(round(rng.normal(item_mean, 0.8)), 1, 7))
            soreness = int(np.clip(round(rng.normal(item_mean, 0.8)), 1, 7))
            stress = int(np.clip(round(rng.normal(item_mean, 0.8)), 1, 7))
            sleep = int(np.clip(round(rng.normal(item_mean, 0.8)), 1, 7))

            rec["fatigue"] = fatigue
            rec["stress"] = stress
            rec["doms"] = soreness  # soreness → doms
            rec["sleep"] = sleep

            # next_day_condition
            if acwr_eff > 1.5:
                p_worse = 0.5
            elif acwr_eff > 1.2:
                p_worse = 0.25
            else:
                p_worse = 0.1
            p_better = (1 - p_worse) * 0.4
            p_same = 1 - p_worse - p_better
            condition = rng.choice(
                ["WORSE", "SAME", "BETTER"],
                p=[p_worse, p_same, p_better],
            )
            rec["next_day_condition"] = condition

            # 부하 지표 추가
            for col in ["atl_rolling", "ctl_rolling", "acwr_rolling",
                         "atl_ewma", "ctl_ewma", "acwr_ewma",
                         "monotony", "strain"]:
                rec[col] = user_df.iloc[i].get(col, np.nan)

    df = pd.DataFrame(records)

    # 결측 5% 랜덤 삽입 (REST 제외 행의 Hooper 항목)
    non_rest_mask = df["session_type"] != "REST"
    non_rest_idx = df.index[non_rest_mask]
    n_missing = int(len(non_rest_idx) * MISSING_RATE)

    for col in ["fatigue", "stress", "doms", "sleep"]:
        missing_idx = rng.choice(non_rest_idx, size=n_missing, replace=False)
        df.loc[missing_idx, col] = np.nan

    # _user_idx 제거
    df.drop(columns=["_user_idx"], inplace=True)

    return df


def generate_track_a(rng: np.random.Generator, track_b_df: pd.DataFrame) -> pd.DataFrame:
    """
    트랙 A 합성 데이터 생성.

    track_b_df의 ACWR을 참조하여 HRV(RR 간격)를 생성한다.
    매일 아침 MORNING_REST 측정 가정.
    """
    dates = pd.date_range(START_DATE, END_DATE, freq="D")
    records = []

    for u_idx, user_id in enumerate(USER_UUIDS):
        # 개인 기저 RR 간격 (ms)
        base_rr = rng.normal(800, 40)

        # 해당 사용자의 track_b acwr_rolling 추출
        user_b = track_b_df[track_b_df["user_id"] == user_id].set_index("date")

        prev_acwr = 1.0  # 초기 ACWR

        daily_ln_rmssd_values = []

        for date in dates:
            # 이전 날의 ACWR 참조
            if date in user_b.index:
                acwr_val = user_b.loc[date, "acwr_rolling"]
                if not np.isnan(acwr_val):
                    prev_acwr = acwr_val

            # RR 간격 생성: mean_rr = 기저 − 50×(acwr − 1.0) + noise
            mean_rr = base_rr - 50.0 * (prev_acwr - 1.0) + rng.normal(0, 10)
            mean_rr = max(mean_rr, 500)  # 최소 500ms (120 bpm)

            n_beats = rng.integers(200, 301)
            rr_intervals = rng.normal(mean_rr, mean_rr * 0.05, size=n_beats)
            rr_intervals = np.clip(rr_intervals, 300, 1500)

            # HRV 지표 산출 (기존 모듈 직접 호출)
            rmssd_val = rmssd(rr_intervals, min_count=150)
            sdnn_val = sdnn(rr_intervals, min_count=150)
            ln_rmssd_val = ln_rmssd(rr_intervals, min_count=150)

            mean_rr_val = float(np.mean(rr_intervals))
            mean_hr_val = 60000.0 / mean_rr_val if mean_rr_val > 0 else np.nan

            daily_ln_rmssd_values.append(ln_rmssd_val)

            records.append({
                "user_id": user_id,
                "subject_id": user_id,
                "date": date,
                "rr_intervals_ms": rr_intervals.tolist(),
                "rr_count": len(rr_intervals),
                "rmssd": rmssd_val,
                "sdnn": sdnn_val,
                "ln_rmssd": ln_rmssd_val,
                "mean_rr": round(mean_rr_val, 2),
                "mean_hr": round(mean_hr_val, 2) if not np.isnan(mean_hr_val) else np.nan,
                "nn_count": len(rr_intervals),
                "valid": rmssd_val is not None,
            })

        # ln_rmssd_7d 산출
        ln_series = pd.Series(daily_ln_rmssd_values, dtype=float)
        ln_7d = ln_rmssd_rolling(ln_series, window=7)

        for i, date in enumerate(dates):
            rec_idx = u_idx * len(dates) + i
            records[rec_idx]["ln_rmssd_7d"] = (
                round(ln_7d.iloc[i], 6) if not np.isnan(ln_7d.iloc[i]) else np.nan
            )

    df = pd.DataFrame(records)
    return df


def build_track_b_csv(track_b_df: pd.DataFrame) -> pd.DataFrame:
    """트랙 B R&D 표준 스키마 CSV용 DataFrame 생성."""
    cols = [
        "athlete_id", "date", "rpe", "duration_min", "srpe",
        "fatigue", "stress", "doms", "sleep",
    ]
    out = track_b_df[cols].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def build_track_a_csv(track_a_df: pd.DataFrame, track_b_df: pd.DataFrame) -> pd.DataFrame:
    """트랙 A R&D 일별 스키마 CSV용 DataFrame 생성."""
    # track_b에서 acwr, monotony 가져오기
    b_metrics = track_b_df[["user_id", "date", "acwr_rolling", "acwr_ewma", "monotony"]].copy()

    merged = track_a_df.merge(
        b_metrics,
        on=["user_id", "date"],
        how="left",
    )

    cols = [
        "subject_id", "date", "rmssd", "sdnn", "ln_rmssd", "ln_rmssd_7d",
        "acwr_rolling", "acwr_ewma", "monotony",
    ]
    out = merged[cols].copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out


def main():
    """메인 실행: 합성 데이터 생성 및 CSV 저장."""
    rng = np.random.default_rng(SEED)
    output_dir = PROJECT_ROOT / "data" / "seed"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("[1/4] 트랙 B 합성 데이터 생성 중...")
    track_b_df = generate_track_b(rng)
    print(f"  - 트랙 B: {len(track_b_df)}행, {track_b_df['user_id'].nunique()}명")

    print("[2/4] 트랙 A 합성 데이터 생성 중...")
    track_a_df = generate_track_a(rng, track_b_df)
    print(f"  - 트랙 A: {len(track_a_df)}행, {track_a_df['user_id'].nunique()}명")

    print("[3/4] R&D 표준 스키마 CSV 저장 중...")
    # 트랙 B 표준 CSV
    track_b_csv = build_track_b_csv(track_b_df)
    track_b_csv.to_csv(output_dir / "seed_track_b.csv", index=False)
    print(f"  - data/seed/seed_track_b.csv ({len(track_b_csv)}행)")

    # 트랙 A 표준 CSV
    track_a_csv = build_track_a_csv(track_a_df, track_b_df)
    track_a_csv.to_csv(output_dir / "seed_track_a.csv", index=False)
    print(f"  - data/seed/seed_track_a.csv ({len(track_a_csv)}행)")

    print("[4/4] 중간 테이블별 CSV 저장 중...")
    # 세션 테이블
    sessions = track_b_df[["user_id", "date", "session_type", "duration_min"]].copy()
    sessions.to_csv(output_dir / "seed_sessions.csv", index=False)

    # Pre-session wellness
    wellness = track_b_df[["user_id", "date", "fatigue", "stress", "doms", "sleep"]].copy()
    wellness.to_csv(output_dir / "seed_pre_wellness.csv", index=False)

    # Post-session feedback
    feedback = track_b_df[["user_id", "date", "rpe", "session_type"]].copy()
    feedback.to_csv(output_dir / "seed_post_feedback.csv", index=False)

    # Next-day reviews
    reviews = track_b_df[["user_id", "date", "next_day_condition"]].copy()
    reviews.to_csv(output_dir / "seed_next_day.csv", index=False)

    # HRV measurements (RR 간격 배열은 CSV 비호환이므로 별도 처리)
    hrv_meas = track_a_df[["user_id", "date", "rr_count", "mean_rr", "mean_hr"]].copy()
    hrv_meas.to_csv(output_dir / "seed_hrv_measurements.csv", index=False)

    # Daily HRV metrics
    hrv_daily = track_a_df[[
        "user_id", "date", "rmssd", "sdnn", "ln_rmssd",
        "ln_rmssd_7d", "mean_rr", "mean_hr", "nn_count", "valid",
    ]].copy()
    hrv_daily.to_csv(output_dir / "seed_daily_hrv.csv", index=False)

    # Computed load metrics
    load_metrics = track_b_df[[
        "user_id", "date", "srpe",
        "atl_rolling", "ctl_rolling", "acwr_rolling",
        "atl_ewma", "ctl_ewma", "acwr_ewma",
        "monotony", "strain",
    ]].copy()
    load_metrics.to_csv(output_dir / "seed_load_metrics.csv", index=False)

    # 사용자 메타 정보
    users_meta = pd.DataFrame({
        "user_id": USER_UUIDS,
        "name": USER_NAMES,
        "position": POSITIONS,
    })
    users_meta.to_csv(output_dir / "seed_users.csv", index=False)

    print("\n합성 데이터 생성 완료.")
    print(f"출력 디렉토리: {output_dir}")

    # 요약 통계
    non_rest = track_b_df[track_b_df["session_type"] != "REST"]
    print(f"\n--- 요약 ---")
    print(f"총 사용자: {N_USERS}명")
    print(f"기간: {START_DATE.date()} ~ {END_DATE.date()} ({len(pd.date_range(START_DATE, END_DATE))}일)")
    print(f"세션 수 (REST 제외): {len(non_rest)}행")
    print(f"RPE 범위: {non_rest['rpe'].min():.1f} ~ {non_rest['rpe'].max():.1f}")
    print(f"Hooper 항목 결측률: {non_rest['fatigue'].isna().mean():.1%}")
    print(f"ACWR 유효 범위: {track_b_df['acwr_rolling'].dropna().min():.2f} ~ "
          f"{track_b_df['acwr_rolling'].dropna().max():.2f}")


if __name__ == "__main__":
    main()
