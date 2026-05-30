"""
부상 onset 라벨 생성 모듈 (Stage 8 / 게이트 P0).

원시 부상 기록(`injury.csv`, 부상-일 단위)을 **독립 부상 사건(onset)**으로 변환한다.

onset 정의(ADR-014, RESEARCH_PROTOCOL §B.2)
------------------------------------------
동일 선수에서 직전 부상-일과의 간격(gap)이 ``gap_days``일 **이상**이면
새로운 독립 사건(onset)으로 간주한다. 즉 7일 미만 간격으로 이어지는
연속 부상-일은 **하나의 부상 에피소드**로 묶고, 그 시작일만 onset으로 센다.
이 규칙으로 SoccerMon 부상 기록은 **onset 43건**(1.75/1000 athlete-days)을 산출하며,
이는 동일 데이터셋을 분석한 외부 연구(arXiv 2601.19479)의 43건과 일치한다.

주요 기능
---------
- parse_injury_records   : 원시 injury.csv 파싱(timestamp·severity·동일일 dedup)
- build_injury_onset_label : gap>=7 규칙으로 onset 사건 도출
- compute_incidence      : onset 수·발생률(1000 athlete-days당) 산출
- merge_onset_panel      : 분석 패널에 k=1/3/7 선행 위험창 라벨 결합
"""

from __future__ import annotations

import json
from typing import Iterable

import numpy as np
import pandas as pd

# onset 판정 기본 간격(일). 직전 부상-일과 이 값 이상 떨어지면 새 사건.
DEFAULT_GAP_DAYS: int = 7

# 선행 예측 위험창(일). label[t] = [t+1, t+k] 사이 onset 발생 여부.
DEFAULT_HORIZONS: tuple[int, ...] = (1, 3, 7)


# ---------------------------------------------------------------------------
# 1) 원시 부상 기록 파싱
# ---------------------------------------------------------------------------

def _parse_type(type_str: str) -> tuple[str, str]:
    """`type` 컬럼(JSON 문자열)에서 (부위, 중증도)를 추출한다.

    예: ``'{"right_thigh":"minor"}'`` → ``("right_thigh", "minor")``.
    복수 부위가 기록된 경우 첫 항목을 대표값으로, 중증도는 'major'가
    하나라도 있으면 'major'로 격상한다(보수적 처리).
    """
    try:
        obj = json.loads(type_str)
    except (json.JSONDecodeError, TypeError):
        return ("unknown", "unknown")
    if not isinstance(obj, dict) or len(obj) == 0:
        return ("unknown", "unknown")
    body_part = next(iter(obj.keys()))
    severities = [str(v).lower() for v in obj.values()]
    severity = "major" if "major" in severities else severities[0]
    return (body_part, severity)


def parse_injury_records(injury_df: pd.DataFrame) -> pd.DataFrame:
    """원시 injury.csv를 파싱하여 부상-일 단위 표준 형태로 변환한다.

    - ``timestamp``(DD.MM.YYYY) → ``date``(datetime, 일 단위)
    - ``type``(JSON) → ``body_part``, ``severity``
    - 동일 (선수, 날짜) 중복 행 제거(dedup). 중복 시 중증도는 'major' 우선.

    Parameters
    ----------
    injury_df : pd.DataFrame
        원시 컬럼 ``player_name``, ``type``, ``timestamp``을 가진 DataFrame.

    Returns
    -------
    pd.DataFrame
        컬럼 ``player_name``, ``date``, ``body_part``, ``severity``
        (선수·날짜 기준 1행, 날짜 오름차순 정렬).
    """
    required = {"player_name", "type", "timestamp"}
    missing = required - set(injury_df.columns)
    if missing:
        raise ValueError(f"injury 원시 데이터에 필수 컬럼 누락: {sorted(missing)}")

    df = injury_df.copy()
    df["date"] = pd.to_datetime(df["timestamp"], format="%d.%m.%Y").dt.normalize()
    parsed = df["type"].apply(_parse_type)
    df["body_part"] = parsed.apply(lambda x: x[0])
    df["severity"] = parsed.apply(lambda x: x[1])

    # 중증도 우선순위: major > minor > unknown (dedup 시 보수적으로 상위 유지)
    sev_rank = {"major": 2, "minor": 1, "unknown": 0}
    df["_sev_rank"] = df["severity"].map(sev_rank).fillna(0)
    df = df.sort_values(["player_name", "date", "_sev_rank"], ascending=[True, True, False])
    df = df.drop_duplicates(subset=["player_name", "date"], keep="first")

    out = df[["player_name", "date", "body_part", "severity"]].reset_index(drop=True)
    return out


# ---------------------------------------------------------------------------
# 2) onset 사건 도출 (gap>=7)
# ---------------------------------------------------------------------------

def build_injury_onset_label(
    injury_df: pd.DataFrame,
    gap_days: int = DEFAULT_GAP_DAYS,
) -> pd.DataFrame:
    """부상-일 기록에서 독립 onset 사건을 도출한다.

    선수별로 부상-일을 정렬한 뒤, 직전 부상-일과의 간격이 ``gap_days``일
    이상이면 새 onset으로 표시한다(첫 부상-일은 항상 onset).

    Parameters
    ----------
    injury_df : pd.DataFrame
        원시 injury.csv DataFrame(parse_injury_records 입력과 동일 컬럼).
    gap_days : int, default 7
        독립 사건 판정 간격(일). 민감도 분석에서 3과 7을 비교한다.

    Returns
    -------
    pd.DataFrame
        onset 사건 1건당 1행. 컬럼 ``player_name``, ``onset_date``,
        ``body_part``, ``severity``.
    """
    parsed = parse_injury_records(injury_df)
    onsets: list[pd.DataFrame] = []
    for player, grp in parsed.groupby("player_name", sort=True):
        grp = grp.sort_values("date").reset_index(drop=True)
        prev = grp["date"].shift(1)
        gap = (grp["date"] - prev).dt.days
        is_onset = prev.isna() | (gap >= gap_days)
        onsets.append(grp.loc[is_onset])

    result = pd.concat(onsets, ignore_index=True) if onsets else parsed.iloc[0:0].copy()
    result = result.rename(columns={"date": "onset_date"})
    result = result[["player_name", "onset_date", "body_part", "severity"]]
    result = result.sort_values(["player_name", "onset_date"]).reset_index(drop=True)
    return result


# ---------------------------------------------------------------------------
# 3) 발생률 산출
# ---------------------------------------------------------------------------

def compute_incidence(onset_df: pd.DataFrame, panel_df: pd.DataFrame) -> dict[str, float]:
    """onset 수와 발생률(1000 athlete-days당)을 산출한다.

    Parameters
    ----------
    onset_df : pd.DataFrame
        build_injury_onset_label 결과.
    panel_df : pd.DataFrame
        분석 패널(athlete-day 단위). 행 수 = 총 노출 athlete-days.

    Returns
    -------
    dict
        ``n_onset``, ``athlete_days``, ``rate_per_1000``,
        ``n_injured_players``.
    """
    n_onset = int(len(onset_df))
    athlete_days = int(len(panel_df))
    rate = (n_onset / athlete_days * 1000.0) if athlete_days else float("nan")
    return {
        "n_onset": n_onset,
        "athlete_days": athlete_days,
        "rate_per_1000": rate,
        "n_injured_players": int(onset_df["player_name"].nunique()),
    }


# ---------------------------------------------------------------------------
# 4) 패널에 선행 위험창 라벨 결합
# ---------------------------------------------------------------------------

def merge_onset_panel(
    panel_df: pd.DataFrame,
    onset_df: pd.DataFrame,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    athlete_col: str = "athlete_id",
    date_col: str = "date",
) -> pd.DataFrame:
    """분석 패널에 onset 사건과 선행 위험창 라벨을 결합한다.

    각 horizon ``k``에 대해 ``onset_next_{k}`` = 1 이면 해당 athlete-day의
    **다음 [t+1, t+k] 구간에 onset이 발생**함을 의미한다(선행 예측 라벨).
    또한 당일 onset 여부 ``onset_event``도 부여한다.

    Parameters
    ----------
    panel_df : pd.DataFrame
        athlete-day 패널(``athlete_id``, ``date`` 포함).
    onset_df : pd.DataFrame
        build_injury_onset_label 결과(``player_name``, ``onset_date``).
    horizons : iterable of int, default (1, 3, 7)
        선행 위험창 길이(일).

    Returns
    -------
    pd.DataFrame
        입력 패널에 ``onset_event``, ``onset_next_{k}`` 컬럼이 추가된 복사본.
    """
    panel = panel_df.copy()
    panel[date_col] = pd.to_datetime(panel[date_col]).dt.normalize()

    horizons = list(horizons)
    panel["onset_event"] = 0
    for k in horizons:
        panel[f"onset_next_{k}"] = 0

    onset_by_player: dict[str, np.ndarray] = {
        player: np.sort(grp["onset_date"].values)
        for player, grp in onset_df.groupby("player_name", sort=False)
    }

    for idx, row in panel.iterrows():
        dates = onset_by_player.get(row[athlete_col])
        if dates is None:
            continue
        d = np.datetime64(row[date_col], "D")
        # 당일 onset
        if np.any(dates == d):
            panel.at[idx, "onset_event"] = 1
        # 선행 위험창: (t, t+k]
        for k in horizons:
            hi = d + np.timedelta64(k, "D")
            if np.any((dates > d) & (dates <= hi)):
                panel.at[idx, f"onset_next_{k}"] = 1

    return panel
