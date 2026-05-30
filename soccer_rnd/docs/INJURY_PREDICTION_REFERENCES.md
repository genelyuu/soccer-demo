# 부상 예측 — Reference 데이터셋 및 문헌 조사

> **작성**: 2026-05-30 | **언어 정책**: 한국어(ko-KR)
> **목적**: [`docs/RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md)의 부상 예측 재설계를 뒷받침하는 **공개 데이터셋**과 **핵심 문헌**을 정리한다.
> **범위 구분**: 부하/HRV/웰니스 *지표*의 학술 근거는 [`docs/REFERENCES.md`](REFERENCES.md)에 있다. 본 문서는 **부상 예측(injury prediction)** 도메인 전용이다.

---

## 0. 요약 — 가장 중요한 발견

> **본 프로젝트의 Track B(SoccerMon)를 이용한 부상 예측 연구가 이미 학계에 존재한다.** 특히 한 연구는 **동일 데이터에서 부상 43건**을 보고하는데, 이는 본 프로젝트가 독립적으로 계산한 onset 이벤트 수(gap≥7일 기준 **43건**, `scripts/eda_protocol.py`)와 **정확히 일치**한다 → 본 프로젝트의 라벨 정의가 외부 검증된 셈이다. 동시에 그들이 사용한 **생존모형·LOPO 검증·SHAP**은 본 프로토콜 §E~F의 설계 선택과 동일하며, 그들의 성능(**C-index 0.762**)은 본 연구의 벤치마크가 된다.

---

## 1. 공개 부상 예측 데이터셋 (Public Datasets)

| # | 데이터셋 | 종목 | 규모 | 부상 라벨 | 부하/웰니스 변수 | 라이선스/접근 | 본 프로젝트 활용 |
|---|---|---|---|---|---|---|---|
| D1 | **SoccerMon** (Midoglu et al., 2024) | 여자 축구(노르웨이 2팀) | 선수~50명, 2시즌(2020–21), 주관보고 33,849건·객관 10,075건, GPS 60억+ 측정 | injury/illness 로깅(의료진 검증) | sRPE, ATL/CTL28/42, ACWR, Monotony, Strain, 웰니스 6종, GPS | **CC BY 4.0**, Zenodo DOI `10.5281/zenodo.10033832` | **본 Track B 원자료** |
| D2 | **Competitive Runners Injury** (Lövdal et al., 2021) | 중·장거리 육상 | 선수 74명, **7년**(2012–19) 훈련일지 | 부상 기록(일별) | GPS(거리·시간)+주관(노력·성공) 일/주 집계, 70+ 변수 | **공개** — DataverseNL DOI `10.34894/UWU9PV` / Kaggle | **외적 타당도 후보(P5)** — 종목 전이 검증 |
| D3 | **GPS Wearables Injury** (Sensors, 2023) | 축구 | 단일 시즌, GPS 웨어러블 | 부상 이벤트 | GPS 외부부하 다수 | 논문 부록(접근성 변동) | 외부부하 특징 설계 참고 |
| D4 | **Iranian Pro Football GPS** (Frontiers, 2025) | 남자 축구(이란) | 프로 시즌 | 부상 | GPS 기반 부하 | 논문 기반 | ML 특징·검증 비교 |
| D5 | **josedv82/public_sport_science_datasets** | (메타) | 다종목 모음 | 일부 포함(D2 등) | 다양 | GitHub 공개 | 추가 데이터 탐색 허브 |
| D6 | **MMASH** (PhysioNet) | 건강 성인 22명 | 24h | (부상 없음) | beat-to-beat HR/HRV, 수면, 코르티솔 | PhysioNet 공개 | **Track A HRV 파이프라인 검증** |
| — | Rossi et al. (2018) 이탈리아 클럽 | 남자 축구 | 1시즌 | 부상 | GPS | **비공개**(클럽 익명, 재배포 불가) | 재현 불가 — 방법론만 참고 |

**핵심 시사**: 즉시 재현 가능한 *완전 공개* 부상+부하 데이터셋은 사실상 **D1(SoccerMon, 본 데이터)**과 **D2(Lövdal 육상)** 두 개다. 따라서 본 프로젝트의 강력한 확장은 **D1로 주 분석 → D2로 종목 전이(외적 타당도) 검증**이다.

### 1.1 다모달(HRV + 부하 + 웰니스 + 부상) 통합 데이터 — R3 경로 후보

> [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) §A′의 **R3 경로**(동일 선수에 객관 HRV와 주관 회복을 모두 갖춘 통합)를 위한 데이터 탐색 결과.
> **결론: 동일 선수에 클린 RR/HRV + 일별 부하 + 웰니스 + 부상이 모두 있는 완전 공개 데이터셋은 현재 부재한다.** 가장 근접한 자원·템플릿:

| # | 자원 | 구성 | HRV | 부상 | 공개 | 비고 |
|---|---|---|---|---|---|---|
| R3-1 | **PMData** (Thambawita et al., 2020) | PMSys(SoccerMon과 동일 로깅)+Fitbit Versa 2+Google Forms, 16명·5개월 | △(Fitbit) | ✗ | ✅ OSF/Simula | **최근접** — 동일 생태계 |
| R3-2 | **ScopeSense** (2023) | 8.5개월 스포츠·영양·라이프스타일 라이프로깅 | △ | ✗ | ✅ | 라이프로깅 |
| R3-3 | 웨어러블 HRV + 수면일지 연속 데이터셋 (2024/25) | 실세계 HRV + 수면 | ○ | ✗ | ✅(부분) | 부하·부상 없음 |
| R3-4 | **Sanchez et al. (2025)** | 12주, 외·내적 부하 + HRV + 지각피로 + 수면 + **부상** | ○ | ○ | ✗ | **R3 설계 템플릿**(비공개) |
| R3-5 | Flatt & Esco (2015) | 여자 축구 9명, 스마트폰 HRV + 부하, 3주 | ○ | ✗ | ✗ | 소표본 |
| R3-6 | AFL 2년 내·외적 부하 + HRV (2024) | 호주풋볼 2시즌 | ○ | △ | ✗ | 종단 길지만 비공개 |

**함의**: R3은 데이터 *공백*이 본질 → R1(SoccerMon 단일 데이터 복합지표)을 본선으로, R3은 **PMData식 조합 또는 전향적 신규 수집**을 전제한 데이터 취득 프로젝트로 분리한다.

**광범위 탐색 보강(클린하지 않아도 활용 가능 후보)** — 상세 4계층 분류는 [`RESEARCH_PROTOCOL.md`](RESEARCH_PROTOCOL.md) §A′.5 참조:
- **Tier B(원신호→HRV 파생, 파이프라인 검증용)**: Comprehensive PPG HR/HRV(arXiv 2505.18165), Multi-site PPG in-the-wild(arXiv 2605.17859), PhysioNet *Wearable Device Dataset: Stress+Exercise*(Sci Data 2025), CogWear/WESAD/PPG-DaLiA.
- **Tier D(⚠ Kaggle "athlete" 데이터)**: Athlete Training & Recovery Tracker, Athlete Injury and Performance 등 — **다수 합성·시뮬레이션 추정 → 출처 검증 전 사용 금지**, 합성 데이터로 "실데이터 통합" 주장 시 신뢰성 붕괴.
- **경로 확정(2026-05-30)**: R1 본선 → R2 보조 → R3 향후과제.

---

## 2. 핵심 문헌 (Key Literature)

### 2.1 SoccerMon 직접 활용 연구 (본 데이터 동일)

| # | 저자/제목 | 출처 | 핵심 내용 | 본 프로젝트 함의 |
|---|---|---|---|---|
| L1 | Midoglu, C. et al. — *A large-scale multivariate soccer athlete health, performance, and position monitoring dataset* | *Nature Scientific Data* (2024), `s41597-024-03386-x` | SoccerMon 데이터셋 공식 기술 논문(데이터 사전·수집 프로토콜 PmSys/STATSports) | **데이터 인용·명세의 1차 출처** |
| L2 | *Time-to-Injury Forecasting in Elite Female Football: A DeepHit Survival Approach* | arXiv `2601.19479` (2026, preprint) | SoccerMon 37명·**부상 43건**(급성24/과사용19)·4,449 player-days. DeepHit 생존모형, **연대기 분할+LOPO**, **C-index 0.762**, SHAP. baseline RF F1=0.533/XGB F1=0.429 | **라벨(43) 외부검증 + 생존설계·LOPO·SHAP·C-index 벤치마크 직결** |
| L3 | *SoccerGuard: Investigating Injury Risk Factors for Professional Soccer Players with ML* | arXiv `2411.08901` (2024, preprint) | SoccerMon 기반 부상위험 ML 프레임워크(주관·GPS·서드파티·의료검증 통합) | 특징공학·파이프라인 구조 참고 |

### 2.2 ML 부상 예측 실증 연구

| # | 저자 | 연도 | 제목/출처 | 비고 |
|---|---|---|---|---|
| L4 | Rossi, A., Pappalardo, L., Cintia, P. et al. | 2018 | Effective injury forecasting in soccer with GPS training data and machine learning. *PLOS ONE* 13:e0201264 | 의사결정나무, 민감도~80%/정밀도~50%. **데이터 비공개** |
| L5 | Lövdal, S.S., den Hartigh, R.J.R., Azzopardi, G. | 2021 | Injury Prediction in Competitive Runners With Machine Learning. *IJSPP* 16(10):1522–1531 | D2 데이터의 원논문, 시계열 특징·3주 윈도우 |
| L6 | (Sensors) | 2023 | Predicting Injuries in Football Based on GPS-Based Wearable Sensors. *Sensors* 23(3):1227 | GPS 외부부하 중심 |

### 2.3 방법론·비판 문헌 (★ 본 연구의 겸손한 프레이밍 근거)

| # | 저자 | 연도 | 제목/출처 | 본 프로젝트 함의 |
|---|---|---|---|---|
| L7 | Bahr, R. | 2016 | Why screening tests to predict injury do not work—and probably never will… *BJSM* 50(13):776–780 | "현재 적정 성능의 부상 예측 스크리닝 검사는 없다" → **배포형 예측기가 아닌 방법론 시연으로 프레이밍**(§0 정직성 원칙) |
| L8 | Bittencourt, N.F.N., Meeuwisse, W.H. et al. | 2016 | Complex systems approach for sports injuries… *BJSM* 50(21):1309–1314 | 환원주의적 단일 위험인자 회귀의 한계 → **다지표 통합(RQ2)·상호작용·복잡계 관점** 정당화 |
| L9 | Van Eetvelde, H. et al. | 2021 | Machine learning methods in sport injury prediction and prevention: a systematic review. *J Exp Orthop* `10.1186/s40634-021-00346-x` | ML 부상예측 체계적 리뷰 — 표준화 부재 지적 |
| L10 | (Scoping review) | 2024–25 | Machine learning approaches to injury risk prediction in sport: a scoping review with evidence synthesis. *PMC12013557* | 전처리·특징선택·평가 비일관성 → **TRIPOD 준수·사전등록**(§F) 근거 |

### 2.4 ACWR–부상 위험 (교차 참조)

ACWR과 부상 위험의 핵심 문헌(Hulin 2014, Blanch & Gabbett 2016, Gabbett 2016, Williams 2017, Murray 2017)과 그 비판(Lolli 2019, Impellizzeri 2020, Wang 2020, Carey 2018 — discretization)은 [`docs/REFERENCES.md`](REFERENCES.md) §2에 정리되어 있다. **요지**: ACWR은 수학적 커플링·이산화 편향 비판이 있으므로, 본 연구는 ACWR을 *단독 정답*이 아닌 *벤치마크 룰(P2)*로 다루고 다지표·연속 모형과 비교한다.

---

## 3. 본 프로젝트 적용 함의 (Synthesis)

1. **라벨 정의 검증됨** — 독립 연구(L2)가 동일 SoccerMon에서 부상 43건을 보고 → 본 EDA의 onset 43건(gap≥7) 정의가 타당. `ADR-injury-label.md`(P0)에 이 일치를 근거로 인용.
2. **설계 선택 검증됨** — L2/L3가 생존모형·LOPO·SHAP을 사용 → 본 프로토콜 §E.3(이산시간 생존+frailty), §F(LOPO/시간분할), §E.3(SHAP) 설계가 학계 합의와 정렬.
3. **벤치마크 확보** — L2의 **C-index 0.762**, baseline F1(RF 0.533/XGB 0.429)을 본 연구 성능의 비교 기준으로 사전 등록.
4. **외적 타당도 경로** — D2(Lövdal 육상, 공개)로 종목 전이 검증(P5) → "단일 데이터셋" 한계(§I-2) 완화.
5. **겸손한 프레이밍의 학술적 근거** — L7(Bahr), L8(Bittencourt)로 "예측은 본질적으로 어렵다"는 점을 명시하고, 통계적 유의가 아닌 **임상효용(decision-curve)** 중심 평가(§F)를 정당화.

---

## 4. 출처 (Sources)

- SoccerMon: [Nature Sci Data](https://www.nature.com/articles/s41597-024-03386-x), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11139986/), [Zenodo DOI 10.5281/zenodo.10033832]
- DeepHit Time-to-Injury: [arXiv 2601.19479](https://arxiv.org/html/2601.19479v1)
- SoccerGuard: [arXiv 2411.08901](https://arxiv.org/html/2411.08901v1)
- Rossi et al. 2018: [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0201264), [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6059460/)
- Lövdal et al. 2021: [Groningen portal](https://research.rug.nl/en/publications/injury-prediction-in-competitive-runners-with-machine-learning/), [Kaggle](https://www.kaggle.com/shashwatwork/injury-prediction-for-competitive-runners), DataverseNL DOI 10.34894/UWU9PV
- GPS Wearables (Sensors 2023): [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9919698/), [MDPI](https://www.mdpi.com/1424-8220/23/3/1227)
- Iranian Pro Football (Frontiers 2025): [Frontiers](https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2025.1425180/full)
- Public datasets repo: [GitHub josedv82](https://github.com/josedv82/public_sport_science_datasets)
- Bahr 2016: [PubMed/BJSM]; Bittencourt 2016: [PubMed 27445362](https://pubmed.ncbi.nlm.nih.gov/27445362/)
- ML reviews: [J Exp Orthop](https://link.springer.com/article/10.1186/s40634-021-00346-x), [Scoping review PMC12013557](https://pmc.ncbi.nlm.nih.gov/articles/PMC12013557/)
- (R3) PMData: [SimulaMet](https://www.simulamet.no/research/pmdata-sports-logging-dataset), [OSF](https://osf.io/vx4bk/), [ACM](https://dl.acm.org/doi/abs/10.1145/3339825.3394926)
- (R3) ScopeSense: [Springer](https://link.springer.com/chapter/10.1007/978-3-031-27077-2_39)
- (R3) Sanchez et al. 2025 (12주 부하·HRV·부상): [SAGE](https://journals.sagepub.com/doi/10.1177/17479541251335613)
- (R3) Flatt & Esco 2015 (여자 축구 HRV): [IJSPP](https://journals.humankinetics.com/view/journals/ijspp/10/8/article-p994.xml)
- (R3) AFL 2년 부하·HRV (2024): [J Sports Sci](https://www.tandfonline.com/doi/full/10.1080/02640414.2024.2390238)
- (R3 Tier B) PPG HR/HRV: [arXiv 2505.18165](https://arxiv.org/pdf/2505.18165), [Multi-site PPG arXiv 2605.17859](https://arxiv.org/html/2605.17859v2)
- (R3 Tier B) PhysioNet Wearable Device Dataset(Stress+Exercise): [Sci Data](https://www.nature.com/articles/s41597-025-04845-9), [PhysioNet](https://physionet.org/content/wearable-device-dataset/1.0.1/); CogWear: [PhysioNet](https://physionet.org/content/consumer-grade-wearables/1.0.0/)
- (R3 Tier D ⚠ provenance 미검증·합성 추정) Kaggle: [Athlete Training & Recovery](https://www.kaggle.com/datasets/prince7489/athlete-training-and-recovery-tracker-dataset), [Athlete Injury & Performance](https://www.kaggle.com/datasets/ziya07/athlete-injury-and-performance-dataset), [PMData mirror](https://www.kaggle.com/datasets/vlbthambawita/pmdata-a-sports-logging-dataset)

---

*마지막 갱신: 2026-05-30 | 본 문서는 `RESEARCH_PROTOCOL.md` §A·§D·§G와 상호 참조된다.*
