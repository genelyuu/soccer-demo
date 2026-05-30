# 연구 프로토콜 — 훈련 부하 모니터링의 예측·인과·임상효용 분석

> **버전**: 1.0 | **작성**: 2026-05-30 | **언어 정책**: 한국어(ko-KR)
> **위치**: `docs/RESEARCH_PROTOCOL.md`
> **선행 산출물**: [`reports/POV_REPORT.md`](../reports/POV_REPORT.md) (연관성 분석 단계)
> **참고 문서**: [`docs/REFERENCES.md`](REFERENCES.md), [`docs/METRICS_FORMULAS.md`](METRICS_FORMULAS.md),
> [`docs/INJURY_PREDICTION_REFERENCES.md`](INJURY_PREDICTION_REFERENCES.md), [`docs/track_A/`](track_A/), [`docs/track_B/`](track_B/)
> **재현 환경**: Python 3.13.7, numpy 1.26.4(seed=42), pandas 2.3.1, statsmodels 0.14.5, scipy 1.16.1, scikit-learn 1.7.1
> **EDA 산출 스크립트**: [`scripts/eda_protocol.py`](../scripts/eda_protocol.py) (read-only, 본 문서의 모든 실측치 재현)

---

## 0. 연구의 위치와 격상 방향

기존 `POV_REPORT.md`는 **연관성/설명(explanatory)** 단계를 완료했다: 혼합효과모형으로 `HRV ~ power`, `Hooper ~ ACWR + Monotony`의 *방향과 효과크기*를 추정했다(예: Track B ACWR 계수 −0.089, ICC 0.45). 본 프로토콜은 이를 세 축으로 격상한다.

1. **예측(prediction)** — 사후 적합도(R²·AIC)가 아닌, *미래 부상을 선행 탐지*하는 전향적 성능을 시간 분리 검증·확률 보정과 함께 평가.
2. **인과(causal)** — 회귀계수가 아닌, DAG로 교란을 명시하고 case-crossover 등 *준실험 설계*로 개인 불변 교란을 통제.
3. **임상·운영 효용(utility)** — 통계적 유의성이 아닌, decision-curve로 "경고를 따랐을 때의 순이익"을 평가(FDS의 비용민감 운영과 동형).

> **정직성 원칙**: §C/§E에서 드러나듯 본 데이터의 부상 onset은 **43건**에 불과하다. 따라서 본 연구의 1차 가치는 *배포형 부상 예측기*가 아니라, **데이터 희소성·극단적 불균형 하에서의 엄밀한 방법론**이며, 이것이 FDS 도메인으로 직접 이전 가능한 핵심 역량이다.

---

## A. 데이터셋 설명 (Datasets)

> 주의: `docs/track_A/DATASETS.md`, `docs/track_B/DATASETS.md`는 **취득 전 후보 비교(스카우팅) 문서**이며 실제 확보 데이터와 규모가 다르다. 아래는 **실제 사용 데이터** 기준이다.

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
| 한계 | 부상 기록은 *상태 로깅*(중복일) → onset 정의 필요. 단일 종목·여성·2팀 → 일반화 제한 |

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
