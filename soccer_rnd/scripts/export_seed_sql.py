"""
시드 DataFrame → INSERT SQL 변환 스크립트.

generate_seed_data.py가 생성한 CSV를 읽어 PostgreSQL INSERT 문으로 변환한다.
FK 순서: users → team_members → user_profiles → training_sessions
       → pre_session_wellness → post_session_feedback → next_day_reviews
       → hrv_measurements → daily_hrv_metrics → computed_load_metrics

출력: data/seed/seed_insert.sql
"""

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd


SEED_DIR = PROJECT_ROOT / "data" / "seed"
OUTPUT_FILE = SEED_DIR / "seed_insert.sql"

TEAM_UUID = "10000000-0000-0000-0000-000000000001"

# post_condition 매핑: RPE → condition
POST_CONDITION_MAP = {
    (1, 3): "GOOD",
    (3, 5): "NEUTRAL",
    (5, 7): "NEUTRAL",
    (7, 9): "BAD",
    (9, 11): "VERY_BAD",
}


def _sql_val(val) -> str:
    """Python 값을 SQL 리터럴로 변환."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "NULL"
    if isinstance(val, str):
        escaped = val.replace("'", "''")
        return f"'{escaped}'"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, np.integer)):
        return str(int(val))
    if isinstance(val, (float, np.floating)):
        return f"{float(val):.4f}"
    return str(val)


def _uuid5(namespace_str: str, name: str) -> str:
    """결정적 UUID5 생성."""
    ns = uuid.UUID(namespace_str)
    return str(uuid.uuid5(ns, name))


# 고정 네임스페이스 (시드 데이터 전용)
NS_SESSION = "a0000000-0000-0000-0000-000000000001"
NS_PRE = "a0000000-0000-0000-0000-000000000002"
NS_POST = "a0000000-0000-0000-0000-000000000003"
NS_NEXT = "a0000000-0000-0000-0000-000000000004"
NS_HRV = "a0000000-0000-0000-0000-000000000005"
NS_HRV_DAILY = "a0000000-0000-0000-0000-000000000006"
NS_METRICS = "a0000000-0000-0000-0000-000000000007"


def _rpe_to_condition(rpe_val) -> str:
    """RPE 값을 post_condition ENUM으로 매핑."""
    if rpe_val is None or np.isnan(rpe_val):
        return "NEUTRAL"
    for (lo, hi), cond in POST_CONDITION_MAP.items():
        if lo <= rpe_val < hi:
            return cond
    return "VERY_BAD"


def export_training_sessions(track_b: pd.DataFrame) -> list[str]:
    """training_sessions INSERT 생성."""
    lines = [
        "-- training_sessions",
        "INSERT INTO training_sessions (id, user_id, team_id, session_type, session_date, duration_min, "
        "has_pre_wellness, has_post_feedback, has_next_day_review) VALUES",
    ]
    values = []
    for _, row in track_b.iterrows():
        sid = _uuid5(NS_SESSION, f"{row['user_id']}_{row['date']}")
        session_type = row["session_type"]
        has_pre = session_type != "REST" and not np.isnan(row.get("fatigue", np.nan))
        has_post = session_type != "REST" and not np.isnan(row.get("rpe", np.nan))
        has_next = session_type != "REST"

        values.append(
            f"  ('{sid}', '{row['user_id']}', '{TEAM_UUID}', "
            f"'{session_type}', '{row['date']}', {_sql_val(row['duration_min'])}, "
            f"{_sql_val(has_pre)}, {_sql_val(has_post)}, {_sql_val(has_next)})"
        )
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT DO NOTHING;\n")
    return lines


def export_pre_wellness(track_b: pd.DataFrame) -> list[str]:
    """pre_session_wellness INSERT 생성."""
    lines = [
        "-- pre_session_wellness",
        "INSERT INTO pre_session_wellness (id, session_id, user_id, fatigue, soreness, stress, sleep) VALUES",
    ]
    values = []
    for _, row in track_b.iterrows():
        if row["session_type"] == "REST":
            continue
        # 모든 4항목이 유효해야 함
        if any(np.isnan(row.get(c, np.nan)) for c in ["fatigue", "stress", "doms", "sleep"]):
            continue
        sid = _uuid5(NS_SESSION, f"{row['user_id']}_{row['date']}")
        pid = _uuid5(NS_PRE, f"{row['user_id']}_{row['date']}")
        values.append(
            f"  ('{pid}', '{sid}', '{row['user_id']}', "
            f"{int(row['fatigue'])}, {int(row['doms'])}, "
            f"{int(row['stress'])}, {int(row['sleep'])})"
        )
    if not values:
        return []
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT DO NOTHING;\n")
    return lines


def export_post_feedback(track_b: pd.DataFrame) -> list[str]:
    """post_session_feedback INSERT 생성."""
    lines = [
        "-- post_session_feedback",
        "INSERT INTO post_session_feedback (id, session_id, user_id, session_rpe, condition) VALUES",
    ]
    values = []
    for _, row in track_b.iterrows():
        if row["session_type"] == "REST":
            continue
        if np.isnan(row.get("rpe", np.nan)):
            continue
        sid = _uuid5(NS_SESSION, f"{row['user_id']}_{row['date']}")
        fid = _uuid5(NS_POST, f"{row['user_id']}_{row['date']}")
        rpe_int = int(np.clip(round(row["rpe"]), 1, 10))
        condition = _rpe_to_condition(row["rpe"])
        values.append(
            f"  ('{fid}', '{sid}', '{row['user_id']}', {rpe_int}, '{condition}')"
        )
    if not values:
        return []
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT DO NOTHING;\n")
    return lines


def export_next_day_reviews(track_b: pd.DataFrame) -> list[str]:
    """next_day_reviews INSERT 생성."""
    lines = [
        "-- next_day_reviews",
        "INSERT INTO next_day_reviews (id, session_id, user_id, condition) VALUES",
    ]
    values = []
    for _, row in track_b.iterrows():
        if row["session_type"] == "REST":
            continue
        cond = row.get("next_day_condition")
        if not cond or (isinstance(cond, float) and np.isnan(cond)):
            continue
        sid = _uuid5(NS_SESSION, f"{row['user_id']}_{row['date']}")
        nid = _uuid5(NS_NEXT, f"{row['user_id']}_{row['date']}")
        values.append(
            f"  ('{nid}', '{sid}', '{row['user_id']}', '{cond}')"
        )
    if not values:
        return []
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT DO NOTHING;\n")
    return lines


def export_daily_hrv(track_a: pd.DataFrame) -> list[str]:
    """daily_hrv_metrics INSERT 생성."""
    lines = [
        "-- daily_hrv_metrics",
        "INSERT INTO daily_hrv_metrics (id, user_id, metric_date, rmssd, sdnn, ln_rmssd, "
        "ln_rmssd_7d, mean_rr, mean_hr, nn_count, valid) VALUES",
    ]
    values = []
    for _, row in track_a.iterrows():
        did = _uuid5(NS_HRV_DAILY, f"{row['user_id']}_{row['date']}")
        values.append(
            f"  ('{did}', '{row['user_id']}', '{row['date']}', "
            f"{_sql_val(row.get('rmssd'))}, {_sql_val(row.get('sdnn'))}, "
            f"{_sql_val(row.get('ln_rmssd'))}, {_sql_val(row.get('ln_rmssd_7d'))}, "
            f"{_sql_val(row.get('mean_rr'))}, {_sql_val(row.get('mean_hr'))}, "
            f"{_sql_val(row.get('nn_count'))}, {_sql_val(row.get('valid'))})"
        )
    if not values:
        return []
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT (user_id, metric_date) DO NOTHING;\n")
    return lines


def export_computed_metrics(track_b: pd.DataFrame) -> list[str]:
    """computed_load_metrics INSERT 생성."""
    lines = [
        "-- computed_load_metrics",
        "INSERT INTO computed_load_metrics (id, user_id, metric_date, daily_load, "
        "atl_rolling, ctl_rolling, acwr_rolling, atl_ewma, ctl_ewma, acwr_ewma, "
        "monotony, strain_value) VALUES",
    ]
    values = []
    for _, row in track_b.iterrows():
        mid = _uuid5(NS_METRICS, f"{row['user_id']}_{row['date']}")
        values.append(
            f"  ('{mid}', '{row['user_id']}', '{row['date']}', "
            f"{_sql_val(row.get('srpe'))}, "
            f"{_sql_val(row.get('atl_rolling'))}, {_sql_val(row.get('ctl_rolling'))}, "
            f"{_sql_val(row.get('acwr_rolling'))}, "
            f"{_sql_val(row.get('atl_ewma'))}, {_sql_val(row.get('ctl_ewma'))}, "
            f"{_sql_val(row.get('acwr_ewma'))}, "
            f"{_sql_val(row.get('monotony'))}, {_sql_val(row.get('strain'))})"
        )
    if not values:
        return []
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT (user_id, metric_date) DO NOTHING;\n")
    return lines


def main():
    """메인: CSV 읽기 → SQL 생성."""
    print("시드 CSV → INSERT SQL 변환 시작...")

    # CSV 로드 — athlete_id를 user_id로 통일
    track_b_full = pd.read_csv(SEED_DIR / "seed_track_b.csv", parse_dates=["date"])
    track_b_full.rename(columns={"athlete_id": "user_id"}, inplace=True)

    sessions = pd.read_csv(SEED_DIR / "seed_sessions.csv", parse_dates=["date"])
    next_day = pd.read_csv(SEED_DIR / "seed_next_day.csv", parse_dates=["date"])
    load_metrics = pd.read_csv(SEED_DIR / "seed_load_metrics.csv", parse_dates=["date"])

    # 병합
    merged_b = track_b_full.merge(
        sessions[["user_id", "date", "session_type"]],
        on=["user_id", "date"],
        how="left",
    )
    merged_b = merged_b.merge(
        next_day[["user_id", "date", "next_day_condition"]],
        on=["user_id", "date"],
        how="left",
    )
    merged_b = merged_b.merge(
        load_metrics[["user_id", "date", "atl_rolling", "ctl_rolling", "acwr_rolling",
                       "atl_ewma", "ctl_ewma", "acwr_ewma", "monotony", "strain"]],
        on=["user_id", "date"],
        how="left",
        suffixes=("", "_lm"),
    )

    # 트랙 A
    track_a = pd.read_csv(SEED_DIR / "seed_daily_hrv.csv", parse_dates=["date"])

    # SQL 생성
    sql_parts = [
        "-- PoV 시드 데이터 INSERT",
        "-- 생성: scripts/export_seed_sql.py",
        "-- 의존: 00003_training_wellness_schema.sql 테이블이 먼저 생성되어야 함",
        "",
    ]

    sql_parts.extend(export_training_sessions(merged_b))
    sql_parts.extend(export_pre_wellness(merged_b))
    sql_parts.extend(export_post_feedback(merged_b))
    sql_parts.extend(export_next_day_reviews(merged_b))
    sql_parts.extend(export_daily_hrv(track_a))
    sql_parts.extend(export_computed_metrics(merged_b))

    # 파일 출력
    sql_text = "\n".join(sql_parts)
    OUTPUT_FILE.write_text(sql_text, encoding="utf-8")
    print(f"SQL 파일 생성 완료: {OUTPUT_FILE}")
    print(f"파일 크기: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
