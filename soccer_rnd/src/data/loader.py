"""
데이터 로딩 및 스키마 검증 모듈.

CSV 파일을 읽어 트랙 A/B 표준 스키마에 맞게 검증하고 DataFrame으로 반환한다.
표준 스키마 정의: docs/DATA_SCHEMA_MAPPING.md 참조.
"""

import pandas as pd


# ---------------------------------------------------------------------------
# 표준 스키마 필수 컬럼 정의
# ---------------------------------------------------------------------------

TRACK_A_REQUIRED_COLS: list[str] = [
    "subject_id",
    "session_id",
    "timestamp",
    "rr_interval_ms",
    "power_watts",
]

TRACK_B_REQUIRED_COLS: list[str] = [
    "athlete_id",
    "date",
    "rpe",
    "duration_min",
    "srpe",
    "fatigue",
    "stress",
    "doms",
    "sleep",
]


# ---------------------------------------------------------------------------
# 스키마 검증
# ---------------------------------------------------------------------------

def validate_schema(
    df: pd.DataFrame,
    required_cols: list[str],
    schema_name: str,
) -> None:
    """
    DataFrame에 필수 컬럼이 모두 존재하는지 검증한다.

    누락된 컬럼이 있으면 ValueError를 발생시키며, 에러 메시지에
    스키마 이름과 누락 컬럼 목록을 포함한다.

    Parameters
    ----------
    df : pd.DataFrame
        검증 대상 DataFrame.
    required_cols : list[str]
        필수 컬럼 이름 목록.
    schema_name : str
        스키마 이름 (에러 메시지 출력용, 예: "Track A", "Track B").

    Raises
    ------
    ValueError
        필수 컬럼이 하나라도 누락된 경우.
    """
    existing_cols = set(df.columns)
    missing = [col for col in required_cols if col not in existing_cols]

    if missing:
        raise ValueError(
            f"[{schema_name}] 필수 컬럼 누락: {missing}. "
            f"필요 컬럼: {required_cols}"
        )


# ---------------------------------------------------------------------------
# 트랙 A 로더
# ---------------------------------------------------------------------------

def load_track_a(filepath: str) -> pd.DataFrame:
    """
    트랙 A CSV 파일을 로딩하고 표준 스키마를 검증한다.

    필수 컬럼: subject_id, session_id, timestamp, rr_interval_ms, power_watts
    (docs/DATA_SCHEMA_MAPPING.md 1.1절 참조)

    Parameters
    ----------
    filepath : str
        CSV 파일 경로.

    Returns
    -------
    pd.DataFrame
        표준 스키마가 검증된 트랙 A DataFrame.

    Raises
    ------
    ValueError
        필수 컬럼이 누락된 경우.
    FileNotFoundError
        파일이 존재하지 않는 경우.
    """
    df = pd.read_csv(filepath)
    validate_schema(df, TRACK_A_REQUIRED_COLS, "Track A")
    return df


# ---------------------------------------------------------------------------
# 트랙 B 로더
# ---------------------------------------------------------------------------

def load_track_b(filepath: str) -> pd.DataFrame:
    """
    트랙 B CSV 파일을 로딩하고 표준 스키마를 검증한다.

    필수 컬럼: athlete_id, date, rpe, duration_min, srpe, fatigue, stress,
    doms, sleep (docs/DATA_SCHEMA_MAPPING.md 1.2절 참조)

    date 컬럼은 자동으로 datetime 형식으로 변환된다.

    Parameters
    ----------
    filepath : str
        CSV 파일 경로.

    Returns
    -------
    pd.DataFrame
        표준 스키마가 검증된 트랙 B DataFrame. date 컬럼은 datetime 타입.

    Raises
    ------
    ValueError
        필수 컬럼이 누락된 경우.
    FileNotFoundError
        파일이 존재하지 않는 경우.
    """
    df = pd.read_csv(filepath)
    validate_schema(df, TRACK_B_REQUIRED_COLS, "Track B")

    # date 컬럼을 datetime으로 변환
    df["date"] = pd.to_datetime(df["date"])

    return df
