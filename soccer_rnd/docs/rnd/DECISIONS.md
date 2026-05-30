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

---

## ADR-013: 실험 운영 문서 체계 표준화

- **일자**: 2026-05-30
- **상태**: 채택
- **맥락**: `docs/track_A/`·`docs/track_B/` 문서 다수가 stub(86~185 bytes) 상태였고, 실험 운영을 위한 거버넌스·실행 런북·전체 파이프라인 요구사항 문서가 부재했다. 트랙 간 문서 구조·완성도도 불균형(Track A 15% vs Track B 75%)이었다.
- **결정**: 다음 문서 체계를 표준화한다.
  - **신규 운영 문서 3종** (docs/ 루트, `DRD_v*.md`·`RESEARCH_PROTOCOL.md`와 동일한 flat 컨벤션): `TRD_v1.0.md`(Stage 0~8 원자적 요구사항), `GOVERNANCE.md`(거버넌스·용어집·RACI·리스크·보고표준), `PLAYBOOK.md`(실행 런북)
  - **track 문서 공통 템플릿**: 6종(PROTOCOL/DATASETS/METRICS/EDA_PLAN/STATS_PLAN/EXPECTED_OUTPUTS) 상단 메타블록(문서 ID·버전·최종수정·상위문서) 통일, stub 7개를 실측 근거로 상세화
  - **버전 정책**: 기존 충실 문서는 in-place 보강 시 헤더 `버전: v2` + 하단 `## 변경 이력` 기록(별도 `_v2` 파일 미생성)
  - **mermaid 적극 활용**: 데이터흐름·게이트·의존성·인과 DAG 등. 한글/괄호/콜론 라벨은 `["..."]` 따옴표, 줄바꿈 `<br/>`
  - **지표 정의 단일 출처(SSOT)**: 수식 원전은 `METRICS_FORMULAS.md`, track METRICS.md는 교차참조 + Track 특이사항만 기술
- **근거**: 실험 재현성·추적성(품질 기준)과 부상예측 단계(Stage 8) 실행을 위해 우선순위·검증경로가 명시된 요구사항·운영 문서가 필요하다. `METRICS_FORMULAS.md`의 원자적 포맷과 `DRD_v3.0.md`의 버전 이력·다이어그램 관행을 차용한다.
- **영향**: `docs/TRD_v1.0.md`·`docs/GOVERNANCE.md`·`docs/PLAYBOOK.md` 신규, `docs/track_A/`·`docs/track_B/` 12문서 상세화/보강, `docs/README.md` 문서 지도·인덱스 추가


---

## ADR-014: 부상 onset 라벨 정의 및 동결 (Stage 8 / P0)

- **일자**: 2026-05-30
- **상태**: 채택 (분석 착수 전 동결 — 사후 변경 시 신규 ADR + 사유)
- **맥락**: Stage 8 부상예측은 원시 부상 기록(`injury.csv`, 부상-일 162행, 동일일 중복 포함, 선수 15명)을 독립 사건(onset)으로 환산해야 한다. 자가보고 부상은 동일 부상이 여러 날에 걸쳐 중복 기록되므로, 사건 단위 라벨 규칙을 사전에 고정하지 않으면 발생률·검정력 추정이 흔들린다.
- **결정**:
  - **onset 정의**: 동일 선수에서 직전 부상-일과의 간격(gap)이 **7일 이상**이면 새로운 독립 onset으로 센다(7일 미만 연속 부상-일은 하나의 에피소드). 첫 부상-일은 항상 onset.
  - **dedup**: 동일 (선수, 날짜) 중복 행은 1행으로 축약, 중증도는 'major' 우선 보존.
  - **선행 위험창 라벨**: athlete-day `t`에 대해 `onset_next_k` = [t+1, t+k] 구간 onset 발생 여부(k=1·3·7).
  - **변수 예산(EPV)**: 독립 onset 43건 → EPV 10 규칙상 **동시 투입 예측변수 ≤ 4개**. 풀 ML 단독 주모형 금지.
- **근거**: gap≥7 규칙 적용 시 **onset 43건·발생률 1.75/1000 athlete-days**가 산출되며, 이는 동일 SoccerMon 데이터를 분석한 외부 연구(arXiv 2601.19479)의 43건과 정확히 일치한다(외부 검증). 민감도: gap=3은 75건으로 결과가 라벨 정의에 민감함을 확인(RESEARCH_PROTOCOL §I-3) → gap 3/7 민감도 분석을 필수 보고.
- **영향**: `src/data/injury_label.py`(라벨 빌더), `src/stats/injury_eval.py`(공용 평가), `tests/test_injury_label.py`(onset=43 재현 게이트 7개 테스트), TRD REQ-P-01.


---

## ADR-015: 문서 거버넌스 재구성 — flat → 3축 nested (ADR-013 개정)

- **일자**: 2026-05-30
- **상태**: 채택 (ADR-013의 flat 컨벤션을 본 ADR로 개정)
- **맥락**: 루트 `docs/`에 연구 문서·요구사항·운영성 문서(마이그레이션·DB 장애)가 평면으로 섞여 17개 파일이 한 레벨에 누적됐다. ADR-013은 단순 flat 구조를 표준화했으나, 부상예측(Stage 8) 격상으로 문서가 늘며 성격별 길찾기가 어려워졌다. 한글 파일명 2건(`데이터명세서_v3.0.md`, `마이그레이션_진행보고서.md`)도 식별자 규칙과 어긋났다.
- **결정**: [DOC_GOVERNANCE_PROPOSAL.md](../DOC_GOVERNANCE_PROPOSAL.md)의 권장안대로 **3축**으로 재구성한다.
  - **`docs/rnd/`** = 연구·요구·통제·실행(RESEARCH_PROTOCOL·TRD·GOVERNANCE·PLAYBOOK·DECISIONS·INJURY_PREDICTION_REFERENCES), 하위 `requirements/`(DRD·DATA_SPEC)·`tracks/`(track_A·B).
  - **`docs/standards/`** = 공통 기준 SSOT(METRICS_FORMULAS·DATA_SCHEMA_MAPPING·REFERENCES).
  - **`ops/`**(최상위) = 운영성 문서(migration·incidents). R&D와 분리.
  - **파일명 규칙**: 기존 영문명 유지, 한글 2건만 영문화(`DATA_SPEC_v3.0.md`, `migration_progress_report.md`). 번호 프리픽스(`01_`) 미채택 — 읽는 순서는 `docs/README` 인덱스가 표현.
  - **링크 무결성 게이트**: 이동에 따른 마크다운 상대링크(약 125건)·코드 docstring(`src/*.py` 6건)·루트 `README.md`·`CLAUDE.md` 참조를 상대경로 재계산으로 일괄 재작성하고 "깨진 링크 0"을 완료 조건으로 둔다.
  - **허브 + per-folder README**: `docs/README`(허브) + `rnd`·`rnd/requirements`·`standards`·`ops` 로컬 인덱스 신설.
- **근거**: 성격(연구/기준/운영)별 분리로 탐색성·추적성을 높이고, SSOT(지표 수식은 `standards/`에서만 정의) 원칙을 구조로 강제한다. flat 대비 깊이가 늘지만 허브·로컬 README로 길찾기를 보장한다.
- **영향**: `docs/rnd/`·`docs/standards/`·`ops/` 신설, 16개 파일 이동(한글 2건 개명 포함) + 미커밋 신규 `INJURY_PREDICTION.md` 이동, 4개 README 신설/개편, `CLAUDE.md` 디렉토리 구조·`DECISIONS` 경로 갱신. 링크 체커 broken=0, `pytest` 영향 없음 확인.