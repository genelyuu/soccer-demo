# -*- coding: utf-8 -*-
"""
부상예측 게이트 P3 — 생존·삼각검증 모듈 단위 테스트 (Stage 8).

소형 합성 데이터(시드 고정)로 세 설계를 검증한다. 합성은 ACWR이 높을수록
onset 위험이 증가하도록 생성하므로, 각 설계의 효과 방향이 '위험↑'으로
회복되는지(HR/OR>1, coef>0) 확인한다. 또한 반환 구조(coef/ci_low/ci_high/
pvalue 키)와 CI가 coef를 포함하는지, triangulate의 방향 일관성 플래그를
점검한다. 희소 이벤트 특성상 수렴 실패는 관용 처리(xfail/허용)한다.
"""

import numpy as np
import pandas as pd
import pytest

from src.stats.survival_models import (
    build_case_crossover,
    build_person_period,
    fit_case_crossover,
    fit_discrete_time_survival,
    fit_penalized_glmm,
    triangulate,
)

# 효과추정 결과 dict의 필수 키
REQUIRED_KEYS = {
    "design", "effect_name", "coef", "effect",
    "ci_low", "ci_high", "pvalue", "n_obs", "n_events", "converged", "note",
}


# ---------------------------------------------------------------------------
# 합성 데이터: ACWR↑ → onset 위험↑
# ---------------------------------------------------------------------------

@pytest.fixture()
def synthetic_panel_onset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """소형 합성 패널과 onset 라벨을 생성한다.

    40명 × 120일. 일별 hazard = cloglog^{-1}(-5 + 1.2*acwr)로 onset을
    표집하여 ACWR이 높을수록 onset 위험이 커지도록 설계한다. 각 선수의
    최초 onset만 사건으로 사용(이산시간 생존과 정합).
    """
    rng = np.random.default_rng(seed=20260530)
    n_athletes = 40
    n_days = 120
    start = pd.Timestamp("2021-01-01")

    panel_rows: list[dict] = []
    onset_rows: list[dict] = []

    for a in range(n_athletes):
        aid = f"A{a:02d}"
        # 선수별 평균 ACWR 수준에 약간의 이질성 부여
        base = rng.uniform(0.7, 1.2)
        injured = False
        for t in range(n_days):
            date = start + pd.Timedelta(days=t)
            acwr = float(np.clip(base + rng.normal(0, 0.4), 0.0, 4.0))
            # ACWR↑ → hazard↑ (cloglog 역링크)
            eta = -5.0 + 1.2 * acwr
            hazard = 1.0 - np.exp(-np.exp(eta))
            panel_rows.append({"athlete_id": aid, "date": date, "acwr": acwr})
            if not injured and rng.uniform() < hazard:
                onset_rows.append({"player_name": aid, "onset_date": date})
                injured = True

    panel = pd.DataFrame(panel_rows)
    onset = pd.DataFrame(onset_rows)
    # 최소 한 건 이상의 onset 보장(시드상 항상 성립하나 방어적)
    if len(onset) == 0:
        first = panel.iloc[10]
        onset = pd.DataFrame([{"player_name": first["athlete_id"],
                               "onset_date": first["date"]}])
    return panel, onset


# ---------------------------------------------------------------------------
# person-period / case-crossover 구성 검증
# ---------------------------------------------------------------------------

class TestPersonPeriod:
    """이산시간 위험집합 구성 테스트."""

    def test_onset_이후_검열됨(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        pp = build_person_period(panel, onset)
        # 각 선수의 event 합은 최대 1(최초 onset만)
        per_athlete = pp.groupby("athlete_id")["event"].sum()
        assert (per_athlete <= 1).all(), "선수별 이벤트가 1을 초과함(검열 실패)"
        # 이벤트가 적어도 하나 존재
        assert pp["event"].sum() >= 1

    def test_event일이_최초_onset과_일치(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        pp = build_person_period(panel, onset)
        ev_rows = pp[pp["event"] == 1]
        first_onset = onset.groupby("player_name")["onset_date"].min()
        for _, r in ev_rows.iterrows():
            assert pd.Timestamp(r["date"]) == pd.Timestamp(first_onset[r["athlete_id"]])


class TestCaseCrossoverBuild:
    """case-crossover strata 구성 테스트."""

    def test_각_strata에_case_1개(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        cc = build_case_crossover(panel, onset)
        if len(cc) == 0:
            pytest.skip("통제기간을 확보할 case가 없음(소형 합성)")
        case_per_set = cc.groupby("set_id")["case"].sum()
        assert (case_per_set == 1).all(), "strata당 case가 정확히 1개가 아님"


# ---------------------------------------------------------------------------
# (1) 이산시간 생존
# ---------------------------------------------------------------------------

class TestDiscreteTimeSurvival:
    """이산시간 생존(cloglog) 적합 테스트."""

    def test_반환_구조_및_CI_포함(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        res = fit_discrete_time_survival(panel, onset)
        assert REQUIRED_KEYS <= set(res.keys())
        assert res["effect_name"] == "HR"
        assert res["converged"], res["note"]
        # HR 척도 CI가 effect(HR)를 포함
        assert res["ci_low"] <= res["effect"] <= res["ci_high"]

    def test_효과_방향_위험증가(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        res = fit_discrete_time_survival(panel, onset)
        # 합성에서 ACWR↑ → 위험↑ 이므로 HR>1 (log-HR>0)
        assert res["coef"] > 0, f"log-HR가 양수가 아님: {res['coef']}"
        assert res["effect"] > 1.0


# ---------------------------------------------------------------------------
# (2) case-crossover
# ---------------------------------------------------------------------------

class TestCaseCrossover:
    """case-crossover 조건부 로지스틱 테스트."""

    def test_반환_구조(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        res = fit_case_crossover(panel, onset)
        assert REQUIRED_KEYS <= set(res.keys())
        assert res["effect_name"] == "OR"

    def test_효과_방향_위험증가_또는_관용(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        res = fit_case_crossover(panel, onset)
        if not res["converged"]:
            pytest.xfail(f"case-crossover 수렴/구성 실패(소형 합성 관용): {res['note']}")
        # CI가 OR을 포함
        assert res["ci_low"] <= res["effect"] <= res["ci_high"]
        # 방향: 위험↑ 기대(OR>1). 소형 표본 변동 가능성 있어 coef 부호로 관용 점검
        assert res["coef"] > 0 or res["pvalue"] > 0.05, (
            f"OR 방향이 위험↑가 아니고 유의함: coef={res['coef']}"
        )


# ---------------------------------------------------------------------------
# (3) 벌점 로지스틱
# ---------------------------------------------------------------------------

class TestPenalizedLogit:
    """벌점(L2) 로지스틱 테스트."""

    def test_반환_구조(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        res = fit_penalized_glmm(panel, onset, horizon=7)
        assert REQUIRED_KEYS <= set(res.keys())
        assert res["effect_name"] == "coef"

    def test_효과_방향_위험증가(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        res = fit_penalized_glmm(panel, onset, horizon=7)
        if not res["converged"]:
            pytest.xfail(f"벌점 로지스틱 수렴 실패(관용): {res['note']}")
        assert res["coef"] > 0, f"벌점 계수가 양수가 아님: {res['coef']}"

    def test_EPV_변수예산_초과_거부(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        # acwr + 공변량 4개 = 5개 → EPV<=4 위반으로 거부되어야 함
        res = fit_penalized_glmm(
            panel, onset, horizon=7,
            covariates=["c1", "c2", "c3", "c4"],
        )
        assert not res["converged"]
        assert "EPV" in res["note"]


# ---------------------------------------------------------------------------
# triangulate
# ---------------------------------------------------------------------------

class TestTriangulate:
    """삼각검증 방향 일관성 테스트."""

    def test_요약행_및_방향_플래그(self, synthetic_panel_onset):
        panel, onset = synthetic_panel_onset
        tri = triangulate(panel, onset, horizon=7)
        # 3개 설계 + 요약 1행
        assert len(tri) == 4
        assert "direction_up" in tri.columns
        summary = tri[tri["design"] == "consistency_summary"]
        assert len(summary) == 1
        # 합성은 위험↑로 생성되므로 적어도 적합된 설계는 위험↑ 방향
        valid = tri[tri["design"] != "consistency_summary"]["direction_up"].dropna()
        assert len(valid) >= 1
        assert valid.sum() >= 1, "어느 설계도 위험↑ 방향이 아님"
