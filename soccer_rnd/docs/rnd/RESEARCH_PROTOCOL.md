# 연구 프로토콜 — 훈련 부하 모니터링의 예측·인과·임상효용 분석

> **버전**: 1.0 | **작성**: 2026-05-30 | **언어 정책**: 한국어(ko-KR)
> **위치**: `docs/rnd/RESEARCH_PROTOCOL.md`
> **선행 산출물**: [`reports/POV_REPORT.md`](../../reports/POV_REPORT.md) (연관성 분석 단계)
> **참고 문서**: [`docs/standards/REFERENCES.md`](../standards/REFERENCES.md), [`docs/standards/METRICS_FORMULAS.md`](../standards/METRICS_FORMULAS.md),
> [`docs/rnd/INJURY_PREDICTION_REFERENCES.md`](INJURY_PREDICTION_REFERENCES.md), [`docs/rnd/tracks/track_A/`](../track_A), [`docs/rnd/tracks/track_B/`](../track_B)
> **재현 환경**: Python 3.13.7, numpy 1.26.4(seed=42), pandas 2.3.1, statsmodels 0.14.5, scipy 1.16.1, scikit-learn 1.7.1
> **EDA 산출 스크립트**: [`scripts/eda_protocol.py`](../../scripts/eda_protocol.py) (read-only, 본 문서의 모든 실측치 재현)

---

## 0. 연구의 위치와 격상 방향

기존 `POV_REPORT.md`는 **연관성/설명(explanatory)** 단계를 완료했다: 혼합효과모형으로 `HRV ~ power`, `Hooper ~ ACWR + Monotony`의 *방향과 효과크기*를 추정했다(예: Track B ACWR 계수 −0.089, ICC 0.45). 본 프로토콜은 이를 세 축으로 격상한다.

1. **예측(prediction)** — 사후 적합도(R²·AIC)가 아닌, *미래 부상을 선행 탐지*하는 전향적 성능을 시간 분리 검증·확률 보정과 함께 평가.
2. **인과(causal)** — 회귀계수가 아닌, DAG로 교란을 명시하고 case-crossover 등 *준실험 설계*로 개인 불변 교란을 통제.
3. **임상·운영 효용(utility)** — 통계적 유의성이 아닌, decision-curve로 "경고를 따랐을 때의 순이익"을 평가(FDS의 비용민감 운영과 동형).

> **정직성 원칙**: §C/§E에서 드러나듯 본 데이터의 부상 onset은 **43건**에 불과하다. 따라서 본 연구의 1차 가치는 *배포형 부상 예측기*가 아니라, **데이터 희소성·극단적 불균형 하에서의 엄밀한 방법론**이며, 이것이 FDS 도메인으로 직접 이전 가능한 핵심 역량이다.

---

## A. 데이터셋 설명 (Datasets)

> 주의: `docs/rnd/tracks/track_A/DATASETS.md`, `docs/rnd/tracks/track_B/DATASETS.md`는 **취득 전 후보 비교(스카우팅) 문서**이며 실제 확보 데이터와 규모가 다르다. 아래는 **실제 사용 데이터** 기준이다.

### A.1 Track A — PhysioNet ACTES (HRV 용량-반응)

| 항목 | 내용 |
|---|---|
| 정식명 | Autonomic Control of the cardiovascular system during Exercise (ACTES) |
| 출처 | PhysioNet (`physionet.org/content/actes/`) |
| 설계 | 점증 자전거 에르고미터 검사 중 beat-to-beat 측정 (단일 세션, 개인 내 용량-반응) |
| 실제 규모 | **피험자 18명**, beat-level 52,062행 |
| 인구 | 연령 12~18세(평균 15.2), 종목: fencing 10 · kayak 6 · triathlon 2 |
| 핵심 변수 | RR(ms), power(W), VO2, VT1/VT2 power |
| 분석 단위 | 피험자 × 파워구간(Rest/Low/Moderate/High) |
| **역할(보완 개념)** | **자율신경 회복 검증 앵커(objective autonomic anchor)** — "부하↑ → 미주신경(rMSSD)↓" 기전의 객관적 face validity를 제공. ⚠ *신체 과부하 축적*을 재는 "신체 트랙"이 **아니다**(급성 운동검사·타 종목·타 개인, HRV는 본질적으로 *회복/준비도* 마커) |
| 한계 | 종단(일별) 구조 아님 → "세션 내 부하-HRV 반응"으로 프레이밍. n=18은 군집수준 검정력 제한 |

### A.2 Track B — SoccerMon (부하-웰니스-부상 종단)

| 항목 | 내용 |
|---|---|
| 정식명 | SoccerMon (Midoglu et al., 2024) — 노르웨이 엘리트 여자 축구 2개 팀 |
| 출처 | Zenodo (CC BY 4.0) |
| 설계 | **전향적 코호트** — 일별 부하·웰니스·부상 로깅 |
| 실제 규모 | 활성 필터 후 **선수 44명**(TeamA/TeamB), **24,596 athlete-days**, 2020-01-09~2021-12-31(722일), 선수당 평균 559일 |
| 부하 | daily_load(=sRPE), ATL, CTL28/42, ACWR, Monotony, Strain, weekly_load (일별 사전산출) |
| 웰니스 | fatigue, stress, soreness, sleep_quality (+ mood/readiness/sleep_duration) → Hooper Index |
| **라벨** | injury 162 부상-일, illness 15건, game-performance 247건 |
| **역할(보완 개념)** | 통합 지표의 **본선 데이터** — 객관 부하 차원(D1)과 주관 회복 차원(D2)을 *모두* 포함. ⚠ **HRV는 없음**(웰니스의 readiness는 자가보고이지 HRV가 아님) |
| 한계 | 부상 기록은 *상태 로깅*(중복일) → onset 정의 필요. 단일 종목·여성·2팀 → 일반화 제한 |

---

## A′. 개념 모델 보완 — 과부하 차원 정의와 통합 경로

> **배경**: 초기 직관은 "Track A = 신체적(객관) 과부하, Track B = 정신적(주관) 과부하 → 통합하여 과훈련 임계치 예측"이었다. 그러나 데이터 구조 검토 결과 이 이분법은 성립하지 않으므로 아래와 같이 재정의한다.

### A′.1 왜 "A=신체/객관, B=정신/주관" 이분법이 성립하지 않는가

1. **두 데이터는 개인을 공유하지 않으며, Track B에는 HRV가 없다.** A(청소년 18명·급성 검사)와 B(엘리트 여자 축구 44명·2시즌)는 사람·시간구조·측정변수가 모두 다르다. 통합 지표를 *적용할* B에 HRV가 없으므로, A의 HRV 기전을 B 선수에게 직접 입힐 수 없다.
2. **두 개의 축이 혼동되어 있다.** ① 측정(객관 vs 주관)과 ② 영역(신체 vs 정신)은 별개다. HRV(객관)는 신체·심리 스트레스 *양쪽*에 반응하고, Hooper는 soreness·fatigue(신체) + stress·sleep(정신)이 *섞인* 지표다.
3. **Track B는 이미 객관·주관을 모두 포함한다.** ACWR/Monotony/Strain(객관적 신체 부하) + Hooper(주관적 회복)이 한 데이터에 공존한다.

### A′.2 재정의된 2차원 모델

```
            [ 개인화 과부하-회복 복합 지표 (Composite Readiness Index) ]
                                 │
        ┌────────────────────────┴────────────────────────┐
   D1. 외적/내적 신체 부하 (객관, Track B)      D2. 주관적 심리·회복 부하 (주관, Track B)
   · ACWR, Monotony, Strain, (GPS)             · stress·sleep·mood(정신) / soreness·fatigue(신체-주관)
                                 │
              [ 검증 앵커 ] Track A HRV 용량-반응 — 자율신경 차원의 생리적 타당성
                                 │
              [ 원위 검증 라벨 ] 부상 onset 43건 — 복합 지표가 실제 부상을 예측하는가
```

핵심 변경: **Track A를 별도 "신체 트랙"이 아니라 자율신경 차원의 객관적 검증 앵커로 강등**하고, 통합 지표는 *D1·D2를 모두 가진 Track B 위에서* 구성한다.

### A′.3 "과훈련 임계치"의 조작적 정의 (falsifiable)

과훈련 증후군(OTS)은 *배제 진단*(Meeusen et al., 2013)이며 SoccerMon에 라벨이 없다. 따라서 OTS를 직접 예측한다고 주장하지 않고 **복합 위험 상태**를 정의한다:

> **위험 상태** ≡ (신체 부하 이상: *개인화* ACWR z>+1.5 또는 Monotony z↑) AND/OR (주관 악화: *개인화* Hooper z 하락) → **원위 라벨 부상 onset(43건)으로 검증**.

검정 가능한 질문: *복합 지표가 단일 차원(부하만/주관만)보다 부상을 더 잘 예측하는가?* (RQ2 다영역 통합의 증분가치와 연결.)

### A′.4 통합 경로 — 세 가지 (엄밀성 순)

| 경로 | 방법 | 장점 | 한계 | 위상 |
|---|---|---|---|---|
| **R1. 단일 데이터 복합지표** | Track B 내부에서 D1+D2 복합 지표 구성·부상 검증. A는 HRV 가정의 *생리적 검증*에만 사용 | 배포 가능, 누수 없음, 사람·HRV 불일치 회피 | HRV를 지표에 직접 못 넣음 | **★ 주 경로** |
| **R2. 합성 통합(DGP)** | A·B 효과크기를 합성 코호트에 이식해 결합 지표 거동 연구(현 H1~H4 확장) | 참값 통제, 검정력·민감도 | 배포 불가 | 보조(검증) |
| **R3. 동일선수 HRV+부하+부상 취득** | HRV·부하·웰니스·부상이 같은 선수에게 있는 데이터로 진정한 객관+주관 개인 통합 | 진정한 통합 가능 | **공개 데이터 부재**(§A′.5) | 향후 과제 |

> **경로 확정 (2026-05-30): R1 본선 → R2 보조 → R3 향후과제** 순으로 진행한다.
> 즉 (i) Track B 단일 데이터 복합지표를 본선으로 구축·부상 검증(R1), (ii) 합성 DGP로 결합 지표 거동·검정력을 보조 검증(R2), (iii) 동일선수 HRV 통합은 데이터 취득 프로젝트로 분리(R3).

### A′.5 R3 관련 데이터셋 리서치 결과 (광범위 listup)

> **결론: 동일 선수에 *클린 RR/HRV + 일별 부하 + 웰니스 + 부상*이 모두 있는 완전 공개 데이터셋은 현재 존재하지 않는다**(다수 검색에서 명시 확인). "클린하지 않아도 활용 가능한" 후보까지 범위를 넓혀 아래 4계층으로 정리한다.
> **핵심 경고**: 그물을 넓히면 Kaggle의 "athlete recovery/injury" 데이터가 다수 검색되나 **상당수가 합성·시뮬레이션**으로, 본 프로젝트의 *실데이터* 가치를 훼손한다 → 주 검증 부적합(Tier D).

**Tier A — 실데이터·동일 생태계·가공 시 사용 가능 (R3 현실 출발점)**

| 자원 | 구성 | HRV | 부상 | 공개 | 비고 |
|---|---|---|---|---|---|
| **PMData** (Thambawita 2020) | **PMSys**(SoccerMon과 동일: sRPE·웰니스) + Fitbit Versa 2 + Forms, 16명·5개월 | △ Fitbit 일일 HR/수면(클린 RR 아님) | △ Forms 일부 | ✅ OSF/Simula/Kaggle | **최우선 R3 후보** — 비클린 HRV 허용 시 즉시 결합 가능 |

**Tier B — 실데이터·원신호(PPG/ECG)→HRV 파생 (부하·부상 없음 → HRV 특징 파이프라인 구축·검증용)**

| 자원 | 구성 | 용도 |
|---|---|---|
| Comprehensive PPG-based HR/HRV dataset (arXiv 2505.18165) | PPG 원신호 | RR/HRV 파생·검증 |
| Multi-site PPG in-the-wild (arXiv 2605.17859) | 다부위 PPG | 실세계 HRV 강건성 |
| PhysioNet **Wearable Device Dataset (Stress+Exercise)** (Sci Data 2025) | 스트레스·구조화 운동 중 웨어러블 | 운동 중 HRV |
| PhysioNet CogWear / WESAD / PPG-DaLiA | PPG/BVP·EDA | HRV 파이프라인 sanity-check |
| MMASH (PhysioNet) | beat-to-beat HR/HRV·수면·코르티솔, 24h | 단기 HRV 검증 |

**Tier C — 실데이터·HRV+수면(부하·부상 없음)**

| 자원 | 구성 | 용도 |
|---|---|---|
| 웨어러블 HRV + 수면일지 연속 데이터셋 (2024/25) | 실세계 HRV+수면 | HRV-수면 결합 검증 |
| ScopeSense (2023) | 8.5개월 라이프로깅(웨어러블+자가보고) | 종단 결합 패턴 |

**Tier D — ⚠ Kaggle "athlete" 데이터 (출처 검증 필수, 다수 합성 추정 → 주 검증 부적합)**

| 자원 | 표면 구성 | 주의 |
|---|---|---|
| Athlete Training & Recovery Tracker (prince7489) | 훈련·회복·HRV | 합성 가능성, provenance 불명 |
| Athlete Injury and Performance (ziya07) | 부상·수행·일정 | 합성/시뮬 추정 |
| FitLife / Fitness Tracker 류 | 트래커 요약 | 생성형 데이터 다수 |

**Tier T — 방법론·변수 설계 템플릿 (데이터 비공개)**: Sanchez et al. (2025, 12주 부하+HRV+피로+수면+부상) ·  Flatt & Esco (2015, 여자 축구 HRV) · AFL 2년 부하+HRV (2024).

**함의 및 R3 실현 경로**:
1. **현실 출발점 = PMData(Tier A)** — 비클린 HRV(Fitbit)를 수용하고 동일 PMSys 생태계의 sRPE·웰니스와 결합. 단 부상 라벨이 약해 *준-R3*(객관+주관 통합 *기전* 검증)에 그침.
2. **HRV 특징 파이프라인은 Tier B로 사전 구축·검증** 후 PMData/신규데이터에 이식.
3. **완전 R3 = 전향적 신규 수집** (PMSys+웨어러블 HRV+의무기록 부상)이 필요하며, Tier T(특히 Sanchez 2025)를 변수·설계 템플릿으로 인용.
4. **Tier D는 사용 금지(또는 provenance 검증 후 보조 시연 한정)** — 합성 데이터로 "실데이터 통합"을 주장하면 신뢰성 붕괴.

### A′.6 필수 보강 (설계 제약)

1. **개인화 임계치(필수)**: H1(ICC 0.45, Simpson's Paradox) 근거 — 모든 임계치는 *개인 기저선 대비 z-score*. 팀 고정 컷오프 금지.
2. **휴식 권고는 예측이 아니라 결정**: 비용(훈련 손실)·편익(부상 회피) 비대칭 → **decision-curve(net benefit)**로 임계치 설정·검증(정확도 아님).
3. **구성 타당도 검정**: "정신 과부하"가 별개 잠재요인인지 **요인분석(EFA/CFA)**으로 검정. Hooper는 단일 과훈련 지표로 설계되어 신체·정신이 분리 안 될 가능성 — 분리 실패 시 "정신 차원" 주장 철회.
4. **인과·피드백 주의**: HRV·soreness는 매개변수이자 권고 대상. 휴식 권고는 미래 부하를 바꿈(개입 간섭) → "현 정책 하 예측"으로 한정, 개입효과는 별도 인과/RL 프레임(범위 외).
5. **결측 32%(MNAR)**: 컨디션 나쁠 때 미보고 시 "주관 차원"이 체계적으로 과소추정 → H4(RQ4) 프레임으로 정량화.

---

## B. 데이터 명세 (Data Dictionary — EDA 실측 기반)

### B.1 Track B 분석 패널 (`data/processed/track_B_merged.csv`, n=24,596)

| 변수 | 유형 | 평균±SD | 중앙값 | 범위 | 결측 | 비고 |
|---|---|---|---|---|---|---|
| daily_load | 연속 | 284.9±323.3 | 180 | 0~3420 | 0% | sRPE, 0=비활성일 |
| acwr | 연속 | 0.98±0.76 | 0.97 | 0~**4.00** | 0% | 상한 4.0에서 **캡핑**(coupling 보정) |
| atl | 연속 | 281.7±181.3 | 305.7 | 0~965.7 | 0% | 7일 급성부하 |
| monotony | 연속 | 1.05±0.69 | 1.09 | 0~8.75 | 0% | |
| strain | 연속 | 2787±2552 | 2401 | 0~34475 | 0% | 우편향 심함 → 로그변환 권장 |
| fatigue | 순서형(1~5) | 3.03±0.63 | 3 | 1~5 | **32.4%** | Hooper 구성 |
| stress | 순서형(1~5) | 3.21±0.63 | 3 | 1~5 | **32.4%** | |
| soreness | 순서형(1~5) | 2.80±0.74 | 3 | 1~5 | **32.4%** | DOMS 대리 |
| sleep_quality | 순서형(1~5) | 3.27±0.72 | 3 | 1~5 | **32.4%** | |
| hooper_index | 연속(합산) | 10.70±1.77 | 10.5 | 4.5~17.5 | **32.5%** | 4개 항목 합 |

- **활성일(daily_load>0) 비율 56.8%** → 0-부하일(휴식/비훈련)이 43%. 부하 0인 날의 ACWR/Monotony 해석 주의.
- **웰니스 결측 ≈32%는 무작위가 아닐 가능성**(부상·경기 직후 미보고) → MNAR 가설(RQ4)의 직접 동기.
- 부하 지표 결측 0%는 원자료가 *사전 산출·전진충전(forward-fill)*되었을 가능성 → 결측 메커니즘이 부하·웰니스에서 상이함을 ADR로 기록.

### B.2 부상 라벨 (`injury.csv` → onset 파생)

| 항목 | 실측 |
|---|---|
| 원자료 부상-일 | 162 (상태 로깅, 중복일 포함) |
| 부상 보유 선수 | **15 / 44** (29명은 무부상 — 이벤트가 소수에 집중) |
| 중증도 | minor 133 · major 29 |
| 부위 상위 | right_foot 45 · left_knee 44 · right_thigh 21 · left_thigh 18 · right_knee 11 · groin_hip 10 |
| **onset(gap≥3일)** | **75건** |
| **onset(gap≥7일)** | **43건** |
| 발생률 | **1.75 onset / 1000 athlete-days** (gap≥7) |
| illness | 15건 / 4명 → **검정력 부족, 주 분석 제외** |

### B.3 Track A (`subject-info.csv`, `test_measure.csv`, `track_A_hrv_by_zone.csv`)

| 변수 | 실측 |
|---|---|
| RR(ms) 범위 | 252~**30500** → 상한값은 생리적 불가능 = **아티팩트**, RR 클리닝 전처리 전제(POV에서 수행) |
| power(W) | 0~335 |
| VT1 / VT2 | 평균 113W / 187W |

---

## C. EDA 결과 (탐색적 분석)

### C.1 부하 분포와 위험구간 (Track B)

- **ACWR**: sweet spot(0.8~1.3) 48.4%, **위험구간(>1.5) 11.5%**. 상한 4.0 캡핑으로 극단 분포가 절단됨.
- **Monotony>2.0(Foster 위험역치) 6.4%** — 드물지만 존재.
- strain은 극심한 우편향(최대 34,475, 평균 2,787) → 모형 투입 전 로그변환 필수.

### C.2 부상 onset의 시간 구조와 불균형 (★ 핵심)

향후 k일 내 onset 발생을 양성으로 정의한 athlete-day 라벨:

| 예측 윈도우 k | 양성 수 | 유병률 | 불균형비 |
|---|---|---|---|
| k=1일 | 37 | 0.15% | **1:664** |
| k=3일 | 110 | 0.45% | **1:223** |
| k=7일 | 254 | 1.03% | **1:96** |

- 이 분포는 **FDS 사기 탐지(통상 0.1~1%대)와 동일한 난이도**이며, ROC-AUC가 아닌 **PR-AUC·recall@고정정밀도**가 적절함을 직접 정당화한다.
- 단, 양성 athlete-day는 자기상관(같은 onset 주변 일수) → *독립 onset 이벤트 43건*이 실질 정보량이다.

### C.3 HRV 용량-반응 (Track A)

| 파워구간 | 평균 power(W) | rMSSD(ms) | ln_rMSSD |
|---|---|---|---|
| Rest | 0 | 7.60±2.39 | 1.98 |
| Low | 75 | 6.73±2.27 | 1.85 |
| Moderate | 155 | 5.22±1.97 | 1.60 |
| High | 212 | 4.59±1.55 | 1.48 |

→ 파워 증가에 따른 단조 감소가 명확(POV의 혼합효과 계수 −0.016과 일치). 본 트랙은 라벨 분석이 아니라 *생리적 타당성 앵커(face validity)* 역할.

---

## D. 연구질문 · 사전등록 가설

| ID | 연구질문 | 설계 | PASS 기준(사전 정의) | 기존 자산 |
|---|---|---|---|---|
| RQ1 | 부하 이상(ACWR↑·Monotony↑·ΔACWR)이 [t+1,t+k] 부상 onset을 선행 예측하는가 | 이산시간 생존(frailty) + case-crossover | PR-AUC > 기저율×2, 시간분리 검증 유지 | H3 |
| RQ2 | 웰니스(Hooper/구성 7종)가 부하를 넘어 증분 예측력을 갖는가 | 중첩모형(벌점화) | ΔAIC>10 **AND** NRI/IDI>0 | H2 |
| RQ3 | 개인 기저선 보정(랜덤효과/개인 z-score)이 탐지를 개선하는가 | RI/RS·개인표준화 | 보정 모형 PR-AUC 우위 + calibration 개선 | H1 |
| RQ4 | 결측(부상 시 미보고=MNAR)이 추정을 편향시키는가 | Monte Carlo 결측 시뮬 | MNAR 편향률·coverage 정량 보고(투명성) | H4 |

---

## E. 통계·인과 설계 (검정력 제약 반영)

### E.1 검정력 현실 — 설계를 지배하는 제약

- **독립 onset 43건**. EPV(events-per-variable) 10 규칙상 **동시 투입 예측변수 ≤ 4개**.
- 따라서 **풀 ML(GBM 등)은 단독 주모형으로 부적합**(과적합). ML은 *민감도/탐색* 보조로만.
- 주 추론은 **희소이벤트에 강건한 설계**: 벌점 회귀(Firth/ridge), case-crossover(케이스만 사용 → 효율적), 이산시간 생존.

### E.2 인과 구조(DAG)와 과조정 회피

`부하(load) → 피로(fatigue/HRV) → 부상`. 교란: 연령·포지션·이전부상력·일정밀집·계절.
**피로는 매개변수**이므로 ACWR→부상 총효과 추정 시 *조정하면 과조정 편향*. 매개분석은 별도 모형으로 분리.

### E.3 설계 삼각검증 (단일 모형 의존 금지)

| 설계 | 강점 | 통제 편향 |
|---|---|---|
| 이산시간 생존(cloglog)+frailty | 위험집합·중도절단 정합 | 시간의존 위험, 반복이벤트 |
| **Case-crossover / SCCS** | 개인이 자기 대조, 희소이벤트 효율 | 시간불변 교란 완전 제거 |
| 벌점 GLMM(지연 공변량) | 해석 용이, 기존 코드 연속 | 군집 상관, 분리(separation) |
| GBM + SHAP | 비선형·상호작용, XAI | (예측 상한 탐색, 보조) |

### E.4 노출 윈도우

exposure window·lag·induction period 분리 정의(k=1·3·7; 시점 vs 누적). "전일 ACWR"이 아닌 *위험기간* 개념.

---

## F. 검증 프로토콜

- **이중 누수 차단**: 중첩 LOSO(선수 분리) **+** 시간 분리(2020 학습 → 2021 검정).
- **외적 타당도**: Leave-Team-Out (TeamA→TeamB) 도메인 이동 평가.
- **확률 보정**: Brier score, calibration curve, isotonic 재보정.
- **임상 효용**: decision-curve(net benefit) — "Gabbett 룰만" vs "모형" 순이익 비교.
- **불균형 운영**: class weight/focal loss, threshold는 PR 곡선에서 선택, lead-time(경고~부상 간격) 분포 보고.
- **보고 표준**: 예측모형 **TRIPOD**, 관찰연구 **STROBE** 체크리스트 준수.

---

## G. FDS Modeler 직무 매핑

| 본 연구 | FDS 대응 | 공유 기법 |
|---|---|---|
| 부상 0.15~1% 희소 라벨 | 사기 거래 희소성 | PR-AUC, recall@precision |
| ACWR 임계 운영점 | 의심거래 임계 | 비용민감 threshold, decision-curve |
| 시즌 전환 분포이동 | concept drift | 시간분리 검증, 재보정 |
| 부상 중 보고중단(MNAR 32%) | 누락/회피 거래 | 결측 메커니즘 편향 정량화(H4) |
| SHAP 부상기여 분해 | 의심사유 설명 | XAI, 규제 대응 |

---

## H. 진행사항 구성 (로드맵 · 합격 게이트)

| Phase | 내용 | 산출물 | 합격 게이트 | 리스크 |
|---|---|---|---|---|
| **P0 거버넌스·라벨** | onset(gap≥7)/중증도/위험집합 정의, 데이터 라이선스 명시 | `ADR-injury-label.md`, 라벨 빌더+단위테스트 | onset 수·발생률 재현(=43, 1.75/1000), seed 고정 | 라벨 노이즈, 자가보고 편향 |
| **P1 기술역학 EDA** | 발생률, 부위/중증도, 노출-결과 시간정렬, 결측 패턴 | 기술통계표, KM 곡선, 결측 히트맵 | STROBE 흐름도 완비 | 0-부하일/활성시즌 처리 |
| **P2 기준선** | Gabbett sweet-spot 룰을 *벤치마크*로 박제 | 룰 baseline PR-AUC | 후속 모형은 이 기준 초과 의무 | 기준 과소설정 |
| **P3 주 추론** | 이산시간 생존+frailty, case-crossover 병행(벌점화) | 효과추정+95%CI, 설계 간 일치성 | 설계 3종 방향 일관 + 민감도 통과 | 과조정/분리/검정력 |
| **P4 예측+XAI** | 벌점 회귀 주모형, GBM+SHAP 보조, 보정, decision-curve | TRIPOD 표, calibration·DCA 그림 | 시간분리 검정서 net benefit>룰 | 누수, 과적합 |
| **P5 강건성** | MNAR 편향(H4 재사용), 윈도우 민감도, Leave-Team-Out | 민감도 부록, 외적타당도표 | 결론의 가정 강건성 입증 | 표본 한계 |
| **P6 재현·전달** | 재현 패키지, Streamlit(선수별 위험+실제 부상 마커), 면접용 1-pager | 데모 URL, TRIPOD 체크리스트 | 동일입력→동일결과 | 노트북 용량 |

---

## I. 한계 (Limitations) — 정직한 자기비판

1. **표본·검정력**: 독립 onset 43건, 부상 보유 15/44명 → 예측변수 ≤4개, 결론은 *방법론 시연*이며 임상 배포 주장 불가.
2. **단일 데이터셋·일반화**: 단일 종목(여자 축구) 2팀 → 성별·종목·수준 일반화 제한.
3. **라벨 노이즈**: 자가보고 부상, onset의 gap 임계(3 vs 7일)에 결과 민감 → 민감도 분석 필수.
4. **결측**: 웰니스 32% 결측이 MNAR이면 웰니스 효과 추정이 편향될 수 있음(RQ4로 정량화하되 완전 보정은 불가).
5. **지표 아티팩트**: ACWR 4.0 캡핑, RR 30,500ms 등 전처리 의존성 → 전처리 규칙을 ADR로 고정.

---

*본 프로토콜은 사전등록 성격이며, 분석 착수 전 P0(라벨 정의 ADR) 확정을 전제로 한다.*
