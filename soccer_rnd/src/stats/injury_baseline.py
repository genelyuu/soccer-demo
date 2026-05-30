"""
부상예측 규칙기반 기준선(Gabbett sweet-spot) 모듈 (Stage 8 / 게이트 P2).

데이터 기반 모형(로지스틱·GBM 등)을 평가하기 전에, 반드시 **초과해야 할
비학습 벤치마크**로 Gabbett sweet-spot 룰을 박제한다(Gabbett 2016).
ACWR(급성:만성 부하비)의 "sweet spot"(대략 0.8~1.5)은 저위험,
극저(<0.8)와 고비(>1.5)는 부상위험 증가로 알려져 있다. 본 모듈은 이
직관을 단일 위험점수로 환산해, onset 선행 위험창 라벨에 대한 PR-AUC·
recall@precision·lift를 산출한다.

평가 지표 선택 근거
-------------------
onset 양성률이 ~1%로 희소하므로 ROC-AUC는 과대평가된다. 따라서
`src.stats.injury_eval`의 **PR-AUC(평균정밀도)**를 1차 지표로 쓰고,
기저율(=양성률) 대비 lift(PR-AUC/기저율)로 무작위 대비 식별력을 본다
(RESEARCH_PROTOCOL §C.2·§F). 검정력 제약(EPV≤4, onset=43)으로 절대
수치는 작을 수 있으며 reviewer-safe 톤으로 해석한다.

ACWR 캡핑 전제(ADR)
-------------------
입력 패널의 ``acwr`` 컬럼은 전처리 단계에서 **상한 4.0으로 캡핑**되어
있다(만성 부하 분모가 매우 작은 초기 구간의 비율 폭주 방지).
즉 danger 구간(>1.5)의 위험점수는 [1.5, 4.0] 구간에서만 변동하며,
4.0 이상은 모두 동일한 최대 위험으로 포화된다. 본 모듈의 위험점수는 이
캡핑 전제를 그대로 수용해 [0, 1] 단조 점수로 변환한다.

주요 기능
---------
- gabbett_risk_score : ACWR → 위험점수[0~1], sweet에서 최소·양극단에서 증가
- gabbett_risk_zone  : ACWR → 'under'/'sweet'/'danger' 라벨
- evaluate_baseline  : k별 PR-AUC·기저율·recall@precision·lift 표 산출
"""

from __future__ import annotations

from typing import Callable, Iterable

import numpy as np
import pandas as pd

from src.stats.injury_eval import baseline_pr_auc, pr_auc, recall_at_precision

# Gabbett sweet-spot 경계(ADR/문헌 기본값). low 미만은 저부하, high 초과는 고부하.
DEFAULT_LOW: float = 0.8
DEFAULT_HIGH: float = 1.5

# 전처리에서 적용된 ACWR 상한(캡핑). danger 구간 정규화 기준값.
ACWR_CAP: float = 4.0

# 선행 예측 위험창(일) 기본값. injury_label.DEFAULT_HORIZONS와 정합.
DEFAULT_HORIZONS: tuple[int, ...] = (1, 3, 7)


# ---------------------------------------------------------------------------
# 1) Gabbett 위험점수 / 구간 라벨
# ---------------------------------------------------------------------------

def gabbett_risk_score(
    acwr,
    low: float = DEFAULT_LOW,
    high: float = DEFAULT_HIGH,
):
    """ACWR을 위험점수[0~1]로 매핑한다(sweet spot에서 최소, 양극단에서 증가).

    Gabbett sweet-spot 직관을 단조 변환으로 박제한다.

    - sweet 구간 ``low <= acwr <= high`` : 위험점수 = 0 (최저 위험).
    - under 구간 ``acwr < low`` : ``(low - acwr) / low``. ACWR이 0으로
      갈수록 1에 접근(저부하 위험이 단조 증가).
    - danger 구간 ``acwr > high`` : ``(acwr - high) / (ACWR_CAP - high)``.
      ACWR이 캡(4.0)으로 갈수록 1에 접근. 캡 초과분은 1로 포화(clip).

    스칼라/Series/ndarray 모두 지원한다. 결측(NaN)은 NaN으로 전파해
    위험을 임의로 0/1로 단정하지 않는다(reviewer-safe).

    Parameters
    ----------
    acwr : float | array-like
        급성:만성 부하비(전처리에서 상한 4.0 캡핑됨).
    low, high : float
        sweet spot 하한·상한. 기본 0.8, 1.5.

    Returns
    -------
    float | np.ndarray
        입력 형태에 대응하는 위험점수[0~1]. (Series 입력 시 동일 인덱스 Series)
    """
    is_scalar = np.isscalar(acwr)
    index = acwr.index if isinstance(acwr, pd.Series) else None
    x = np.asarray(acwr, dtype=float)

    score = np.zeros_like(x, dtype=float)

    # 저부하(under): sweet 하한에서 멀어질수록 증가, 0에서 최대 1.
    under = x < low
    score[under] = (low - x[under]) / low

    # 고부하(danger): sweet 상한에서 멀어질수록 증가, 캡(4.0)에서 1.
    danger = x > high
    score[danger] = (x[danger] - high) / (ACWR_CAP - high)

    # [0, 1] 클리핑(캡 초과 ACWR·수치오차 방지) 및 NaN 전파.
    score = np.clip(score, 0.0, 1.0)
    score = np.where(np.isnan(x), np.nan, score)

    if is_scalar:
        return float(score)
    if index is not None:
        return pd.Series(score, index=index, name="gabbett_risk")
    return score


def gabbett_risk_zone(
    acwr,
    low: float = DEFAULT_LOW,
    high: float = DEFAULT_HIGH,
):
    """ACWR을 'under'/'sweet'/'danger' 구간 라벨로 분류한다.

    - ``acwr < low`` → 'under'
    - ``low <= acwr <= high`` → 'sweet'
    - ``acwr > high`` → 'danger'
    - 결측(NaN) → 'unknown'

    스칼라/Series/ndarray 모두 지원한다.
    """
    is_scalar = np.isscalar(acwr)
    index = acwr.index if isinstance(acwr, pd.Series) else None
    x = np.asarray(acwr, dtype=float)

    zone = np.full(x.shape, "sweet", dtype=object)
    zone[x < low] = "under"
    zone[x > high] = "danger"
    zone[np.isnan(x)] = "unknown"

    if is_scalar:
        return str(zone.item())
    if index is not None:
        return pd.Series(zone, index=index, name="gabbett_zone")
    return zone


# ---------------------------------------------------------------------------
# 2) 기준선 평가 표
# ---------------------------------------------------------------------------

def evaluate_baseline(
    panel_with_labels: pd.DataFrame,
    score_col_or_fn: str | Callable[[pd.DataFrame], "pd.Series | np.ndarray"] = gabbett_risk_score,
    horizons: Iterable[int] = DEFAULT_HORIZONS,
    acwr_col: str = "acwr",
) -> pd.DataFrame:
    """각 선행 위험창 k에 대한 기준선 식별력 표를 산출한다.

    위험점수를 고정한 채, k별 라벨 ``onset_next_{k}``에 대해
    PR-AUC·기저율·recall@precision=0.5·lift를 계산한다.

    Parameters
    ----------
    panel_with_labels : pd.DataFrame
        ``merge_onset_panel`` 결과(``onset_next_{k}`` 라벨 포함) + ``acwr`` 컬럼.
    score_col_or_fn : str | callable, default gabbett_risk_score
        - str  : 패널에서 위험점수로 쓸 컬럼명.
        - callable : 패널을 받아 위험점수(Series/ndarray)를 반환하는 함수.
          기본값 ``gabbett_risk_score``는 ``acwr_col`` 컬럼에 적용된다.
    horizons : iterable of int, default (1, 3, 7)
        평가할 선행 위험창 길이(일).
    acwr_col : str, default "acwr"
        기본 점수 함수가 사용할 ACWR 컬럼명.

    Returns
    -------
    pd.DataFrame
        k별 1행. 컬럼:
        ``horizon``, ``n``, ``n_pos``, ``positive_rate``,
        ``pr_auc``, ``baseline``(기저율=무작위 PR-AUC),
        ``recall_at_p50``, ``lift``(= pr_auc / baseline).
        NaN 점수가 있는 행은 평가에서 제외(해당 k 라벨과 함께 정합 유지).
    """
    # 위험점수 산출(컬럼 지정 또는 함수 적용).
    if callable(score_col_or_fn):
        scores = score_col_or_fn(panel_with_labels[acwr_col])
        score_arr = np.asarray(scores, dtype=float)
    else:
        score_arr = np.asarray(panel_with_labels[score_col_or_fn], dtype=float)

    valid = ~np.isnan(score_arr)

    rows = []
    for k in horizons:
        label_col = f"onset_next_{k}"
        if label_col not in panel_with_labels.columns:
            raise ValueError(f"패널에 라벨 컬럼이 없습니다: {label_col}")

        y = np.asarray(panel_with_labels[label_col], dtype=float)
        # 점수 결측 행 제외(점수·라벨 정합 유지).
        mask = valid & ~np.isnan(y)
        y_true = y[mask].astype(int)
        y_score = score_arr[mask]

        n = int(len(y_true))
        n_pos = int(y_true.sum())
        base = baseline_pr_auc(y_true)
        ap = pr_auc(y_true, y_score)
        rec = recall_at_precision(y_true, y_score, min_precision=0.5)
        lift = (ap / base) if (base and base > 0) else float("nan")

        rows.append(
            {
                "horizon": k,
                "n": n,
                "n_pos": n_pos,
                "positive_rate": (n_pos / n) if n else float("nan"),
                "pr_auc": ap,
                "baseline": base,
                "recall_at_p50": rec,
                "lift": lift,
            }
        )

    return pd.DataFrame(rows)
