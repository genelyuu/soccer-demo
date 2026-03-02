"""
시드 데이터 및 Supabase 뷰 로더.

시드 CSV 또는 Supabase ETL 뷰(v_rnd_track_a, v_rnd_track_b)에서
R&D 표준 스키마로 데이터를 로딩한다.
기존 loader.py의 validate_schema()를 재사용하여 스키마 호환성을 보장한다.
"""

import pandas as pd

from src.data.loader import validate_schema, TRACK_B_REQUIRED_COLS


# ---------------------------------------------------------------------------
# 시드 트랙 A 필수 컬럼 (일별 HRV 스키마)
# ---------------------------------------------------------------------------
SEED_TRACK_A_REQUIRED_COLS: list[str] = [
    "subject_id",
    "date",
    "rmssd",
    "sdnn",
    "ln_rmssd",
    "ln_rmssd_7d",
]


# ---------------------------------------------------------------------------
# 시드 트랙 B 로더
# ---------------------------------------------------------------------------
def load_seed_track_b(
    filepath: str = "data/seed/seed_track_b.csv",
) -> pd.DataFrame:
    """
    시드 트랙 B CSV를 R&D 표준 스키마로 로딩한다.

    기존 load_track_b()와 동일한 출력 스키마를 보장한다.
    필수 컬럼: athlete_id, date, rpe, duration_min, srpe,
              fatigue, stress, doms, sleep

    Parameters
    ----------
    filepath : str
        시드 CSV 파일 경로 (기본값: data/seed/seed_track_b.csv).

    Returns
    -------
    pd.DataFrame
        트랙 B 표준 스키마 DataFrame. date 컬럼은 datetime 타입.
    """
    df = pd.read_csv(filepath)
    validate_schema(df, TRACK_B_REQUIRED_COLS, "Seed Track B")

    df["date"] = pd.to_datetime(df["date"])
    return df


# ---------------------------------------------------------------------------
# 시드 트랙 A 로더
# ---------------------------------------------------------------------------
def load_seed_track_a(
    filepath: str = "data/seed/seed_track_a.csv",
) -> pd.DataFrame:
    """
    시드 트랙 A CSV를 R&D 일별 HRV 스키마로 로딩한다.

    필수 컬럼: subject_id, date, rmssd, sdnn, ln_rmssd, ln_rmssd_7d

    Parameters
    ----------
    filepath : str
        시드 CSV 파일 경로 (기본값: data/seed/seed_track_a.csv).

    Returns
    -------
    pd.DataFrame
        트랙 A 일별 HRV 스키마 DataFrame. date 컬럼은 datetime 타입.
    """
    df = pd.read_csv(filepath)
    validate_schema(df, SEED_TRACK_A_REQUIRED_COLS, "Seed Track A")

    df["date"] = pd.to_datetime(df["date"])
    return df
