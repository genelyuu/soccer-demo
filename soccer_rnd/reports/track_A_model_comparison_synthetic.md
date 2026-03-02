# 트랙 A: 합성 데이터 기반 모형 비교 보고서

> **작성**: stats-lead@soccer-rnd
> **최종 갱신**: 2026-02-11
> **재현 환경**: Python 3, numpy seed=42, statsmodels mixedlm (ML 추정)
> **데이터**: 합성 데이터 (8명 피험자, 90일, 파이프라인 검증 목적)
> **산출 코드**: `notebooks/run_synthetic_analysis.py`

---

## 1. 분석 목적

본 보고서는 **ACWR(Acute:Chronic Workload Ratio)이 다음 날의 HRV(ln_rMSSD)에 미치는 영향**을 혼합효과 회귀모형으로 분석하는 파이프라인의 정합성을 검증하기 위해, 알려진 참값 파라미터로 생성된 합성 데이터에 대해 세 가지 모형을 비교한다.

핵심 질문:

1. 모형이 합성 데이터의 참값 계수(beta_1 = -0.5)를 적절히 복원하는가?
2. 피험자별 랜덤 절편을 포함하면 OLS 대비 모형 적합도가 향상되는가?
3. Rolling ACWR과 EWMA ACWR 중 어느 산출 방식이 더 적합한가?

본 분석은 **파이프라인 검증 목적**으로 수행되었으며, 합성 데이터의 결과를 실제 생리학적 현상으로 직접 해석할 수 없다.

---

## 2. 합성 데이터 설계

### 생성 모델

```
ln_rmssd_next(t) = beta_0 + beta_1 * acwr_rolling(t) + u_j + epsilon(t)
```

### 파라미터 표

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| 피험자 수 | 8명 | subject_id: S01–S08 |
| 관측 기간 | 90일 | daily_load 기반 |
| 분석 관측수 | 504 | 워밍업 기간(28일) 제거 후 |
| daily_load | 평균 400 AU, SD 150 | 주말(토/일) 0.5배 |
| beta_0 (절편) | 4.0 | 기저 ln_rMSSD 수준 |
| beta_1 (ACWR 기울기) | **-0.5** | ACWR 1단위 증가 시 ln_rMSSD 감소 |
| sigma_subject | 0.3 | 피험자 간 랜덤 절편 SD |
| sigma_noise | 0.4 | 관측 노이즈 SD |
| seed | 42 | 재현성 보장 |

### 기술통계량

| 변수 | 평균 | SD | 최솟값 | 최댓값 |
|------|:----:|:---:|:-----:|:-----:|
| daily_load (AU) | 345.1 | 156.9 | 44.5 | 786.0 |
| acwr_rolling | 1.005 | 0.127 | 0.585 | 1.351 |
| acwr_ewma | 0.995 | 0.112 | 0.683 | 1.278 |
| ln_rmssd_next | 3.669 | 0.438 | 2.381 | 4.942 |

종속변수(ln_rmssd_next)는 **Rolling ACWR을 기준으로 생성**되었으므로, Rolling ACWR이 EWMA ACWR보다 설명력이 약간 높을 것으로 기대된다.

---

## 3. 모형 설계

| 모형 | 유형 | 고정효과 | 랜덤효과 | 추정 방법 |
|------|------|----------|----------|-----------|
| 모형 1 | OLS | ACWR (Rolling) | -- | 최소자승법 |
| 모형 2 | Mixed Effects (LMM) | ACWR (Rolling) | (1\|subject_id) | ML |
| 모형 3 | Mixed Effects (LMM) | ACWR (EWMA) | (1\|subject_id) | ML |

### 모형 선택 근거

- **모형 1 (OLS)**: 반복 측정 구조를 무시하는 베이스라인. 피험자 내 상관을 고려하지 않으므로 표준오차가 부적절하게 추정될 수 있다.
- **모형 2 (Mixed Rolling)**: 피험자별 랜덤 절편으로 개인 간 기저 HRV 차이를 설명한다. 데이터 생성 구조와 일치하는 모형이다.
- **모형 3 (Mixed EWMA)**: EWMA 방식의 ACWR을 투입하여, Rolling 방식과의 상대적 적합도를 비교한다. EWMA는 최근 부하에 더 높은 가중치를 부여한다 (Williams et al., 2017).

### AIC/BIC 산출

혼합효과모형의 AIC/BIC는 **ML(Maximum Likelihood) 추정**으로 산출하였다. REML 추정 시 statsmodels가 AIC/BIC를 NaN으로 반환하는 문제를 방지하기 위함이다. 모형 간 고정효과 구조가 다르므로 ML 기반 비교가 적절하다 (Zuur et al., 2009).

---

## 4. 모형 비교표

| 지표 | 모형 1: OLS (Rolling) | 모형 2: Mixed (Rolling) | 모형 3: Mixed (EWMA) |
|------|:--------------------:|:----------------------:|:-------------------:|
| **AIC** | 593.05 | **521.45** | 523.43 |
| **BIC** | 601.49 | **538.34** | 540.32 |
| **MAE** | 0.3465 | **0.3109** | 0.3119 |
| **RMSE** | 0.4341 | **0.3910** | 0.3921 |
| **R²** | 0.0172 | **0.2024** | 0.1981 |
| **Cohen's f²** | 0.0175 | **0.2537** | 0.2471 |
| **ACWR 계수** | -0.4548 | **-0.5212** | -0.5328 |
| **절편** | 4.1257 | 4.1924 | 4.1991 |
| **p-value** | 3.16e-03 | **2.04e-04** | 8.39e-04 |
| **RE 분산(절편)** | -- | 0.0482 | 0.0314 |

> 산출 코드: `notebooks/run_synthetic_analysis.py`

### 비교 기준 설명

| 지표 | 설명 | 선호 방향 |
|------|------|----------|
| AIC | 모형 복잡도와 적합도의 균형 (Akaike, 1974) | 낮을수록 양호 |
| BIC | AIC보다 파라미터 수에 더 엄격한 페널티 (Schwarz, 1978) | 낮을수록 양호 |
| MAE | 예측 오차의 절대값 평균 | 낮을수록 양호 |
| RMSE | 큰 오차에 민감한 예측 정확도 | 낮을수록 양호 |
| Cohen's f² | 고정효과의 효과크기. 0.02(소), 0.15(중), 0.35(대) (Cohen, 1988) | 클수록 효과 큼 |

---

## 5. 결과 해석

### 5.1 계수 방향 확인 (참값과 비교)

세 모형 모두에서 ACWR 계수가 **음의 방향**으로 추정되어, 참값(beta_1 = -0.5)과 일치하는 방향이 확인되었다.

| 모형 | 추정 계수 | 참값 | 편차 |
|------|:---------:|:----:|:----:|
| OLS (Rolling) | -0.4548 | -0.5 | +0.045 (과소추정) |
| Mixed (Rolling) | -0.5212 | -0.5 | -0.021 (근접) |
| Mixed (EWMA) | -0.5328 | -0.5 | -0.033 |

혼합효과모형(모형 2)의 추정값(-0.5212)이 OLS(-0.4548)보다 참값에 더 가까운 것으로 관찰된다. OLS에서 계수가 과소추정된 것은 피험자 간 변동이 잔차에 혼입되어 기울기 추정에 편향이 발생했기 때문으로 해석된다.

절편 추정 역시 유사한 패턴을 보인다: OLS(4.126) < Mixed Rolling(4.192) < 참값(4.0). 랜덤 절편이 피험자 간 기저값 차이를 분리하면서 절편 추정이 참값에 수렴하는 경향이 관찰된다.

### 5.2 혼합효과모형 vs OLS

혼합효과모형(모형 2, 3)은 OLS(모형 1) 대비 모든 적합도 지표에서 우수하였다:

- **AIC**: 593.05 → 521.45 (delta = -71.6, 대폭 개선)
- **BIC**: 601.49 → 538.34 (delta = -63.2)
- **R²**: 0.0172 → 0.2024 (약 12배 증가)
- **RMSE**: 0.4341 → 0.3910 (9.9% 감소)

OLS의 R²가 0.017에 불과한 것은, 피험자 간 기저 HRV 수준의 변동(sigma_subject = 0.3)이 잔차에 포함되어 전체 설명력을 희석시키기 때문이다. 랜덤 절편이 이 변동을 흡수하면서 R²가 0.202로 상승하였다. 이는 반복 측정 데이터에서 개인 간 변동을 고려하지 않으면 효과를 과소평가할 수 있음을 시사한다.

랜덤 절편 분산(0.0482)은 참값 분산(0.09 = 0.3^2)보다 낮게 추정되었는데, 이는 8명이라는 소규모 표본에서 분산 추정이 불안정할 수 있음을 반영한다.

### 5.3 Rolling vs EWMA

| 비교 항목 | Mixed (Rolling) | Mixed (EWMA) | 차이 |
|-----------|:---------------:|:------------:|:----:|
| AIC | **521.45** | 523.43 | +1.98 |
| BIC | **538.34** | 540.32 | +1.98 |
| R² | **0.2024** | 0.1981 | -0.004 |
| RMSE | **0.3910** | 0.3921 | +0.001 |
| Cohen's f² | **0.2537** | 0.2471 | -0.007 |

Rolling ACWR 기반 모형(모형 2)이 EWMA 기반 모형(모형 3)보다 근소하게 우수한 적합도를 보였다. 이는 합성 데이터가 Rolling ACWR을 기준으로 생성되었기 때문에 예상되는 결과이다. 다만, AIC 차이(1.98)는 매우 작으며, 두 모형 간 실질적 차이는 미미한 것으로 판단된다.

EWMA ACWR 계수(-0.5328)가 Rolling ACWR 계수(-0.5212)보다 절대값이 약간 큰 것은, EWMA의 분산(0.112)이 Rolling의 분산(0.127)보다 작아 단위 변화당 효과가 증폭되는 스케일링 효과로 해석된다.

### 5.4 효과크기 해석

| 모형 | Cohen's f² | 해석 |
|------|:----------:|:----:|
| OLS (Rolling) | 0.018 | 소(small) |
| Mixed (Rolling) | 0.254 | **중(medium)** |
| Mixed (EWMA) | 0.247 | **중(medium)** |

OLS에서는 효과크기가 소(small) 수준이지만, 혼합효과모형에서는 중(medium) 수준으로 상승하였다. 이는 랜덤 절편이 잔차 분산을 감소시킴으로써 고정효과의 상대적 설명력이 증가한 것에 기인한다. 참값 파라미터(beta_1 = -0.5, sigma_noise = 0.4)를 고려하면 중간 효과크기는 합리적인 수준이다.

---

## 6. 실제 데이터와의 비교 논의

### 실제 데이터 분석 결과 요약 (Track A: PhysioNet ACTES)

| 항목 | 실제 데이터 | 합성 데이터 |
|------|:-----------:|:-----------:|
| 피험자 수 | 18명 | 8명 |
| 분석 구조 | 파워(W) → rMSSD (단일 세션) | ACWR → ln_rMSSD (종단) |
| 파워/ACWR 계수 | **-0.016** (p < 0.001) | -0.521 (p < 0.001) |
| OLS AIC | 293.9 | 593.05 |
| Mixed(절편) AIC | 296.3 | 521.45 |
| MAE (OLS) | 1.64 | 0.347 |
| MAE (Mixed) | 1.41 | 0.311 |

### 주요 차이점 서술

1. **분석 구조의 근본적 차이**: 실제 데이터(PhysioNet ACTES)는 단일 세션 점증 부하 검사에서 파워(W)와 rMSSD의 관계를 분석한 반면, 합성 데이터는 다중 일간 시계열에서 ACWR과 ln_rMSSD의 시차 관계를 모형화하였다. 따라서 계수의 절대값을 직접 비교하는 것은 적절하지 않다.

2. **혼합효과의 상대적 이점**: 실제 데이터에서는 OLS의 AIC(293.9)가 Mixed(296.3)보다 낮아 혼합효과의 이점이 제한적이었으나, 합성 데이터에서는 Mixed(521.45)가 OLS(593.05)를 대폭 능가하였다. 이는 실제 데이터의 관측 단위가 피험자당 3~4개로 극히 적어 랜덤효과 추정의 이점이 제한적이었던 반면, 합성 데이터는 피험자당 63개 관측으로 충분한 정보가 있었기 때문이다.

3. **효과 방향의 일관성**: 실제 데이터(power_mean coef = -0.016)와 합성 데이터(ACWR coef = -0.521) 모두에서 부하 증가 시 HRV가 감소하는 방향이 관찰되었다. 이는 운동 강도 증가에 따른 부교감신경 철수(vagal withdrawal)라는 공통 메커니즘과 일관된 경향이다.

4. **효과 크기**: 합성 데이터의 ACWR 계수(-0.521)는 참값(-0.5)을 반영하여 상당히 크게 설정되었으나, 실제 데이터의 계수(-0.016)는 이보다 훨씬 작다. 실제 생리학적 관계에서는 ACWR 외에도 다수의 교란변수가 존재하며, 단일 변수의 순수 효과는 작을 수 있다.

---

## 7. 한계 및 향후 과제

### 7.1 현재 분석의 한계

| 항목 | 설명 |
|------|------|
| **합성 데이터** | 알려진 참값으로 생성된 데이터이므로, 결과의 생리학적 해석에 직접 적용할 수 없다 |
| **선형 가정** | 실제 ACWR-HRV 관계는 비선형(U자형 등)일 수 있다 (Gabbett, 2016) |
| **시간적 자기상관** | 일별 반복 측정에서의 시간적 자기상관을 모형에 포함하지 않았다 |
| **소규모 피험자** | 8명의 피험자는 랜덤효과 분산 추정에 제한적이다. 수렴 경고가 발생하였다 |
| **단일 예측변수** | ACWR 외 교란변수(수면, 영양, 심리적 스트레스 등)가 모형에 미포함 |
| **데이터 생성 편향** | Rolling ACWR 기준으로 종속변수를 생성하여 Rolling 모형에 유리한 구조이다 |

### 7.2 향후 과제

1. **실제 데이터 적용**: PhysioNet ACTES 등 다중 일간 HRV 데이터에 동일 파이프라인을 적용하여 실증적 결과를 확보한다.
2. **AR(1) 상관 구조**: 잔차의 시간적 자기상관을 다루기 위해 AR(1) 상관 구조를 도입한다.
3. **비선형 모형**: GAM(Generalized Additive Model) 등으로 ACWR-HRV 비선형 관계를 탐색한다.
4. **랜덤 기울기**: `(1 + ACWR|subject)` 모형으로 확장하여 개인별 ACWR 반응 이질성을 분석한다.
5. **교차검증**: LOSO(Leave-One-Subject-Out) CV를 통해 모형의 일반화 가능성을 평가한다.
6. **더 큰 표본**: 피험자 수를 20명 이상으로 확대한 합성 데이터 시뮬레이션을 수행하여 분산 추정의 안정성을 확인한다.

---

## 참고문헌

- Akaike, H. (1974). A new look at the statistical model identification. *IEEE Transactions on Automatic Control*, 19(6), 716-723.
- Buchheit, M. (2014). Monitoring training status with HR measures. *International Journal of Sports Physiology and Performance*, 9(5), 883-895.
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.
- Gabbett, T. J. (2016). The training-injury prevention paradox. *British Journal of Sports Medicine*, 50(5), 273-280.
- Plews, D. J., et al. (2013). Training adaptation and heart rate variability in elite endurance athletes. *International Journal of Sports Physiology and Performance*, 8(6), 688-694.
- Schwarz, G. (1978). Estimating the dimension of a model. *The Annals of Statistics*, 6(2), 461-464.
- Williams, S., et al. (2017). Better way to determine the acute:chronic workload ratio? *British Journal of Sports Medicine*, 51(3), 209-210.
- Zuur, A. F., et al. (2009). *Mixed Effects Models and Extensions in Ecology with R*. Springer.

---

*본 보고서는 `notebooks/run_synthetic_analysis.py` 실행 결과와 연동된다.*
*산출 코드 위치: `notebooks/run_synthetic_analysis.py` (Track A 섹션)*
*지표 모듈: `src/metrics/acwr.py`, `src/metrics/hrv_features.py`*
*재현: `cd notebooks && python run_synthetic_analysis.py` (seed=42)*
