"""
Gabbett sweet-spot 기준선 모듈 단위 테스트 (Stage 8 / 게이트 P2).

검증 항목
---------
- 위험점수 단조성: sweet 구간에서 최소(0), 양극단으로 갈수록 증가.
- 구간 라벨 정확성: under/sweet/danger 경계.
- evaluate_baseline: k별 행과 필수 컬럼(pr_auc, baseline, lift) 반환,
  PR-AUC ≥ 0, lift = pr_auc/baseline 정합.
- 실데이터(injury.csv + 패널, gap=7, merge_onset_panel)로 k=1/3/7
  기준선이 양성률(기저)·PR-AUC·lift를 산출하는지 확인.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data.injury_label import build_injury_onset_label, merge_onset_panel
from src.stats.injury_baseline import (
    evaluate_baseline,
    gabbett_risk_score,
    gabbett_risk_zone,
)

# 저장소 루트 기준 실데이터 경로
ROOT = Path(__file__).resolve().parents[1]
INJURY_CSV = ROOT / "data" / "raw" / "track_B" / "subjective" / "injury" / "injury.csv"
PANEL_CSV = ROOT / "data" / "processed" / "track_B_merged.csv"


@pytest.fixture(scope="module")
def injury_raw() -> pd.DataFrame:
    return pd.read_csv(INJURY_CSV)


@pytest.fixture(scope="module")
def panel() -> pd.DataFrame:
    return pd.read_csv(PANEL_CSV)


@pytest.fixture(scope="module")
def labeled_panel(injury_raw, panel) -> pd.DataFrame:
    """실데이터 패널에 gap=7 onset 라벨(k=1/3/7)을 결합한 분석용 패널."""
    onset = build_injury_onset_label(injury_raw, gap_days=7)
    return merge_onset_panel(panel, onset, horizons=(1, 3, 7))


# ---------------------------------------------------------------------------
# 1) 위험점수 단조성 (sweet에서 최소)
# ---------------------------------------------------------------------------

def test_risk_score_sweet_is_zero():
    """sweet 구간(0.8~1.5) 위험점수는 0(최저)이어야 한다."""
    for acwr in (0.8, 1.0, 1.3, 1.5):
        assert gabbett_risk_score(acwr) == pytest.approx(0.0)


def test_risk_score_extremes_high():
    """양극단(극저·고비)은 sweet보다 위험점수가 커야 한다."""
    assert gabbett_risk_score(0.2) > gabbett_risk_score(0.8)
    assert gabbett_risk_score(2.5) > gabbett_risk_score(1.5)
    # 극단값은 최대치 1에 접근.
    assert gabbett_risk_score(0.0) == pytest.approx(1.0)
    assert gabbett_risk_score(4.0) == pytest.approx(1.0)


def test_risk_score_monotonic_under_and_danger():
    """under는 ACWR↓일수록, danger는 ACWR↑일수록 위험점수가 단조 증가."""
    under = np.array([0.8, 0.6, 0.4, 0.2, 0.0])
    su = gabbett_risk_score(under)
    assert np.all(np.diff(su) >= 0)  # 점점 위험 증가

    danger = np.array([1.5, 2.0, 3.0, 4.0])
    sd = gabbett_risk_score(danger)
    assert np.all(np.diff(sd) >= 0)


def test_risk_score_range_and_clip():
    """캡(4.0) 초과·임의 값에서도 위험점수는 [0, 1] 범위여야 한다."""
    x = np.array([-0.5, 0.0, 1.0, 4.0, 6.0])
    s = gabbett_risk_score(x)
    assert np.all((s >= 0.0) & (s <= 1.0))


def test_risk_score_nan_propagates():
    """결측 ACWR은 위험점수도 NaN으로 전파(임의 단정 금지)."""
    s = gabbett_risk_score(np.array([np.nan, 1.0, 0.0]))
    assert np.isnan(s[0])
    assert s[1] == pytest.approx(0.0)
    assert s[2] == pytest.approx(1.0)


def test_risk_score_series_preserves_index():
    """Series 입력 시 동일 인덱스의 Series를 반환한다."""
    ser = pd.Series([0.5, 1.0, 2.0], index=[10, 20, 30])
    out = gabbett_risk_score(ser)
    assert isinstance(out, pd.Series)
    assert list(out.index) == [10, 20, 30]


# ---------------------------------------------------------------------------
# 2) 구간 라벨 정확성
# ---------------------------------------------------------------------------

def test_risk_zone_labels():
    """under/sweet/danger 경계가 정확해야 한다."""
    assert gabbett_risk_zone(0.5) == "under"
    assert gabbett_risk_zone(0.8) == "sweet"   # 경계 포함
    assert gabbett_risk_zone(1.2) == "sweet"
    assert gabbett_risk_zone(1.5) == "sweet"   # 경계 포함
    assert gabbett_risk_zone(2.0) == "danger"
    assert gabbett_risk_zone(np.nan) == "unknown"


def test_risk_zone_vectorized():
    """벡터 입력 시 라벨 배열을 반환한다."""
    z = gabbett_risk_zone(np.array([0.5, 1.0, 2.0]))
    assert list(z) == ["under", "sweet", "danger"]


# ---------------------------------------------------------------------------
# 3) evaluate_baseline — 합성 패널 (구조·정합)
# ---------------------------------------------------------------------------

def _synthetic_panel() -> pd.DataFrame:
    """위험점수가 라벨과 양의 상관을 갖도록 구성한 작은 합성 패널.

    danger 구간(고 ACWR) 일수에 onset 양성을 몰아넣어, 기준선이
    무작위(기저율)보다 높은 PR-AUC를 내도록 설계한다.
    """
    rng = np.random.default_rng(42)
    n = 400
    acwr = rng.uniform(0.3, 3.5, size=n)
    score = gabbett_risk_score(acwr)
    # 위험점수가 높을수록 양성 확률이 높은 라벨 생성.
    prob = 0.01 + 0.20 * score
    y = (rng.uniform(size=n) < prob).astype(int)
    return pd.DataFrame(
        {
            "acwr": acwr,
            "onset_next_1": y,
            "onset_next_3": y,
            "onset_next_7": y,
        }
    )


def test_evaluate_baseline_structure():
    """k별 행과 필수 컬럼이 반환되어야 한다."""
    df = _synthetic_panel()
    res = evaluate_baseline(df, horizons=(1, 3, 7))
    assert list(res["horizon"]) == [1, 3, 7]
    for col in ("pr_auc", "baseline", "lift", "recall_at_p50", "positive_rate"):
        assert col in res.columns
    # PR-AUC, 기저율은 음수가 아니어야 한다.
    assert (res["pr_auc"] >= 0).all()
    assert (res["baseline"] >= 0).all()


def test_evaluate_baseline_lift_consistency():
    """lift는 pr_auc/baseline과 정합해야 한다."""
    df = _synthetic_panel()
    res = evaluate_baseline(df, horizons=(1,))
    row = res.iloc[0]
    assert row["lift"] == pytest.approx(row["pr_auc"] / row["baseline"])


def test_evaluate_baseline_beats_random_on_synthetic():
    """설계상 양의 상관 합성 데이터에서 기준선 lift > 1(무작위 초과)."""
    df = _synthetic_panel()
    res = evaluate_baseline(df, horizons=(1,))
    assert res.iloc[0]["lift"] > 1.0


def test_evaluate_baseline_accepts_score_column():
    """문자열 컬럼명으로도 위험점수를 받을 수 있어야 한다."""
    df = _synthetic_panel()
    df = df.assign(risk=gabbett_risk_score(df["acwr"]))
    res = evaluate_baseline(df, score_col_or_fn="risk", horizons=(1,))
    assert res.iloc[0]["pr_auc"] >= 0


# ---------------------------------------------------------------------------
# 4) evaluate_baseline — 실데이터 (k=1/3/7)
# ---------------------------------------------------------------------------

def test_evaluate_baseline_real_panel(labeled_panel):
    """실데이터에서 k별 PR-AUC·기저율·lift가 산출되어야 한다."""
    res = evaluate_baseline(labeled_panel, horizons=(1, 3, 7))
    assert len(res) == 3
    # PR-AUC ≥ 0, 기저율은 희소(0~5%) 범위.
    assert (res["pr_auc"] >= 0).all()
    assert ((res["baseline"] > 0) & (res["baseline"] < 0.05)).all()
    # 양성률은 k가 길수록 증가(선행 위험창 단조).
    assert res["positive_rate"].is_monotonic_increasing


def test_real_panel_console_dump(labeled_panel, capsys):
    """실데이터 기준선 수치를 콘솔로 출력해 Stage 3 인용용 수치를 확보한다."""
    res = evaluate_baseline(labeled_panel, horizons=(1, 3, 7))
    with capsys.disabled():
        print("\n[P2] Gabbett sweet-spot 기준선 (실데이터, gap=7)")
        for _, r in res.iterrows():
            print(
                f"  k={int(r['horizon'])}일: "
                f"양성률(기저PR-AUC)={r['baseline']:.5f} "
                f"PR-AUC={r['pr_auc']:.5f} "
                f"recall@P0.5={r['recall_at_p50']:.4f} "
                f"lift={r['lift']:.3f} "
                f"(n={int(r['n'])}, n_pos={int(r['n_pos'])})"
            )
    assert len(res) == 3
