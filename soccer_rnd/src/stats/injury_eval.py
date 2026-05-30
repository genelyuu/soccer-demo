"""
부상예측 공용 평가 유틸 (Stage 8 / 게이트 P0~P3 공유).

희소 이벤트(부상 onset, 양성률 ~1%) 평가는 ROC-AUC가 과대평가되므로
**PR-AUC(평균정밀도)**와 고정 정밀도에서의 재현율을 1차 지표로 사용한다
(RESEARCH_PROTOCOL §C.2, §F). 검증은 시간분리(2020→2021)와 선수분리
중첩 LOSO를 병행해 누수를 차단한다.

주요 기능
---------
- pr_auc              : PR 곡선 아래 면적(평균정밀도)
- recall_at_precision : 목표 정밀도 이상에서 달성 가능한 최대 재현율
- baseline_pr_auc     : 무작위(기저율) PR-AUC = 양성률
- time_split          : 연도 기준 시간분리(학습 2020 → 검정 2021)
- loso_subject_splits : 선수(그룹) 단위 Leave-One-Subject-Out 분할 인덱스
- gap_sensitivity     : onset 간격(gap) 민감도 — onset 수·발생률 비교
"""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve


# ---------------------------------------------------------------------------
# 1) 불균형 분류 지표 (PR 기반)
# ---------------------------------------------------------------------------

def pr_auc(y_true: Iterable[int], y_score: Iterable[float]) -> float:
    """PR 곡선 아래 면적(평균정밀도, average precision)을 반환한다.

    희소 이벤트에서 ROC-AUC 대신 사용하는 1차 지표. 양성이 없으면 NaN.
    """
    y_true = np.asarray(list(y_true))
    y_score = np.asarray(list(y_score))
    if y_true.sum() == 0:
        return float("nan")
    return float(average_precision_score(y_true, y_score))


def baseline_pr_auc(y_true: Iterable[int]) -> float:
    """무작위 분류기의 PR-AUC = 양성률(기저율). 모형 비교의 하한선."""
    y_true = np.asarray(list(y_true))
    n = len(y_true)
    return float(y_true.sum() / n) if n else float("nan")


def recall_at_precision(
    y_true: Iterable[int],
    y_score: Iterable[float],
    min_precision: float = 0.5,
) -> float:
    """목표 정밀도(min_precision) 이상을 만족하는 지점의 최대 재현율.

    운영 임계값 선택(precision 보장하 recall 극대화) 관점의 지표.
    해당 정밀도를 만족하는 지점이 없으면 0.0.
    """
    y_true = np.asarray(list(y_true))
    y_score = np.asarray(list(y_score))
    if y_true.sum() == 0:
        return float("nan")
    precision, recall, _ = precision_recall_curve(y_true, y_score)
    mask = precision >= min_precision
    if not np.any(mask):
        return 0.0
    return float(np.max(recall[mask]))


# ---------------------------------------------------------------------------
# 2) 누수 차단 검증 분할
# ---------------------------------------------------------------------------

def time_split(
    df: pd.DataFrame,
    date_col: str = "date",
    train_year: int = 2020,
    test_year: int = 2021,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """연도 기준 시간분리 분할. 학습(train_year) → 검정(test_year).

    시즌 전환에 따른 분포이동(concept drift)에 대한 강건성을 평가한다.
    """
    dates = pd.to_datetime(df[date_col])
    train = df.loc[dates.dt.year == train_year].copy()
    test = df.loc[dates.dt.year == test_year].copy()
    return train, test


def loso_subject_splits(
    df: pd.DataFrame,
    group_col: str = "athlete_id",
) -> list[tuple[np.ndarray, np.ndarray]]:
    """선수(그룹) 단위 Leave-One-Subject-Out 분할 인덱스 목록.

    한 선수를 검정셋으로 남기고 나머지로 학습 — 개인 정보 누수를 차단한다.
    각 원소는 (train_idx, test_idx) 위치 인덱스 쌍.
    """
    groups = df[group_col].to_numpy()
    splits: list[tuple[np.ndarray, np.ndarray]] = []
    for g in pd.unique(groups):
        test_idx = np.where(groups == g)[0]
        train_idx = np.where(groups != g)[0]
        splits.append((train_idx, test_idx))
    return splits


# ---------------------------------------------------------------------------
# 3) onset 간격 민감도
# ---------------------------------------------------------------------------

def gap_sensitivity(
    injury_df: pd.DataFrame,
    panel_df: pd.DataFrame,
    gaps: Iterable[int] = (3, 7),
) -> pd.DataFrame:
    """onset 판정 간격(gap)에 따른 onset 수·발생률 민감도 표를 만든다.

    라벨 정의의 결과 민감성(RESEARCH_PROTOCOL §I-3)을 정량화한다.
    """
    # 지연 임포트(순환 의존 방지)
    from src.data.injury_label import build_injury_onset_label, compute_incidence

    rows = []
    for gap in gaps:
        onset = build_injury_onset_label(injury_df, gap_days=gap)
        inc = compute_incidence(onset, panel_df)
        rows.append({"gap_days": gap, **inc})
    return pd.DataFrame(rows)
