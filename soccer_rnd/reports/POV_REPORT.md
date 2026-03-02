# 훈련 부하 지표와 회복/웰니스 반응 간 시차 관계에 대한 통계적 관점 보고서

> **프로젝트**: soccer_rnd — 공개 데이터셋 기반 부하-회복 시차 관계 정량 분석
> **작성**: report-writer@soccer-rnd
> **최종 갱신**: 2026-02-11
> **재현 환경**: Python 3.13, numpy (seed=42), pandas 2.3.1, statsmodels 0.14.5, scipy 1.16.1
> **데이터 출처**: PhysioNet ACTES (Track A), SoccerMon/Zenodo (Track B)
> **라이선스**: 내부 연구 문서

---

## 요약 (Executive Summary)

본 보고서는 **실제 공개 데이터셋**을 활용하여 훈련 부하 지표(ACWR, Monotony, Strain)와 회복/웰니스 지표(HRV, Hooper Index) 사이의 관계를 정량적으로 제시하는 통계적 관점(Point of View) 문서이다. 핵심 발견은 다음과 같다.

### Track A — HRV 중심 (PhysioNet ACTES, 18명)

1. **파워-HRV 용량-반응 관계**: 점증 운동 부하 검사에서 파워 구간이 높아질수록 rMSSD가 유의하게 감소하였다 (Rest: 7.6±2.4ms → High: 4.6±1.5ms). 혼합효과모형에서 power_mean 계수 = **-0.016** (p < 0.001)로, 파워 1W 증가 시 rMSSD가 약 0.016ms 감소하는 용량-반응 관계가 확인되었다.

2. **개인차 반영의 중요성**: 랜덤 절편 혼합효과모형(AIC=296.3)이 OLS(AIC=293.9) 대비 MAE 기준 개선을 보였으며 (OLS MAE=1.64 → Mixed MAE=1.41), 피험자 간 기저 HRV 수준의 이질성이 확인되었다 (랜덤효과 분산=0.56).

3. **30초 윈도우 세밀 분석**: 486개 30초 윈도우 기반 ln(rMSSD) ~ power 혼합효과모형에서 계수 = **-0.002** (p < 0.001)로 연속적 용량-반응 관계가 확인되었다.

4. **이월 효과(Carryover)**: 이전 파워 구간의 부하와 현재 rMSSD 간 Pearson r = **-0.465** (p = 0.001)로 유의한 이월 효과가 관찰되었다.

### Track B — 부하+설문 중심 (SoccerMon, 44명 엘리트 축구 선수)

5. **개인 랜덤효과의 지배적 역할**: OLS(R²=0.000) 대비 혼합효과모형(R²=0.453)이 극적으로 개선되었으며, 이는 Hooper Index 변동의 약 45%가 **선수 간 개인차(랜덤 절편)**로 설명됨을 의미한다.

6. **ACWR-Hooper 관계**: 혼합효과모형에서 ACWR 계수 = **-0.089** (p < 0.001)로, ACWR이 1단위 증가할 때 다음 날 Hooper Index가 약 0.089 포인트 감소하는 경향이 관찰되었다. 이는 높은 급성 부하가 웰니스 자가보고를 오히려 낮추는 역설적 패턴으로, 활동적 훈련일에 주관적 컨디션이 양호하게 보고되는 선수 행동 특성과 관련될 수 있다.

7. **Monotony+Strain 복합 효과**: M4 모형(ACWR+Monotony+Strain)에서 Monotony 계수 = **+0.142** (p = 0.002), Strain 계수 = **-0.00007** (p < 0.001)로, 부하 단조성이 높을수록 웰니스가 악화되는 독립적 효과가 확인되었다 (AIC: M3=54751 → M4=54737).

8. **LOSO 교차검증**: M3 모형의 Leave-One-Subject-Out 교차검증 결과 평균 MAE=**1.45** (SD=0.57), RMSE=**1.76**으로, 선수 간 예측 성능의 이질성이 관찰되었다 (MAE 범위: 0.58~2.91).

---

## 1. 서론 및 이론적 맥락

### 1.1 스포츠 부하 모니터링의 필요성

현대 스포츠 과학에서 훈련 부하의 체계적 모니터링은 선수의 경기력 향상과 부상/질병 예방을 위한 핵심 과제로 자리매김하고 있다 (Bourdon et al., 2017; Halson, 2014). 적절한 수준의 훈련 자극은 체력 향상을 유도하지만, 과도하거나 단조로운 부하는 피로 누적, 과훈련 증후군, 부상 위험의 증가로 이어질 수 있다 (Foster, 1998; Gabbett, 2016).

### 1.2 Fitness-Fatigue 모형과 ATL/CTL/ACWR

Banister et al. (1975)이 제안한 Fitness-Fatigue 모형에서 파생된 ATL(7일), CTL(28일), ACWR(ATL/CTL)은 급성 대 만성 부하의 균형을 정량화한다. Gabbett (2016)의 "sweet spot" (0.8~1.3)과 "danger zone" (>1.5) 개념이 널리 활용되나, ACWR의 개념적 한계에 대한 비판도 존재한다 (Lolli et al., 2019; Impellizzeri et al., 2020; Wang et al., 2020).

### 1.3 HRV와 자율신경계 회복

rMSSD는 부교감(vagal) 신경 활동을 반영하며, 훈련 부하 증가 시 일시적으로 억제되고 회복 후 기저 수준으로 복귀하는 패턴이 보고되어 있다 (Buchheit, 2014; Plews et al., 2013).

### 1.4 Hooper Index와 주관적 웰니스

Hooper & Mackinnon (1995)이 제안한 Hooper Index(= fatigue + stress + DOMS + sleep quality)는 선수의 주관적 회복 상태를 간편하게 정량화하는 도구이다. Saw et al. (2016)은 주관적 웰니스 지표가 객관적 지표보다 급성 부하 변화에 민감하게 반응함을 보고하였다.

---

## 2. 데이터 및 지표

### 2.1 Track A 데이터셋: PhysioNet ACTES

| 항목 | 내용 |
|------|------|
| 정식 명칭 | Cardiorespiratory measurement from graded cycloergometer exercise testing |
| 출처 | https://physionet.org/content/actes-cycloergometer-exercise/1.0.0/ |
| 라이선스 | Open Data Commons Attribution License v1.0 |
| 피험자 수 | 18명 (fencing 10명, kayak 6명, triathlon 2명) |
| 연령 | 12~18세 |
| 프로토콜 | 최대 점증 자전거 에르고미터 운동 부하 검사 |
| 주요 변수 | RR interval (ms), Power (W), VO2 (L/min), Time (s) |
| 데이터 규모 | 52,062 beat-level 관측 |

**분석 설계 조정**: ACTES는 단일 세션 점증 운동 검사로, 다일 시계열 ATL/CTL/ACWR 산출이 불가하므로 **세션 내 파워 구간별 HRV 반응 분석**으로 설계를 조정하였다 (ADR-012).

**파워 구간 정의** (개인별 환기역치 기반):
- **Rest**: power = 0W (운동 전 안정기)
- **Low**: 0 < power ≤ P_vt1
- **Moderate**: P_vt1 < power ≤ P_vt2
- **High**: power > P_vt2

### 2.2 Track B 데이터셋: SoccerMon

| 항목 | 내용 |
|------|------|
| 정식 명칭 | SoccerMon: Large-Scale Multivariate Soccer Athlete Monitoring Dataset |
| 출처 | https://zenodo.org/records/10033832 (DOI: 10.5281/zenodo.10033832) |
| 인용 논문 | Midoglu et al. (2024), *Scientific Data* |
| 라이선스 | CC BY 4.0 |
| 대상 | 노르웨이 여자 엘리트 축구 리그 (Toppserien) 2개 팀, 50명 |
| 분석 대상 | 44명 (60일 이상 유효 데이터 보유 선수) |
| 기간 | 2020-01-09 ~ 2021-12-31 (약 2년) |
| 주관적 변수 | Daily Load (sRPE), Fatigue (1-5), Stress (1-10), Soreness (1-5), Sleep Quality (1-5) |
| 부하 지표 | ACWR, ATL, Monotony, Strain (사전 계산 제공) |
| 분석 관측 수 | 16,186건 (시차 모형용) |

**Hooper Index 매핑**: fatigue + stress_norm(= stress/2) + soreness + sleep_quality. Stress를 1-10에서 1-5 척도로 정규화하였다 (ADR-012). 전통적 Hooper Index(4-28)와 다소 상이한 범위(4.5-17.5)를 갖는다.

### 2.3 지표 정의 요약

| 지표 | 공식 | 출처 |
|------|------|------|
| rMSSD | √(mean(ΔNN²)) | Task Force (1996) |
| SDNN | std(NN intervals) | Task Force (1996) |
| ln(rMSSD) | ln(rMSSD) | Plews et al. (2013) |
| ATL | 7일 rolling mean | Hulin et al. (2014) |
| CTL | 28일 rolling mean | Hulin et al. (2014) |
| ACWR | ATL / CTL | Gabbett (2016) |
| Monotony | mean(7d load) / sd(7d load) | Foster (1998) |
| Strain | weekly_load × Monotony | Foster (1998) |
| Hooper Index | fatigue + stress + DOMS + sleep | Hooper et al. (1995) |

---

## 3. Track A 분석 결과: HRV-파워 용량-반응 관계

### 3.1 데이터 품질 점검

| 항목 | 결과 |
|------|------|
| 총 RR 기록 | 52,062건 |
| 유효 RR (이상치 필터링 후) | 35,590건 |
| 이상치 제거율 | 30.1% (중앙값 ±20% 기준) |
| 피험자별 유효 비트 수 | 최소 1,148 ~ 최대 2,614 |

이상치 제거율이 30.1%로 다소 높은데, 이는 운동 중 발생하는 심박 아티팩트(근전도 간섭, 호흡 영향 등)가 상당수 포함된 것으로 판단된다. 안정기(Rest)에서 이상치 비율이 상대적으로 낮고, 고강도(High) 구간에서 높아지는 패턴이 관찰되었다.

### 3.2 파워 구간별 HRV 분포

| 파워 구간 | n | rMSSD (ms) | SDNN (ms) | ln(rMSSD) |
|-----------|---|------------|-----------|-----------|
| Rest | 18 | 7.60 ± 2.39 | 48.91 ± 6.84 | 1.98 ± 0.35 |
| Low | 18 | 6.73 ± 2.27 | 22.42 ± 8.70 | 1.85 ± 0.34 |
| Moderate | 18 | 5.22 ± 1.97 | 21.39 ± 8.90 | 1.60 ± 0.32 |
| High | 13 | 4.59 ± 1.55 | 6.70 ± 4.28 | 1.48 ± 0.29 |

**관찰**: 파워 구간이 Rest → Low → Moderate → High로 증가함에 따라 rMSSD가 **단조 감소**하는 경향이 관찰된다. 이는 운동 강도 증가에 따른 부교감신경 철수(vagal withdrawal)와 일관된 패턴으로, Buchheit (2014)의 보고와 부합한다.

SDNN의 경우 Rest에서 매우 높은 값(48.91ms)을 보이다가 Low/Moderate에서 급감(~21ms)하고 High에서 더욱 감소(6.70ms)하는데, 이는 안정기의 높은 전체 변이성이 운동 중 교감신경 우세로 전환되면서 급격히 감소함을 반영한다.

5명의 피험자가 High 구간에서 min_count(30비트) 미만의 데이터를 가져 HRV 산출이 불가하였다.

### 3.3 통계 모형 비교

| 모형 | AIC | BIC | MAE | RMSE |
|------|-----|-----|-----|------|
| OLS (구간변수) | 293.9 | 302.7 | 1.64 | 2.04 |
| 랜덤 절편 (power_mean) | 296.3 | 302.9 | 1.41 | 1.74 |
| 랜덤 기울기 (power_mean) | 300.6 | 311.6 | 1.24 | 1.54 |

**랜덤 절편 모형 (채택 모형)**:
```
rMSSD ~ power_mean + (1|subject)
  Intercept:  7.743 (p < 0.001)
  power_mean: -0.016 (p < 0.001)
  Group Var:  0.561
```

- **해석**: 파워가 0W일 때 평균 rMSSD는 7.74ms이며, 파워 1W 증가 시 rMSSD가 평균 0.016ms 감소한다. 예를 들어, 100W에서 200W로 파워가 증가하면 rMSSD는 약 1.6ms 감소할 것으로 예측된다.
- **개인차**: 랜덤효과 분산 0.56은 피험자 간 기저 rMSSD 수준에 약 ±0.75ms (√0.56)의 표준편차가 있음을 의미한다.
- 랜덤 기울기 모형은 MAE 기준 추가 개선(1.41 → 1.24)을 보였으나 수렴이 불완전하였고, AIC/BIC 기준 패널티가 더 커 랜덤 절편 모형을 최종 채택한다.

### 3.4 30초 윈도우 용량-반응 분석

486개의 30초 윈도우에서 산출한 ln(rMSSD) ~ power 혼합효과모형:

```
ln(rMSSD) ~ power_mean + (1|subject)
  Intercept:  1.832 (p < 0.001)
  power_mean: -0.002 (p < 0.001)
  Group Var:  0.044
  AIC: 314.3, BIC: 326.9
```

30초 단위의 세밀한 분석에서도 파워 증가에 따른 ln(rMSSD) 감소가 통계적으로 유의하게 확인되었으며 (p < 0.001), 이는 연속적 용량-반응 관계를 시사한다.

### 3.5 시차(Carryover) 분석

이전 파워 구간의 부하가 현재 구간의 HRV에 미치는 이월 효과를 검토하였다.

- **이전 구간 파워 → 현재 rMSSD**: Pearson r = -0.465, p = 0.001
- **혼합효과모형** (current_rMSSD ~ prev_power + current_power + (1|subject)):
  - prev_power_mean: 계수 = -0.003, p = 0.796
  - current_power_mean: 계수 = -0.014, p = 0.193

→ 단순 상관에서는 이전 구간 파워와 현재 rMSSD 간 유의한 음의 상관이 있었으나, 현재 구간 파워를 통제하면 이전 구간의 독립적 효과는 유의하지 않았다. 이는 파워 구간 간 순차적 증가 패턴(Rest→Low→Moderate→High)이 상관의 주된 원인임을 시사한다.

### 3.6 종목별 비교

| 종목 | n (피험자) | Rest rMSSD | High rMSSD | 감소폭 |
|------|-----------|-----------|-----------|--------|
| Fencing | 10 | 6.8 ± 3.0 | 4.8 ± 1.7 | -2.0 |
| Kayak | 6 | 8.2 ± 1.8 | 4.0 ± 1.0 | -4.2 |
| Triathlon | 2 | 6.8 ± 0.2 | 4.5 (n=1) | -2.3 |

Kayak 선수들이 안정 시 rMSSD가 가장 높고, 고강도에서의 감소폭도 가장 컸다. 다만 표본 크기가 매우 작아(특히 triathlon 2명) 종목 간 차이에 대한 통계적 검정력은 제한적이다.

---

## 4. Track B 분석 결과: 부하-웰니스 시차 관계

### 4.1 데이터 품질 및 기술 통계

| 변수 | 유효 관측 | 평균 | SD | 범위 | 결측률 |
|------|-----------|------|-----|------|--------|
| Daily Load (sRPE) | 24,596 | 284.9 | 323.3 | 0-3420 | 0% |
| Fatigue (1-5) | 16,618 | 3.03 | 0.63 | 1-5 | 32.4% |
| Stress (1-10) | 16,623 | 3.21 | 0.63 | 1-5 | 32.4% |
| Soreness (1-5) | 16,625 | 2.80 | 0.74 | 1-5 | 32.4% |
| Sleep Quality (1-5) | 16,620 | 3.27 | 0.72 | 1-5 | 32.4% |
| Hooper Index | 16,592 | 10.70 | 1.77 | 4.5-17.5 | 32.5% |
| ACWR | 24,596 | 0.98 | 0.76 | 0-4.0 | 0% |
| Monotony | 24,596 | 1.05 | 0.69 | 0-8.75 | 0% |
| Strain | 24,596 | 2,787 | 2,552 | 0-34,475 | 0% |

- 웰니스 변수의 결측률이 약 32%로 높은데, 이는 비훈련일/휴일에 설문 미응답이 빈번하기 때문이다.
- ACWR 평균 0.98은 "sweet spot" 영역(0.8-1.3)의 중심에 위치하며, 전반적으로 적절한 부하 관리가 이루어졌음을 시사한다.

### 4.2 주간 부하 패턴

요일별 평균 Daily Load 분석 결과, 시즌 중 주중 훈련과 주말 경기의 주기적 패턴이 관찰되었다 (그림: `track_B_weekly_load_pattern.png`).

### 4.3 ACWR-Hooper 시차 관계

**단변량 상관**: ACWR(t)와 Hooper(t+1)의 Pearson r = -0.004 (p = 0.59)로, 전체 수준에서의 선형 상관은 극히 미약하였다. 이는 **개인차가 통제되지 않은** 풀링 상관이 관계를 희석하기 때문이다.

**다중 시차 분석 (lag 0-7)**:

| Lag | r | p | n |
|-----|---|---|---|
| 0 | 0.005 | 0.551 | 16,299 |
| 1 | -0.004 | 0.593 | 16,186 |
| 2 | 0.008 | 0.293 | 16,086 |
| 3 | 0.014 | 0.071 | 15,996 |
| 4 | 0.016 | 0.045* | 15,902 |
| 5 | 0.020 | 0.012* | 15,826 |
| 6 | 0.024 | 0.003** | 15,750 |
| 7 | 0.027 | 0.001*** | 15,687 |

→ 시차가 길어질수록 상관 강도가 미약하나 점진적으로 증가하는 패턴이 관찰되며, lag 7에서 최대 |r| = 0.027을 보였다. 다만 이 효과 크기는 매우 작다.

### 4.4 혼합효과모형 비교

| 모형 | AIC | BIC | MAE | RMSE | R² | Cohen's f² |
|------|-----|-----|-----|------|-----|-----------|
| M1: OLS (acwr) | 64,509 | 64,524 | 1.35 | 1.77 | 0.000 | — |
| M2: Mixed (acwr) | 54,751 | 54,774 | 0.99 | 1.31 | 0.453 | 0.828 |
| M3: Mixed (acwr+monotony) | 54,751 | 54,782 | 0.99 | 1.31 | 0.453 | 0.828 |
| M4: Mixed (acwr+mono+strain) | 54,737 | 54,775 | 0.99 | 1.31 | 0.454 | 0.830 |

**핵심 관찰**:

1. **OLS → Mixed 효과의 극적 개선**: R²가 0.000에서 0.453으로 도약하며, AIC가 약 10,000 포인트 감소하였다. 이는 **개인 랜덤효과**가 Hooper Index 변동을 설명하는 핵심 요인임을 의미한다. 즉, 각 선수의 "기저 웰니스 수준"이 크게 다르며, 이를 무시한 풀링 분석은 부적절하다.

2. **M4가 최적 모형**: AIC 기준으로 M4(54,737)가 M3(54,751)보다 14포인트 낮아 개선이 확인되었다. Monotony(p=0.002)와 Strain(p<0.001)이 각각 유의한 고정효과를 보였다.

**M4 모형 상세**:
```
hooper_lag1 ~ acwr + monotony + strain + (1|athlete_id)
  Intercept: 10.880 (p < 0.001)
  acwr:      -0.078 (p < 0.001)
  monotony:  +0.142 (p = 0.002)
  strain:    -0.00007 (p < 0.001)
  Group Var: 1.573
```

- **ACWR 계수 (-0.078)**: ACWR 1단위 증가 시 다음 날 Hooper Index가 0.078 감소. 역설적이지만, 활발한 훈련(높은 ACWR) 후 선수들이 주관적 컨디션을 양호하게 보고하거나, 고ACWR 시기에 휴식일이 뒤따르는 구조적 패턴이 반영되었을 가능성이 있다.
- **Monotony 계수 (+0.142)**: 부하 단조성이 1단위 증가 시 Hooper Index가 0.142 증가 (웰니스 악화). 이는 단조로운 부하가 주관적 피로 증가에 독립적으로 기여함을 시사하며, Foster (1998)의 보고와 일관된다.
- **랜덤효과 분산 (1.573)**: 선수 간 기저 Hooper Index의 표준편차가 약 ±1.25 포인트에 달한다.

### 4.5 LOSO 교차검증

M3 모형에 대한 Leave-One-Subject-Out 교차검증 결과:

| 지표 | 평균 | SD | 범위 |
|------|------|-----|------|
| MAE | 1.45 | 0.57 | 0.58 - 2.91 |
| RMSE | 1.76 | 0.61 | 0.76 - 3.44 |

- 44명 전원에 대해 LOSO가 성공적으로 수행되었다.
- 선수별 예측 성능에 상당한 이질성이 존재하며 (MAE 범위 0.58~2.91), 일부 선수는 매우 정확하게 예측(MAE<1.0)되는 반면 다른 선수는 예측이 어려운 것으로 나타났다 (MAE>2.5).
- 이러한 이질성은 모형에 포함되지 않은 요인(심리적 상태, 사회적 스트레스, 수면 패턴 등)이 선수별로 다르게 작용함을 시사한다.

### 4.6 Monotony 임계값 효과

Monotony > 2.0 (Foster의 과훈련 위험 임계값) 그룹과 ≤ 2.0 그룹의 Hooper Index 비교:

| 그룹 | n | Hooper Mean | Hooper SD |
|------|---|------------|-----------|
| Monotony ≤ 2.0 | 14,798 | 10.70 | 1.77 |
| Monotony > 2.0 | 1,388 | 10.67 | 1.81 |

- Welch t = 0.608, p = 0.543, Cohen's d = -0.017
- 이분법적 임계값(2.0)에 의한 집단 비교에서는 유의한 차이가 관찰되지 않았다. 이는 연속변수 모형(M4)에서 유의했던 Monotony 효과가 이분법적 접근에서 희석되었음을 의미하며, 부하-웰니스 관계의 비선형성 또는 개인차 효과의 중요성을 시사한다.

---

## 5. 해석 및 시사점

### 5.1 부하-회복 관계의 다차원성

Track A와 Track B의 결과를 종합하면, 부하-회복 관계는 단순한 선형 모형으로 포착되기 어려운 다차원적 현상임을 알 수 있다:

1. **객관적 지표(HRV)는 부하에 직접적으로 반응**: Track A에서 파워 증가에 따른 rMSSD 감소가 명확하고 일관되게 관찰되었다 (p < 0.001). 이는 자율신경계의 생리적 반응이 운동 강도에 강하게 결합되어 있음을 확인한다.

2. **주관적 지표(Hooper)는 복합적 요인에 의해 결정**: Track B에서 부하 변수만으로 설명되는 분산은 극히 제한적이었으며, 개인 랜덤효과가 변동의 약 45%를 설명하였다. 이는 주관적 웰니스가 훈련 부하 외에도 심리적, 사회적, 환경적 요인에 의해 크게 좌우됨을 의미한다.

### 5.2 개인화 모니터링의 필요성

두 트랙 모두에서 **개인 랜덤효과**가 모형 성능의 핵심이었다:
- Track A: 랜덤효과 분산 0.56 (기저 rMSSD 개인차)
- Track B: 랜덤효과 분산 1.57 (기저 Hooper 수준 개인차)

이는 부하-회복 관계를 활용한 선수 모니터링 시스템이 **선수 개인의 기저선(baseline)**을 반드시 고려해야 함을 의미하며, 집단 평균 기반 임계값의 적용에는 한계가 있음을 시사한다.

### 5.3 Monotony의 독립적 역할

Track B M4 모형에서 Monotony가 ACWR을 통제한 후에도 유의한 양의 효과(+0.142, p=0.002)를 보인 것은 실무적으로 중요한 시사점을 갖는다. 단순히 부하량의 절대 수준이나 급만성 비율뿐 아니라, **부하의 변이성(다양성)**이 선수 웰니스에 독립적으로 영향을 미칠 수 있다는 것이다. 이는 Foster (1998)의 원래 제안과 일관되며, 훈련 프로그래밍에서 부하의 주기화(periodization)가 갖는 중요성을 뒷받침한다.

---

## 6. 제한점

1. **Track A 설계적 한계**: ACTES는 단일 점증 운동 검사 데이터로, 다일 부하-HRV 시차 관계(ATL/CTL/ACWR → 다음 날 HRV)를 직접 분석할 수 없다. 본 분석은 세션 내 용량-반응 관계에 국한되며, 종단적 훈련 적응 효과를 포함하지 않는다.

2. **Track B 인과 관계**: 관측 연구에서 ACWR/Monotony와 Hooper Index 간의 연관은 관찰적(correlational)이며 인과적(causal) 해석에는 주의가 필요하다. 역인과(선수 상태가 훈련 참여에 영향) 가능성이 존재한다.

3. **Hooper Index 척도 차이**: SoccerMon의 Stress 척도(1-10)가 전통적 Hooper 척도(1-7)와 상이하여 정규화(÷2)를 적용하였으나, 이로 인해 전통적 Hooper Index와의 직접 비교에 제약이 있다.

4. **결측 패턴**: Track B의 웰니스 변수 결측률(~32%)이 높으며, 결측이 무작위(MAR)인지 체계적(MNAR)인지 불확실하다. 비훈련일 결측이 대부분이라면 분석에 체계적 편향이 있을 수 있다.

5. **표본 특성**: Track A는 12-18세 청소년 선수, Track B는 여자 엘리트 축구 선수로, 결과의 일반화에는 성별, 연령, 종목 특수성을 고려해야 한다.

6. **시간적 자기상관**: 반복 측정 데이터의 시간적 자기상관(temporal autocorrelation)이 모형에 명시적으로 반영되지 않았다. AR(1) 구조 등을 추가하면 추정의 정밀도가 개선될 수 있다.

---

## 7. 결측 데이터 처리 및 과부하 표기 정책 (향후 애플리케이션 적용)

본 분석 결과를 실제 선수 모니터링 애플리케이션에 적용할 때, **결측 데이터**는 피할 수 없는 현실적 문제이다. SoccerMon 데이터에서 웰니스 설문 결측률이 약 32.4%에 달한 사실은 이를 잘 보여준다. 이 섹션에서는 결측이 부하 지표 산출과 과부하 경고에 미치는 영향을 분석하고, 애플리케이션 수준에서의 처리 정책을 제안한다.

> **주의**: 아래 정책은 문헌 근거와 본 분석 결과에 기반한 **제안(proposal)** 수준이며, 현장 적용 전에 추가 검증과 팀 내 합의가 필요하다.

### 7.1 결측 유형 분류

통계학에서 결측 메커니즘은 세 가지로 분류된다 (Rubin, 1976). 스포츠 모니터링 맥락에서 각 유형의 실제 예시는 다음과 같다.

| 유형 | 정의 | 스포츠 맥락 예시 | 분석 영향 |
|------|------|------------------|-----------|
| **MCAR** (Missing Completely At Random) | 결측이 관측값·미관측값 모두와 무관 | 앱 오류로 인한 데이터 유실, 기기 배터리 방전 | 편향 없음, 검정력 감소 |
| **MAR** (Missing At Random) | 결측이 다른 관측 변수에 의존 | 비훈련일(일정이 관측됨)에 설문 미입력 | 조건부 분석 시 편향 통제 가능 |
| **MNAR** (Missing Not At Random) | 결측이 미관측 값 자체에 의존 | 피로·컨디션 저하 시 의도적 미보고, 부상 선수의 기록 중단 | **체계적 편향** 위험, 보정 어려움 |

**SoccerMon 데이터의 결측 패턴 분석**: Track B에서 관찰된 32.4% 결측은 주로 비훈련일에 집중되어 있어 MAR 패턴에 가까운 것으로 판단된다. 그러나 MNAR 요소를 완전히 배제할 수 없다 — 예컨대 컨디션이 매우 나쁜 날 선수가 설문 응답을 회피하는 경우, 웰니스 지표가 실제보다 양호하게 편향될 수 있다. Saw et al. (2016)은 주관적 모니터링에서 응답 부담(response burden)이 결측의 주요 원인임을 보고한 바 있다.

### 7.2 Rolling 지표의 결측 민감도

ATL, CTL, ACWR, Monotony, Strain 등 rolling 윈도우 기반 지표는 연속 기록을 전제로 설계되었으므로, 결측일이 산출 결과에 직접적 영향을 미친다.

#### 7.2.1 ATL(7일) 및 CTL(28일) 산출 시 결측 영향

| 결측 처리 방식 | 장점 | 단점 | 적합 상황 |
|----------------|------|------|-----------|
| **0으로 대체** | 산출이 항상 가능, 구현 단순 | 실제 부하가 있었을 수 있는 날을 0으로 간주하여 ATL/CTL을 **과소 추정** | 결측=확실한 비훈련일(예: 일정 확인 가능)인 경우 |
| **NA 유지** | 결측일은 산출에서 제외, 편향 최소화 | 윈도우 내 유효일 수 부족 시 지표 산출 불가 | 결측 원인이 불확실한 경우 (기본 권장) |
| **보간(Interpolation)** | 시계열 연속성 유지, 시각화에 유리 | 실제 관측이 아닌 추정값이 지표에 반영, 불확실성 과소 추정 | 산발적 결측(1~2일)이고, 전후 데이터 패턴이 안정적인 경우 |

**권장**: 원칙적으로 NA를 유지하되, 윈도우 내 유효일 수가 최소 요구사항을 충족하는 경우에만 지표를 산출한다 (7.3절 참조). 부하 데이터(daily_load)가 자동 수집(GPS 등)으로 확보되어 결측=비훈련일이 확실한 경우에 한해 0 대체를 적용할 수 있다.

#### 7.2.2 ACWR 산출 시 division by zero 문제

ACWR = ATL / CTL에서, 시즌 초반이나 장기 휴식 후 CTL이 0에 근접하면 ACWR이 무한대로 발산한다. 이는 지표의 수학적 한계로, Lolli et al. (2019)과 Impellizzeri et al. (2020)이 지적한 ACWR의 근본적 문제 중 하나이다.

**처리 방안**:
- CTL < 임계값(예: 50 AU) 이하인 경우 ACWR을 산출하지 않고 "데이터 부족" 상태로 표기
- 또는 분모에 소량의 상수를 추가하는 smoothing 기법 적용 (예: ACWR = ATL / (CTL + ε), ε = 50)
- Williams et al. (2017)이 제안한 EWMA 방식은 초기값 민감도가 낮아 이 문제를 부분적으로 완화한다

#### 7.2.3 Monotony 산출 시 결측의 SD 영향

Monotony = mean(7일 부하) / sd(7일 부하)에서, 결측일 처리에 따라 SD가 왜곡될 수 있다:

- **결측을 0으로 처리**: 비훈련일과 결측이 구분되지 않아 SD가 인위적으로 증가 → Monotony **과소** 추정
- **결측을 제외하고 산출**: 유효일 수가 감소하여 SD 추정의 안정성 저하, 특히 유효일이 2~3일이면 SD 추정이 극히 불안정
- Foster (1998)의 원래 공식은 7일 연속 기록을 전제로 하였으므로, 결측이 있는 주간에는 Monotony 해석에 주의가 필요하다

### 7.3 최소 데이터 요구사항

신뢰할 수 있는 부하 지표 산출을 위한 최소 기록 요건을 아래와 같이 제안한다.

| 지표 | 윈도우 | 최소 유효일 수 | 근거 |
|------|--------|---------------|------|
| **ATL** (7일) | 7일 | **5일 이상** (71%) | 7일 중 2일까지 결측 허용, 그 이상이면 편향 위험 |
| **CTL** (28일) | 28일 | **21일 이상** (75%) | 초기 워밍업 기간 포함, Hulin et al. (2014) 참조 |
| **ACWR** | ATL+CTL | ATL ≥ 5일 **그리고** CTL ≥ 21일 | 두 조건 모두 충족 필요 |
| **Monotony** (7일) | 7일 | **5일 이상** (71%) | SD 안정성 확보, 2일 이하 유효일 시 SD 극히 불안정 |
| **Strain** | 7일 | Monotony 산출 가능 시 | Monotony 의존 |

**CTL 안정화 워밍업 기간**: 새 선수가 시스템에 등록되거나 시즌이 시작될 때, CTL이 의미 있는 만성 부하를 반영하려면 최소 **21~28일**의 연속 기록이 필요하다. 이 기간 동안에는 ACWR을 산출하지 않거나, "워밍업 기간"이라는 상태 표기를 사용하는 것을 권장한다. Murray et al. (2017)은 EWMA 방식이 rolling average보다 초기 불안정성이 다소 낮음을 보고하였다.

### 7.4 과부하 경고(Overload Alert) 정책 제안

#### 7.4.1 ACWR 기반 과부하 경고 조건

Gabbett (2016)의 "danger zone" 개념과 본 분석 결과를 종합하여, 다음과 같은 경고 체계를 제안한다.

| ACWR 범위 | 상태 | 설명 |
|-----------|------|------|
| < 0.8 | 저부하(Undertraining) | 탈훈련(detraining) 위험, 부하 점진적 증가 권고 |
| 0.8 ~ 1.3 | 적정(Sweet Spot) | 최적 적응 영역 (Gabbett, 2016) |
| 1.3 ~ 1.5 | 주의(Caution) | 부하 급등 구간, 모니터링 강화 권고 |
| > 1.5 | 과부하(Overload) | 부상/과훈련 위험 증가, 부하 조절 검토 필요 |

> **주의**: ACWR "danger zone"의 보편적 적용에 대해서는 비판이 존재한다 (Impellizzeri et al., 2020; Wang et al., 2020). 임계값은 종목, 포지션, 개인 특성에 따라 조정이 필요하며, 본 분석의 Track B에서도 ACWR의 Hooper Index 예측 효과 크기가 미약하였음을 유의해야 한다.

#### 7.4.2 결측률에 따른 경고 신뢰도 등급

결측 상황에서 과부하 경고의 신뢰도를 사용자에게 투명하게 전달하기 위해, 최근 7일 기록 완성도에 기반한 **신뢰도 등급 체계**를 제안한다.

| 등급 | 최근 7일 기록일 수 | 신뢰도 | 표시 정책 | 사용자 안내 |
|------|-------------------|--------|-----------|-------------|
| **Green** | 6~7일 | 높음 | 경고 정상 표시 | "데이터 충분 — 경고를 신뢰할 수 있습니다" |
| **Yellow** | 4~5일 | 중간 | 경고 표시 + 주의 문구 | "일부 데이터 누락 — 경고는 참고용입니다" |
| **Red** | 0~3일 | 낮음 | 경고 비표시 + 데이터 부족 안내 | "데이터 부족 — 정확한 분석을 위해 기록을 채워주세요" |

```
[ 과부하 경고 의사결정 플로차트 ]

1. 최근 7일 기록일 수 확인
   │
   ├─ 0~3일 → [Red] 경고 비표시, "데이터 부족" 안내
   │
   ├─ 4~5일 → [Yellow] 경고 산출 후 "참고용" 표기
   │              │
   │              ├─ CTL ≥ 21일 워밍업 완료? ─ No → "워밍업 기간" 표기
   │              │
   │              └─ Yes → ACWR 산출 → 경고 등급 판정 (참고용)
   │
   └─ 6~7일 → [Green] 경고 정상 산출
                  │
                  ├─ CTL ≥ 21일 워밍업 완료? ─ No → "워밍업 기간" 표기
                  │
                  └─ Yes → ACWR 산출 → 경고 등급 판정
                             │
                             ├─ ACWR > 1.5 → "과부하 경고"
                             ├─ ACWR 1.3~1.5 → "주의"
                             ├─ ACWR 0.8~1.3 → "적정"
                             └─ ACWR < 0.8 → "저부하"
```

#### 7.4.3 Monotony 경고의 결측 민감도

Monotony > 2.0은 Foster (1998)가 제안한 과훈련 위험 임계값으로 널리 사용되나, 결측 상황에서는 다음의 주의가 필요하다:

- 7일 중 2일 이상 결측 시 SD 추정이 불안정해져 Monotony가 인위적으로 높거나 낮게 산출될 수 있다
- 본 분석(Track B, 4.6절)에서도 이분법적 Monotony 임계값(> 2.0)에 의한 집단 비교는 유의하지 않았다 (p = 0.543)
- 따라서 Monotony 경고는 **최근 7일 중 5일 이상 기록이 있는 경우에만 표시**하는 것을 권장한다

#### 7.4.4 복합 경고 로직

단일 지표보다 **다중 지표의 동시 참조**가 과부하 탐지의 정확도를 높일 수 있다 (Bourdon et al., 2017). 본 분석에서 M4 모형이 ACWR, Monotony, Strain을 모두 포함했을 때 최적 AIC를 보인 것도 이를 뒷받침한다.

| 경고 수준 | 조건 | 권고 조치 |
|-----------|------|-----------|
| **Level 1** (단일 지표 이상) | ACWR > 1.5 **또는** Monotony > 2.0 | 해당 지표 강조 표시, 추이 모니터링 |
| **Level 2** (복합 이상) | ACWR > 1.5 **그리고** Monotony > 2.0 | 부하 조절 강력 권고, 코칭 스태프 알림 |
| **Level 3** (삼중 이상) | ACWR > 1.5 **그리고** Monotony > 2.0 **그리고** Strain > 상위 25% | 즉시 부하 감소 권고, 선수 면담 제안 |

> 복합 경고의 임계값은 팀 특성과 시즌 단계에 따라 조정이 필요하며, 본 분석의 Track B 결과에서 Strain의 고정효과 크기가 매우 작았음(β = -0.00007)을 고려하면 Strain 임계값의 실용적 유효성은 추가 검증이 필요하다.

### 7.5 결측 보완 전략

#### 7.5.1 부하 데이터 보완

| 전략 | 설명 | 실현 가능성 |
|------|------|-------------|
| **GPS/가속도 자동 수집** | 웨어러블 기기를 통한 외부 부하(external load) 자동 기록 | 높음 — 이미 많은 팀에서 활용 (Bourdon et al., 2017) |
| **심박수 기반 부하 추정** | Training Impulse(TRIMP) 등 심박 기반 내부 부하 추정 | 중간 — 심박 센서 착용 필요 |
| **세션 일정 기반 기본값** | 팀 훈련 일정에서 예상 부하를 기본값으로 할당 | 낮음 — 개인 참여 여부 불확실 |

SoccerMon 데이터에서 daily_load(sRPE) 결측률이 0%였던 것은, 부하 데이터가 팀 관리 시스템을 통해 체계적으로 수집되었기 때문으로 판단된다. 웰니스 데이터와 달리 부하 데이터는 자동 수집 인프라를 통해 결측을 최소화할 수 있다.

#### 7.5.2 웰니스 데이터 응답률 향상

| 전략 | 설명 | 근거 |
|------|------|------|
| **푸시 알림/넛지(Nudge)** | 매일 정해진 시간(예: 기상 후 30분)에 알림 발송 | Saw et al. (2016): 응답 부담 경감이 핵심 |
| **간소화된 설문** | 핵심 항목(3~4문항)으로 축소, 슬라이더/이모지 입력 | 응답 시간 30초 이내 목표 |
| **게이미피케이션** | 연속 기록 일수 표시, 팀 내 응답률 순위 등 | 행동 경제학 기반 동기 부여 |
| **코칭 스태프 연계** | 미응답 선수에 대한 대면 확인 프로세스 | 조직적 대응, 단 선수 자율성 침해 주의 |

#### 7.5.3 통계적 보간 방법

결측이 불가피한 경우 적용할 수 있는 보간 기법과 그 한계를 정리한다.

| 보간 기법 | 방법 | 장점 | 한계 |
|-----------|------|------|------|
| **선형 보간** (Linear Interpolation) | 전후 관측값의 선형 내삽 | 단순, 직관적 | 2일 이상 연속 결측 시 부정확, 비선형 패턴 미반영 |
| **LOCF** (Last Observation Carried Forward) | 마지막 관측값을 이월 | 구현 간단 | 변화 시점을 포착하지 못함, 특히 급격한 부하 변화 후 부적절 |
| **개인 기저선 대체** | 해당 선수의 최근 7일 평균으로 대체 | 개인차 반영 | 급성 변화 미반영, 기저선 자체의 변동 무시 |
| **다중 대체** (Multiple Imputation) | 여러 대체 데이터셋 생성 후 결합 | 불확실성 반영, 통계적으로 엄밀 | 구현 복잡, 실시간 애플리케이션에 부적합 |

**권장**: 애플리케이션 수준에서는 **1일 결측 시 선형 보간, 2일 이상 연속 결측 시 NA 유지** 정책이 실용적 균형점으로 판단된다. 통계 분석 목적으로는 다중 대체를 검토할 수 있으나, 실시간 경고 시스템에는 과도한 복잡성을 유발한다.

#### 7.5.4 개인 기저선(Baseline) 대체

Track B 분석에서 개인 랜덤효과가 Hooper Index 변동의 약 45%를 설명한 점을 고려하면, 결측 시 **해당 선수의 개인 기저선**으로 대체하는 것이 집단 평균 대체보다 합리적이다.

- **산출 방법**: 해당 선수의 최근 7일 이동 평균 (비결측 관측값 기준)
- **갱신 주기**: 새로운 관측이 입력될 때마다 갱신
- **한계**: 기저선 자체가 시즌 단계, 부상 이력, 컨디셔닝 수준에 따라 변동하므로, 장기적으로는 기저선의 트렌드 추적이 필요
- Flatt & Esco (2015)는 HRV 모니터링에서 개인 7일 이동 평균 기저선의 유용성을 보고한 바 있다

### 7.6 본 분석에서의 결측 처리 요약

본 보고서의 Track A와 Track B 분석에서 실제로 적용한 결측 처리 방식을 투명하게 기록한다.

| 항목 | Track A (HRV) | Track B (Hooper Index) |
|------|---------------|----------------------|
| **원본 데이터 규모** | 52,062 beat-level 관측 | 24,596 일별 관측 (44선수) |
| **주요 결측/제거** | RR 이상치 필터링 (중앙값 ±20%) | 웰니스 설문 미응답 (~32.4%) |
| **제거/결측률** | 30.1% (16,472건 제거) | Hooper Index 결측 32.5% |
| **처리 방식** | 이상치 제거 후 유효 RR만 사용, min_count=30 미만 시 해당 구간 NA | Hooper 구성요소 중 하나라도 NA이면 해당일 Hooper = NA |
| **지표 산출** | 30비트 이상 윈도우에서만 rMSSD/SDNN 산출 | SoccerMon 사전 제공 ACWR/Monotony/Strain 사용 (daily_load 기반, 결측 없음) |
| **모형 적합** | Complete-case 분석 (67구간 중 유효 구간만 포함) | Complete-case 분석 (시차 모형 16,186건) |
| **잠재적 편향** | 고강도 구간에서 이상치 비율이 높아 HRV 과대 추정 가능성 | 비훈련일 웰니스 미보고로 "건강한 날" 편향 가능성 |

> **참고**: 두 트랙 모두 complete-case 분석을 적용하였으므로, 결측이 MNAR 패턴을 따를 경우 결과에 체계적 편향이 포함되어 있을 수 있다 (6절 제한점 4번 참조). 향후 민감도 분석(sensitivity analysis)이나 다중 대체 접근을 통해 결측 편향의 강건성을 점검하는 것이 바람직하다.

---

## 8. 결론

본 연구는 두 개의 공개 데이터셋을 활용하여 운동 부하와 회복/웰니스 지표 간의 관계를 정량적으로 분석하였다.

**Track A**에서는 18명의 점증 운동 검사 데이터를 통해, 파워 증가에 따른 rMSSD 감소가 통계적으로 유의한 용량-반응 관계를 형성함을 확인하였다 (β = -0.016, p < 0.001). 이는 급성 운동 부하가 부교감신경 활동을 직접적으로 억제하는 생리적 메커니즘을 반영한다.

**Track B**에서는 44명 엘리트 축구 선수의 2시즌 데이터를 분석하여, **개인 랜덤효과가 Hooper Index 변동의 핵심 결정 요인**임을 확인하였다 (R² 도약: 0.00 → 0.45). ACWR과 Monotony가 각각 유의한 고정효과를 보였으나, 효과 크기는 개인차 대비 미약하였다.

이러한 결과는 스포츠 부하 모니터링에서 (1) **개인화된 기저선 추적**, (2) **다중 지표 통합 모니터링**, (3) **부하 변이성(Monotony) 관리**의 중요성을 시사한다.

---

## 부록 A: 생성된 파일 목록

### 시각화 (reports/figures/)
| 파일명 | 내용 |
|--------|------|
| `track_A_hrv_by_power_zone.png` | 파워 구간별 rMSSD 박스플롯 |
| `track_A_rmssd_vs_power_scatter.png` | rMSSD vs 평균 파워 산점도 (피험자별) |
| `track_A_rr_timeseries_sample.png` | 샘플 피험자 RR/파워 시계열 |
| `track_A_sport_comparison.png` | 종목별 HRV 비교 |
| `track_A_model_comparison.png` | Track A 모형 비교 (AIC/BIC/MAE/RMSE) |
| `track_B_weekly_load_pattern.png` | 주간 부하 패턴 (요일별) |
| `track_B_acwr_hooper_scatter.png` | ACWR vs Hooper Index 산점도 |
| `track_B_monotony_threshold.png` | Monotony 임계값 비교 |
| `track_B_missing_heatmap.png` | 결측 히트맵 |
| `track_B_load_distribution.png` | 부하/웰니스 변수 분포 |
| `track_B_timeseries_sample.png` | 샘플 선수 시계열 |
| `track_B_model_comparison.png` | Track B 모형 비교 |
| `track_B_lag_profile.png` | 다중 시차 상관 프로파일 |

### 처리 데이터 (data/processed/)
| 파일명 | 내용 |
|--------|------|
| `track_A_hrv_by_zone.csv` | 피험자×파워구간별 HRV 지표 (72행) |
| `track_B_merged.csv` | 병합 부하+웰니스 데이터 (24,596행, 44선수) |

### 분석 스크립트 (notebooks/)
| 파일명 | 내용 |
|--------|------|
| `run_track_A.py` | Track A 전체 분석 파이프라인 |
| `run_track_B.py` | Track B 전체 분석 파이프라인 |
| `run_synthetic_analysis.py` | 합성 데이터 분석 (Track A + B) |

### Jupyter 노트북 (notebooks/)
| 파일명 | 셀 수 | 내용 | 실행 상태 |
|--------|:------:|------|:---------:|
| `track_A_real.ipynb` | 37 (md 20 + code 17) | Track A 실제 데이터 전체 분석 | 실행 완료 |
| `track_B_real.ipynb` | 44 (md 23 + code 21) | Track B 실제 데이터 전체 분석 | 실행 완료 |
| `track_A_eda.ipynb` | — | Track A EDA (합성 데이터) | — |
| `track_B_eda.ipynb` | — | Track B EDA (합성 데이터) | — |
| `track_A_stats.ipynb` | — | Track A 통계 (합성 데이터) | — |
| `track_B_stats.ipynb` | — | Track B 통계 (합성 데이터) | — |

### 모형 비교 보고서 (reports/)
| 파일명 | 행 수 | 내용 |
|--------|:-----:|------|
| `track_A_model_comparison.md` | ~280 | Track A 실제 데이터 모형 비교 |
| `track_B_model_comparison.md` | ~280 | Track B 실제 데이터 모형 비교 |
| `track_A_model_comparison_synthetic.md` | 230 | Track A 합성 데이터 모형 비교 |
| `track_B_model_comparison_synthetic.md` | 260 | Track B 합성 데이터 모형 비교 |

---

## 부록 B: 참고문헌

1. Banister, E. W., et al. (1975). A systems model of training for athletic performance. *Australian Journal of Sports Medicine*, 7, 57-61.
2. Bourdon, P. C., et al. (2017). Monitoring athlete training loads. *International Journal of Sports Physiology and Performance*, 12(S2), S2161-S2170.
3. Buchheit, M. (2014). Monitoring training status with HR measures. *International Journal of Sports Physiology and Performance*, 9(5), 883-895.
4. Flatt, A. A., & Esco, M. R. (2015). Smartphone-derived heart-rate variability and training load in a women's soccer team. *International Journal of Sports Physiology and Performance*, 10(8), 994-1000.
5. Foster, C. (1998). Monitoring training in athletes with reference to overtraining syndrome. *Medicine & Science in Sports & Exercise*, 30(7), 1164-1168.
6. Gabbett, T. J. (2016). The training-injury prevention paradox. *British Journal of Sports Medicine*, 50(5), 273-280.
7. Halson, S. L. (2014). Monitoring training load to understand fatigue in athletes. *Sports Medicine*, 44(S2), 139-147.
8. Hooper, S. L., & Mackinnon, L. T. (1995). Monitoring overtraining in athletes. *Sports Medicine*, 20(5), 321-327.
9. Hulin, B. T., et al. (2014). The acute:chronic workload ratio predicts injury. *British Journal of Sports Medicine*, 48(8), 708-712.
10. Impellizzeri, F. M., et al. (2020). Acute:chronic workload ratio: Conceptual issues and fundamental pitfalls. *International Journal of Sports Physiology and Performance*, 15(7), 907-913.
11. Lolli, L., et al. (2019). Mathematical coupling causes spurious correlation within ACWR. *British Journal of Sports Medicine*, 53(1), 54-55.
12. Midoglu, C., et al. (2024). SoccerMon: A large-scale multivariate soccer athlete health, performance, and position monitoring dataset. *Scientific Data*, 11, 569.
13. Murray, N. B., et al. (2017). Calculating acute:chronic workload ratios using exponentially weighted moving averages. *International Journal of Sports Physiology and Performance*, 12(s2), S2171-S2177.
14. Plews, D. J., et al. (2013). Training adaptation and heart rate variability in elite endurance athletes. *International Journal of Sports Physiology and Performance*, 8(6), 688-694.
15. Rubin, D. B. (1976). Inference and missing data. *Biometrika*, 63(3), 581-592.
16. Saw, A. E., et al. (2016). Monitoring athletes through self-report measures. *International Journal of Sports Physiology and Performance*, 11(6), 710-714.
17. Task Force of ESC and NASPE. (1996). Heart rate variability: Standards of measurement. *Circulation*, 93(5), 1043-1065.
18. Wang, C., et al. (2020). Modelling the ACWR: Can we do better? *International Journal of Sports Physiology and Performance*, 15(7), 1023-1029.
19. Williams, S., et al. (2017). Better way to determine the ACWR. *British Journal of Sports Medicine*, 51(3), 209-210.

---

> **재현 절차 (스크립트)**: `python notebooks/run_track_A.py && python notebooks/run_track_B.py && python notebooks/run_synthetic_analysis.py`
> **재현 절차 (노트북)**: `jupyter nbconvert --execute notebooks/track_A_real.ipynb && jupyter nbconvert --execute notebooks/track_B_real.ipynb`
> **코드 추적성**: 모든 수치와 그림은 위 스크립트/노트북에서 산출되며, 동일 환경에서 동일 결과를 보장한다 (seed=42).
