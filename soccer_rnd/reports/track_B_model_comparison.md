# 트랙 B: 부하–웰니스 모형 비교 보고서

> **작성**: stats-lead@soccer-rnd
> **최종 갱신**: 2026-02-11
> **재현 환경**: Python 3, numpy seed=42, statsmodels mixedlm, sklearn
> **데이터**: SoccerMon — 프로 축구 선수 부하·설문 데이터 (44명 선수, 16,186 관측)
> **데이터 출처**: Midoglu et al. (2024). SoccerMon Dataset. *Scientific Data*. DOI: 10.5281/zenodo.10033832
> **노트북**: `notebooks/track_B_real.ipynb` (실행 완료, 전체 셀 출력 포함)

---

## 1. 분석 목적

본 보고서는 **훈련 부하 구조 지표(ACWR, Monotony, Strain)가 다음날 주관적 웰니스(Hooper Index)를 얼마나 잘 설명하는지** 통계적으로 평가한다. 단순 OLS 회귀로부터 출발하여, 선수 간 변동성을 포착하는 혼합효과모형으로 확장하고, 단일변수 대비 다중변수 모형의 추가 설명력을 정량적으로 비교한다.

**분석 프레임워크**: `Hooper_{t+1} ~ ACWR_t + Monotony_t + Strain_t + (1|athlete)`

---

## 2. 모형 설계

총 4개의 모형을 단계적으로 구축한다.

| 모형 | 유형 | 고정효과 | 랜덤효과 | 파라미터 수 |
|------|------|----------|----------|-------------|
| **M1** | OLS | ACWR | — | 2 |
| **M2** | Mixed Effects (LMM) | ACWR | (1\|athlete) | 3 |
| **M3** | Mixed Effects (LMM) | ACWR + Monotony | (1\|athlete) | 4 |
| **M4** | Mixed Effects (LMM) | ACWR + Monotony + Strain | (1\|athlete) | 5 |

### 모형 선택 근거

- **M1 → M2**: 선수 간 기저 피로도 차이를 무시하면 잔차 분산이 과대 추정되고, 고정효과 추정치에 편향이 발생할 수 있다. 랜덤 절편을 추가하여 이를 해소한다.
- **M2 → M3**: 부하의 "양"(ACWR)뿐 아니라 "패턴"(Monotony)이 피로에 기여하는지 검증한다. 단조로운 부하 패턴은 심리적·생리적 적응 실패와 관련될 수 있다 (Foster, 1998).
- **M3 → M4**: Strain(= 주간 총 부하 × Monotony)을 추가하여 부하의 절대적 크기와 패턴의 상호작용 효과를 포착한다.

---

## 3. 데이터

SoccerMon 데이터셋(Midoglu et al., 2024)을 사용하였다.

### 3.1 데이터 전처리 파이프라인

| 단계 | 결과 |
|------|------|
| 원본 로딩 (Wide → Long) | **36,550행**, 11열 |
| 팀 구성 | TeamA: 19,737 / TeamB: 16,813 |
| 활성 시즌 필터 | **25,529행** |
| 선수 필터 (부하 ≥ 60일 & 웰니스 ≥ 60일) | 50명 → **44명** |
| 필터 후 최종 | **24,596행**, 14열 |
| 날짜 범위 | 2020-01-09 ~ 2021-12-31 |

### 3.2 웰니스 구성요소 기술통계

| 변수 | n (유효) | 평균 | SD | 범위 | 결측률 |
|------|:--------:|:----:|:---:|:----:|:------:|
| fatigue | 16,618 | 3.03 | 0.63 | 1–5 | 32.4% |
| stress (원본) | 16,623 | 3.21 | 0.63 | 1–5 | 32.4% |
| stress_norm | 16,623 | 1.60 | 0.31 | 0.5–2.5 | 32.4% |
| soreness | 16,625 | 2.80 | 0.74 | 1–5 | 32.4% |
| sleep_quality | 16,620 | 3.27 | 0.72 | 1–5 | 32.4% |
| **Hooper Index** | **16,592** | **10.70** | **1.77** | **4.5–17.5** | **32.5%** |

### 3.3 부하 변수 기술통계

| 변수 | n | 평균 | SD | min | 25% | 50% | 75% | max | 결측률 |
|------|:---:|:----:|:---:|:---:|:---:|:---:|:---:|:---:|:------:|
| daily_load | 24,596 | 284.9 | 323.3 | 0 | 0 | 180 | 520 | 3,420 | 0% |
| acwr | 24,596 | 0.98 | 0.76 | 0.0 | 0.64 | 0.97 | 1.19 | 4.00 | 0% |
| atl | 24,596 | 281.7 | 181.3 | 0 | 141 | 306 | 414 | 966 | 0% |
| monotony | 24,596 | 1.05 | 0.69 | 0.0 | 0.62 | 1.09 | 1.45 | 8.75 | 0% |
| strain | 24,596 | 2,787 | 2,552 | 0 | 663 | 2,401 | 4,140 | 34,475 | 0% |

> 부하 변수(daily_load, acwr 등)는 SoccerMon에서 사전 산출되어 결측이 없다. 웰니스 변수는 선수 자기보고이므로 ~32.4% 결측이 존재한다.

### 3.4 모형 데이터셋 (이상치 제거 후)

| 파라미터 | 값 |
|----------|-----|
| 관측수 | **16,186** (lag-1 시차 적용 후) |
| 선수 수 | **44명** |
| Hooper Index (M±SD) | 10.70 ± 1.77 |
| ACWR (M±SD) | 1.170 ± 0.640 |
| Monotony (M±SD) | 1.324 ± 0.543 |
| Strain (M±SD) | 3,598.8 ± 2,428.7 |
| 그룹 크기 범위 | 73 – 629 (평균 367.9) |

### 3.5 Hooper Index 구성

```
Hooper Index = fatigue + stress_norm + soreness + sleep_quality
```

- **stress 정규화**: SoccerMon의 stress는 1–10 척도(다른 구성요소는 1–5)이므로, stress/2.0으로 정규화하여 척도를 통일하였다.
- 구성요소 중 하나라도 결측이면 해당 일의 Hooper Index는 결측 처리하였다.

---

## 4. 모형 비교표

> 아래 표는 SoccerMon 실제 데이터 기반 분석 결과이다.

| 지표 | M1: OLS (ACWR) | M2: Mixed (ACWR) | M3: Mixed (ACWR+Mono) | M4: Mixed (ACWR+Mono+Strain) |
|------|:-:|:-:|:-:|:-:|
| **AIC** | 64,508.9 | 54,750.9 | 54,751.1 | **54,736.7** |
| **BIC** | 64,524.3 | 54,773.9 | 54,781.9 | **54,775.1** |
| **MAE** | 1.348 | 0.986 | 0.986 | **0.985** |
| **RMSE** | 1.775 | 1.313 | 1.313 | **1.312** |
| **R²** | 0.000 | 0.453 | 0.453 | **0.454** |
| **Cohen's f²** | 0.000 | 0.828 | 0.828 | **0.830** |

### 고정효과 계수 상세

| 모형 | 변수 | 계수 | 표준오차 | z | p-value |
|------|------|:----:|:--------:|:---:|:-------:|
| M1 (OLS) | Intercept | 10.714 | 0.029 | 368.4 | < 0.001 |
| M1 (OLS) | ACWR | −0.012 | 0.022 | −0.54 | 0.593 |
| M2 (Mixed) | Intercept | 10.931 | 0.191 | 57.3 | < 0.001 |
| M2 (Mixed) | ACWR | **−0.090** | 0.016 | −5.48 | **< 0.001** |
| M3 (Mixed) | Intercept | 10.964 | 0.193 | 56.9 | < 0.001 |
| M3 (Mixed) | ACWR | **−0.089** | 0.016 | −5.40 | **< 0.001** |
| M3 (Mixed) | Monotony | −0.027 | 0.021 | −1.31 | 0.191 |
| M4 (Mixed) | Intercept | 10.880 | 0.193 | 56.3 | < 0.001 |
| M4 (Mixed) | ACWR | **−0.078** | 0.017 | −4.66 | **< 0.001** |
| M4 (Mixed) | Monotony | **+0.142** | 0.047 | 3.05 | **0.002** |
| M4 (Mixed) | Strain | **−0.00007** | 0.00002 | −4.07 | **< 0.001** |

### 랜덤효과

| 모형 | 랜덤 절편 분산 |
|------|:--------------:|
| M2 | 1.578 |
| M3 | 1.580 |
| M4 | 1.573 |

---

## 5. 결과 패턴 해석

### 5.1 랜덤 절편의 극적 효과 (M1 → M2)

M1(OLS)에서 M2(혼합효과)로의 전환에서 가장 극적인 개선이 관찰되었다:

- **AIC**: 64,509 → 54,751 (△ = −9,758)
- **R²**: 0.000 → 0.453
- **RMSE**: 1.775 → 1.313

OLS에서 ACWR 계수는 −0.012(p = 0.593)로 유의하지 않았으나, 혼합효과모형에서는 −0.090(p < 0.001)으로 고도로 유의하게 전환되었다. 이는 **Simpson's Paradox**의 전형적 사례로, 선수 간 기저 Hooper 수준의 이질성이 집단 수준 분석에서 ACWR 효과를 마스킹하고 있었음을 보여준다.

랜덤 절편 분산(1.578)은 잔차 분산(1.728) 대비 상당한 크기로, **ICC ≈ 0.48**이다. 이는 Hooper Index 전체 변동의 약 48%가 선수 간 차이에 기인함을 의미한다.

### 5.2 Monotony 추가의 제한적 효과 (M2 → M3)

M3에서 Monotony를 추가한 효과는 제한적이었다:

- Monotony 계수: −0.027 (p = 0.191, **비유의**)
- AIC/BIC, MAE, RMSE 모두 M2와 사실상 동일

이는 SoccerMon 데이터에서 Monotony가 ACWR을 통제한 후 Hooper Index에 대한 독립적 추가 설명력이 미미함을 시사한다.

### 5.3 Strain 추가의 의미 있는 개선 (M3 → M4)

M4에서 Strain을 추가하면 모형이 의미 있게 개선되었다:

- **AIC**: 54,751 → 54,737 (△ = −14)
- Strain 계수: −0.00007 (p < 0.001)
- Monotony 계수가 −0.027(ns) → **+0.142(p = 0.002)**로 부호 반전 및 유의화

이 부호 반전은 **억제변수(suppressor variable)** 효과를 시사한다. Monotony와 Strain은 수학적으로 관련되어 있으며(Strain = 주간 총부하 × Monotony), Strain을 통제함으로써 Monotony의 순수 효과(부하 패턴의 단조로움 자체가 Hooper를 증가시키는 경향)가 드러난 것으로 해석된다.

### 5.4 ACWR 계수 방향

모든 혼합효과모형(M2~M4)에서 ACWR 계수가 **음의 방향**으로 추정되었다 (−0.078 ~ −0.090). 이는 ACWR이 높을수록(급성 부하 비율 증가) 다음날 Hooper Index가 약간 감소하는 경향을 보여주며, 직관적 예상(ACWR↑ → 피로↑ → Hooper↑)과 반대 방향이다.

가능한 해석:
- ACWR 증가가 훈련 적응의 결과이며, 체력 상태가 좋을 때 부하를 높이는 경향이 있을 수 있음
- Hooper Index의 구성요소(fatigue, stress, soreness, sleep)가 부하 증가에 대해 비균질적으로 반응할 수 있음
- 효과 크기(0.078점/ACWR 1단위)가 실질적으로 매우 작아, 임상적 의의는 제한적임

### 5.5 Monotony 임계값 분석

Foster (1998)의 Monotony > 2.0 임계값에 의한 집단 비교 결과:

| 집단 | n | Hooper 평균 | SD |
|------|:---:|:-----------:|:---:|
| Monotony ≤ 2.0 | 14,798 | 10.70 | 1.77 |
| Monotony > 2.0 | 1,388 | 10.67 | 1.81 |

- Welch t = 0.608, p = **0.543**, Cohen's d = −0.017
- **통계적으로도 실질적으로도 유의한 차이가 없다.** 이분법적 Monotony 임계값의 유용성은 본 데이터에서 지지되지 않았다.

---

## 6. 다중 시차 분석

ACWR(t)과 Hooper(t+k)의 상관을 k = 0~7일 시차에 걸쳐 분석하였다:

| 시차 (일) | Pearson r | p-value | n |
|:---------:|:---------:|:-------:|:---:|
| 0 | +0.005 | 0.551 | 16,299 |
| 1 | −0.004 | 0.593 | 16,186 |
| 2 | +0.008 | 0.293 | 16,086 |
| 3 | +0.014 | 0.071 | 15,996 |
| 4 | +0.016 | *0.045* | 15,902 |
| 5 | +0.020 | *0.012* | 15,826 |
| 6 | +0.024 | **0.003** | 15,750 |
| **7** | **+0.027** | **< 0.001** | 15,687 |

최적 시차는 **Lag 7일**(|r| = 0.027)로, 1주 뒤 Hooper Index와의 상관이 가장 높았다. 다만, 모든 시차에서 상관 계수의 절대값이 0.03 미만으로, ACWR과 Hooper 간의 집단 수준 시차 관계는 매우 약한 것으로 관찰된다.

---

## 7. LOSO 교차검증

M3(ACWR + Monotony)에 대해 Leave-One-Subject-Out 교차검증을 수행하였다:

| 지표 | 값 |
|------|:---:|
| 평가 fold 수 | 44/44 (100% 성공) |
| **평균 MAE** | **1.448** (SD = 0.566) |
| **평균 RMSE** | **1.764** (SD = 0.609) |
| MAE 범위 | 0.585 – 2.906 |
| RMSE 범위 | 0.756 – 3.444 |
| 총 테스트 관측수 | 16,186 |

**선수별 LOSO 결과 (극단 사례)**:

| 선수 | n | MAE | RMSE | 특성 |
|------|:---:|:---:|:----:|------|
| TeamA_2d44 (최우수) | 554 | **0.585** | 0.756 | 집단 평균에 가까운 안정적 패턴 |
| TeamB_7895 | 538 | 0.668 | 0.961 | — |
| TeamB_48bf | 530 | 0.720 | 0.952 | — |
| TeamA_0362 (최저) | 192 | **2.906** | 3.444 | 집단 평균과 크게 괴리된 개인 패턴 |

LOSO MAE(1.448)가 전체 데이터 MAE(0.986)보다 47% 높은 것은 고정효과만으로 새로운 선수를 예측하는 한계를 반영한다. 랜덤 절편(개인별 기저 Hooper)이 예측의 핵심 요소이며, 새로운 선수에 대해서는 이 정보가 부재하기 때문이다.

선수 간 LOSO MAE의 큰 편차(0.585~2.906)는 일부 선수의 Hooper 패턴이 집단 평균과 크게 다름을 시사하며, 이는 **개인화된 모형(warm-start)** 접근의 필요성을 강조한다.

---

## 8. 한계 및 향후 과제

### 8.1 현재 분석의 한계

| 항목 | 설명 |
|------|------|
| **시간적 자기상관** | Hooper Index의 잔차에 시간적 자기상관이 존재할 수 있으나, 현재 모형은 이를 다루지 않음 |
| **비선형 효과** | ACWR과 Hooper 간의 관계가 비선형(U자형 등)일 수 있음 (Gabbett, 2016) |
| **교란변수 미포함** | 경기일, 이동(원정), 부상 이력 등 Hooper에 영향을 줄 수 있는 변수 미포함 |
| **stress 척도 정규화** | stress(1–10)를 단순 나누기(/2)로 1–5 척도에 맞췄으나, 비선형 매핑이 더 적절할 수 있음 |
| **효과 크기** | ACWR 계수(−0.078~−0.090)가 매우 작아, 임상적/실무적 유의성은 제한적 |
| **ACWR 산출** | SoccerMon 제공 ACWR을 그대로 사용하였으며, Rolling/EWMA 방식 비교는 미수행 |

### 8.2 향후 과제

1. **EWMA ACWR 산출 및 비교**: 원시 daily_load에서 직접 EWMA ACWR을 산출하여 Rolling 방식과 비교한다.
2. **AR(1) 상관 구조**: `statsmodels`의 GEE 또는 시계열 혼합효과모형으로 잔차 자기상관을 다룬다.
3. **랜덤 기울기 모형**: `(1 + ACWR|athlete)` 구조로 확장하여 개인별 ACWR 반응 이질성을 탐색한다.
4. **비선형 모형**: GAM(Generalized Additive Model) 또는 스플라인 기반 확장을 통해 비선형 관계를 탐색한다.
5. **교란변수 포함**: 경기일(match day) 더미, 요일 효과, 이전 Hooper(자기상관) 등을 공변량으로 추가한다.
6. **구성요소별 분석**: Hooper Index의 하위 구성요소(fatigue, soreness, sleep, stress)를 개별 종속변수로 분석하여 ACWR이 각 구성요소에 미치는 차별적 영향을 탐색한다.
7. **팀 간 비교**: TeamA와 TeamB 간 부하-웰니스 관계의 차이를 체계적으로 비교한다.

---

## 9. 시각화

노트북 실행으로 생성된 시각화 파일 전체 목록:

| 파일 | 내용 | 크기 |
|------|------|------|
| `track_B_weekly_load_pattern.png` | 요일별 평균 훈련 부하 패턴 | 28.0 KB |
| `track_B_acwr_hooper_scatter.png` | ACWR(t) vs Hooper(t+1) 산점도 | 221.9 KB |
| `track_B_monotony_threshold.png` | Monotony 2.0 임계값 기준 Hooper 비교 | 33.5 KB |
| `track_B_missing_heatmap.png` | 선수별-월별 결측 히트맵 | 126.0 KB |
| `track_B_load_distribution.png` | 부하/웰니스 변수 분포 (히스토그램) | 137.5 KB |
| `track_B_timeseries_sample.png` | 샘플 선수 시계열 (부하 + Hooper + ACWR) | 608.1 KB |
| `track_B_model_comparison.png` | 모형별 AIC/BIC/MAE/RMSE/R²/f² 비교 | 98.8 KB |
| `track_B_lag_profile.png` | 시차별(0~7일) 상관 프로파일 | 41.2 KB |

저장 경로: `reports/figures/`

---

## 10. 참고문헌

- Bourdon, P. C., et al. (2017). Monitoring athlete training loads: Consensus statement. *International Journal of Sports Physiology and Performance*, 12(S2), S2-161.
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.
- Foster, C. (1998). Monitoring training in athletes with reference to overtraining syndrome. *Medicine & Science in Sports & Exercise*, 30(7), 1164-1168.
- Gabbett, T. J. (2016). The training-injury prevention paradox. *British Journal of Sports Medicine*, 50(5), 273-280.
- Hooper, S. L., & Mackinnon, L. T. (1995). Monitoring overtraining in athletes. *Sports Medicine*, 20(5), 321-327.
- Midoglu, C., et al. (2024). SoccerMon: A Multimodal Soccer Dataset. *Scientific Data*. DOI: 10.5281/zenodo.10033832.
- Williams, S., et al. (2017). Better way to determine the acute:chronic workload ratio? *British Journal of Sports Medicine*, 51(3), 209-210.

---

*본 보고서는 `notebooks/track_B_real.ipynb` 및 `notebooks/run_track_B.py` 실행 결과와 연동된다.*
*노트북: `notebooks/track_B_real.ipynb` (44셀, 실행 완료)*
*산출 코드: `notebooks/run_track_B.py` (섹션 9~12)*
*시각화: `reports/figures/track_B_*.png` (8개 파일)*
*처리 데이터: `data/processed/track_B_merged.csv` (24,596행, 44선수)*
*지표 모듈: `src/metrics/acwr.py`, `src/metrics/monotony_strain.py`*
