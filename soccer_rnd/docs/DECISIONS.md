# 결정 기록 (Architecture Decision Records)

본 문서는 프로젝트의 핵심 결정을 ADR 형식으로 기록한다.

---

## ADR-001: 저장소 디렉토리 구조 재편

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 초기 저장소는 `track_A/`, `track_B/` 루트 디렉토리에 마크다운 문서만 존재하는 평면 구조였다. config.json에 정의된 프로젝트 범위(docs, src, tests, notebooks, reports, data)를 반영하기 위해 구조를 재편할 필요가 있었다.
- **결정**: config.json의 `workspace.directories` 정의에 따라 다음 구조로 재편한다.
  - `docs/track_A/`, `docs/track_B/`: 프로토콜·계획 문서
  - `src/metrics/`, `src/eda/`, `src/stats/`: Python 모듈
  - `tests/`: 단위 테스트
  - `notebooks/`: EDA·통계 노트북
  - `reports/figures/`: 보고서·그림
  - `data/raw/`, `data/processed/`: 데이터 (git 제외)
- **근거**: 산출물 추적성(traceability) 확보, 역할별 작업 영역 분리, config.json 표준과 일치
- **영향**: 기존 `track_A/`, `track_B/` 파일을 `docs/track_A/`, `docs/track_B/`로 이동 완료

---

## ADR-002: ACWR 두 변형(Rolling vs EWMA) 병행 비교

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: ACWR 산출 시 rolling average 방식과 EWMA 방식 중 하나를 선택하거나 둘 다 사용할 수 있다.
- **결정**: 두 변형 모두 구현하고 민감도 비교를 필수 분석으로 포함한다.
- **근거**: Williams et al. (2017)에서 EWMA가 부하 변화에 더 민감할 수 있음을 제시. 단일 방식 선택보다 비교를 통해 PoV의 설득력을 높인다.
- **영향**: `src/metrics/acwr.py`에 `acwr_rolling()`, `acwr_ewma()` 두 함수 모두 구현

---

## ADR-003: 언어 정책 — 한국어 우선

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 팀 정책으로 모든 문서·응답·주석·테스트 설명을 한국어로 작성한다.
- **결정**: 코드 식별자(변수명, 함수명), 라이브러리명, 파일명 등 불가피한 고유명사만 영문 허용. 나머지는 한국어.
- **근거**: config.json `teamPolicy.language: "ko-KR"` 정의

---

## ADR-004: 결측 처리 원칙

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 스포츠 데이터에서 결측(부상, 휴식일, 측정 누락 등)은 빈번하다.
- **결정**: 결측은 원칙적으로 NA로 유지한다. 분석 목적상 필요할 때만 명시적 규칙(예: 휴식일 load=0)으로 처리하며, 처리 근거를 본 문서에 기록한다.
- **근거**: 암묵적 보간/대체는 분석 편향을 초래할 수 있으므로, 명시적 규칙만 허용

---

## ADR-005: 트랙 A 데이터셋 — PhysioNet ACTES 선정

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 트랙 A는 RR 원자료 + 운동 부하를 동시에 제공하는 공개 데이터셋이 필요하다. 후보 3개(ACTES, Autonomic Aging, Ephnogram)를 비교 평가했다.
- **결정**: **PhysioNet ACTES**를 1순위로 선정한다.
- **근거**: beat-to-beat RR 간격과 운동 부하(power W, VO2)를 동일 세션에서 제공하는 유일한 공개 데이터셋. 38명 피험자, 훈련 전후 2회 측정. 다른 후보는 운동 부하 미제공(Autonomic Aging) 또는 RR 직접 미제공(Ephnogram).
- **영향**: `data/raw/track_A/` 에 ACTES 데이터 배치 예정. 상세 스키마 매핑은 `docs/DATA_SCHEMA_MAPPING.md` 참조.

---

## ADR-006: 트랙 B 데이터셋 — Carey et al. (Zenodo) 선정

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 트랙 B는 sRPE + Hooper 호환 웰니스 설문 + 선수ID + 날짜를 모두 갖춘 시즌형 데이터가 필요하다. 후보 3개(Carey/Zenodo, Rossi/Figshare, Nobari/Mendeley)를 비교 평가했다.
- **결정**: **Carey et al. (Zenodo, CC BY 4.0)**를 1순위로 선정한다.
- **근거**: sRPE + 웰니스 5항목(Hooper 호환) + 선수ID + 일별 날짜 4가지 필수 요소를 모두 충족하는 유일한 완전 공개 데이터셋. AFL(호주풋볼)이지만 부하-웰니스 시차 관계 분석에는 종목 무관하게 유효.
- **영향**: `data/raw/track_B/` 에 배치 예정. Hooper 항목 매핑은 `docs/DATA_SCHEMA_MAPPING.md` 참조.

---

## ADR-007: 합성 데모 데이터 전략

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 실제 데이터셋 다운로드/배치 전에 EDA·통계 파이프라인 검증이 필요하다.
- **결정**: 노트북에서 `np.random.seed(42)`를 사용한 합성 데모 데이터를 생성하여 전체 파이프라인이 재현 가능하게 실행되도록 한다. 실제 데이터 투입 시 합성 데이터 생성 셀만 교체하면 된다.
- **근거**: 데이터 유무와 무관하게 실행 가능한 파이프라인 구축(M3 종료 기준), 재현성 확보
- **영향**: notebooks/track_A_eda.ipynb, track_A_stats.ipynb, track_B_eda.ipynb, track_B_stats.ipynb에 합성 데이터 생성 셀 포함

---

## ADR-008: 트랙 B 통계 모형 — ACWR + Monotony 다중 예측변수

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 트랙 B에서 Hooper Index 예측 시, ACWR 단독 모형과 ACWR+Monotony 다중 모형 중 선택이 필요하다.
- **결정**: ACWR 단독 모형(M2)과 ACWR+Monotony 다중 모형(M3)을 모두 적합하여 비교한다. 또한 EWMA+Monotony 변형(M4)도 포함한다.
- **근거**: Foster (1998)에 따르면 Monotony는 부하 총량과 독립적으로 과훈련/상병 위험에 기여한다. ACWR만으로는 부하 패턴의 단조성을 포착할 수 없으므로, Monotony를 추가 예측변수로 포함하여 설명력 개선을 검증한다.
- **영향**: `notebooks/track_B_stats.ipynb`에 4개 모형 비교 구현

---

## ADR-009: 다중 시차(Multi-Lag) 분석 프레임워크 도입

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: 기존 분석은 lag-1(t → t+1) 단일 시차만 고려하였으나, 부하-반응 관계의 최적 시차가 lag-1이 아닐 수 있다.
- **결정**: lag-0부터 lag-7까지 체계적으로 탐색하는 다중 시차 분석 모듈을 구현한다. Pearson 상관 테이블과 혼합효과모형 비교를 lag별로 수행하고, AIC/BIC 기준으로 최적 lag을 결정한다.
- **근거**: 부하 유형(급성 vs 누적)과 반응 지표(HRV vs 웰니스 설문)에 따라 최적 시차가 다를 수 있다. 체계적 탐색을 통해 데이터 기반 시차 결정이 가능하다.
- **영향**: `src/stats/lag_analysis.py`에 4개 공개 함수 구현, 9개 테스트

---

## ADR-010: LOSO 교차 검증 도입

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: in-sample 적합도(AIC/BIC)만으로는 모형의 일반화 성능을 보장할 수 없다.
- **결정**: Leave-One-Subject-Out (LOSO) 교차 검증을 도입하여 out-of-sample 예측 성능을 평가한다. 고정효과만 활용한 예측으로 새 선수에 대한 일반화 가능성을 검증한다.
- **근거**: 스포츠 과학에서 개인차가 큰 특성상, 새로운 선수에 대한 예측력은 in-sample 적합도와 다를 수 있다. LOSO는 선수 수준의 독립성을 보장하는 가장 엄격한 교차 검증 방식이다.
- **영향**: `src/stats/cross_validation.py`에 4개 함수 구현, 10개 테스트

---

## ADR-011: 대안 부하 지표(DCWR, TSB, ACWR Uncoupled) 병행 비교

- **일자**: 2026-02-10
- **상태**: 채택
- **맥락**: Impellizzeri et al. (2020)과 Lolli et al. (2019)의 ACWR 비판을 반영하여, 비율 기반 지표의 한계를 보완하는 대안 지표가 필요하다.
- **결정**: DCWR(차이 기반), TSB(균형 기반), ACWR Uncoupled(비결합) 3가지 대안 지표를 구현하고, 기존 ACWR과 병행 비교한다. 레지스트리 패턴으로 확장 가능한 구조를 채택한다.
- **근거**: Wang et al. (2020)은 차이 기반 접근의 division-free 장점을, Lolli et al. (2019)은 비결합 방식의 허위 상관 제거 효과를 보고하였다.
- **영향**: `src/metrics/alternative_load.py`에 7개 함수 + 레지스트리 구현, 13개 테스트

---

## ADR-012: 통합 합성 데이터 가설 검증 실험

- **일자**: 2026-02-11
- **상태**: 채택
- **맥락**: Track A(HRV)와 Track B(부하+설문) 실제 데이터 분석에서 세 가지 핵심 발견이 도출되었다: (1) 개인화된 기저선 추적의 중요성, (2) 다중 지표 통합 모니터링 우위, (3) Monotony 독립 효과. 그러나 기존 트랙별 합성 데이터는 별개로 생성되어 통합 검증이 불가능했다.
- **결정**: 한 선수가 daily_load + HRV(rMSSD) + wellness(Hooper) 모두를 가지는 **통합 DGP**를 설계하고, 4개 가설(H1~H4)을 100회 Monte Carlo 포함 합성 실험으로 검증한다.
  - H1: OLS vs Mixed 비교 (Simpson's Paradox 재현)
  - H2: 부하 단독 vs 부하+HRV 통합 모형 비교
  - H3: 순차 투입으로 Monotony 억제변수 효과 재현
  - H4: MCAR/MAR/MNAR 결측 편향 민감도 분석
- **근거**: 실제 데이터의 발견이 DGP 구조적 속성에서 비롯되는지, 아니면 우연인지를 통제된 조건에서 확인해야 한다. 통합 데이터셋은 Track 간 교차 검증(HRV→Hooper 예측력)을 가능하게 한다.
- **파라미터 근거**:
  - `sigma_u_hooper=1.25` (Track B ICC≈0.48 역산)
  - `sigma_u_hrv=0.35` (Track A ICC≈0.14 역산)
  - `beta_acwr_hooper=-0.08`, `beta_mono_hooper=+0.14`, `beta_strain_hooper=-0.00007` (Track B M4 실제 계수)
  - `seed=2024` (기존 42와 독립)
- **영향**: `src/data/synthetic_integrated.py` DGP 모듈, `tests/test_synthetic_integrated.py` 18개 테스트, `notebooks/run_integrated_hypothesis.py` 실행 스크립트
