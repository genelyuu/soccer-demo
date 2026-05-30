"""
부상 onset 라벨 모듈 단위 테스트 (Stage 8 / 게이트 P0).

핵심 합격 게이트: gap>=7 규칙으로 실제 SoccerMon 부상 기록에서
**onset 43건·발생률 1.75/1000 athlete-days**가 재현되는지 검증한다
(ADR-014, RESEARCH_PROTOCOL §B.2·§H-P0, 외부검증 arXiv 2601.19479와 일치).
또한 동일일 dedup, gap 민감도(3 vs 7), 선행 위험창 라벨 결합 정합성을 검증한다.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.data.injury_label import (
    build_injury_onset_label,
    compute_incidence,
    merge_onset_panel,
    parse_injury_records,
)
from src.stats.injury_eval import gap_sensitivity

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


# ---------------------------------------------------------------------------
# 합격 게이트: onset=43, rate~1.75/1000 재현
# ---------------------------------------------------------------------------

def test_onset_count_is_43(injury_raw, panel):
    """gap>=7 규칙으로 독립 onset 43건이 재현되어야 한다."""
    onset = build_injury_onset_label(injury_raw, gap_days=7)
    assert len(onset) == 43


def test_incidence_rate(injury_raw, panel):
    """발생률이 1.75/1000 athlete-days(±0.01) 범위여야 한다."""
    onset = build_injury_onset_label(injury_raw, gap_days=7)
    inc = compute_incidence(onset, panel)
    assert inc["n_onset"] == 43
    assert inc["athlete_days"] == 24596
    assert inc["rate_per_1000"] == pytest.approx(1.75, abs=0.01)
    assert inc["n_injured_players"] == 15


# ---------------------------------------------------------------------------
# 파싱·dedup 정합성
# ---------------------------------------------------------------------------

def test_parse_dedup(injury_raw):
    """동일 (선수, 날짜) 중복은 1행으로 dedup되어야 한다."""
    parsed = parse_injury_records(injury_raw)
    dup = parsed.duplicated(subset=["player_name", "date"]).sum()
    assert dup == 0
    # 파싱 결과는 원시(162행, 동일일 중복 포함)보다 적어야 한다.
    assert len(parsed) < len(injury_raw)
    assert set(parsed["severity"].unique()) <= {"minor", "major", "unknown"}


def test_severity_parsed(injury_raw):
    """type(JSON)에서 부위·중증도가 추출되어야 한다."""
    parsed = parse_injury_records(injury_raw)
    assert parsed["body_part"].notna().all()
    assert (parsed["body_part"] != "unknown").any()


# ---------------------------------------------------------------------------
# gap 민감도 (3 vs 7)
# ---------------------------------------------------------------------------

def test_gap_sensitivity(injury_raw, panel):
    """gap=3은 gap=7보다 onset 수가 많아야 한다(에피소드 분할 증가)."""
    sens = gap_sensitivity(injury_raw, panel, gaps=(3, 7))
    n3 = sens.loc[sens["gap_days"] == 3, "n_onset"].iloc[0]
    n7 = sens.loc[sens["gap_days"] == 7, "n_onset"].iloc[0]
    assert n7 == 43
    assert n3 > n7


# ---------------------------------------------------------------------------
# 선행 위험창 라벨 결합
# ---------------------------------------------------------------------------

def test_merge_onset_panel(injury_raw, panel):
    """패널 결합 시 행 수 보존 + 위험창 라벨이 생성되어야 한다."""
    onset = build_injury_onset_label(injury_raw, gap_days=7)
    merged = merge_onset_panel(panel, onset, horizons=(1, 3, 7))
    # 행 수 보존
    assert len(merged) == len(panel)
    for k in (1, 3, 7):
        col = f"onset_next_{k}"
        assert col in merged.columns
        assert set(merged[col].unique()) <= {0, 1}
    # 위험창은 길수록 양성이 많거나 같아야 한다(단조 증가).
    assert merged["onset_next_1"].sum() <= merged["onset_next_3"].sum()
    assert merged["onset_next_3"].sum() <= merged["onset_next_7"].sum()
    # 당일 onset 합은 43 이하(패널 기간 밖 onset 제외 가능).
    assert 0 < merged["onset_event"].sum() <= 43


def test_onset_next_positive_rate(injury_raw, panel):
    """k=7 선행 위험창 양성률은 희소(대략 1% 안팎)여야 한다."""
    onset = build_injury_onset_label(injury_raw, gap_days=7)
    merged = merge_onset_panel(panel, onset, horizons=(7,))
    rate = merged["onset_next_7"].mean()
    assert 0 < rate < 0.05
