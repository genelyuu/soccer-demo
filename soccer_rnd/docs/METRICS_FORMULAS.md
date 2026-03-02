# 지표 정의서 (Metrics & Formulas Specification)

> 본 문서는 soccer_rnd 프로젝트에서 사용하는 모든 훈련 부하·HRV·웰니스 지표의
> 표준 수식, 파라미터, 예외 처리 규칙을 정의한다.
> 모든 수식에는 근거 문헌을 인용하며, 인용 번호는 `REFERENCES.md`의 `[Ref #N]`에 대응한다.

---

## 목차

1. [sRPE (Session RPE)](#1-srpe-session-rpe)
2. [ATL (Acute Training Load)](#2-atl-acute-training-load)
3. [CTL (Chronic Training Load)](#3-ctl-chronic-training-load)
4. [ACWR (Acute:Chronic Workload Ratio)](#4-acwr-acutechronic-workload-ratio)
5. [Monotony](#5-monotony)
6. [Strain](#6-strain)
7. [Hooper Index](#7-hooper-index)
8. [HRV 지표 (rMSSD, SDNN)](#8-hrv-지표-rmssd-sdnn)

---

## 1. sRPE (Session RPE)

### 정의

선수가 체감하는 훈련 강도(RPE)에 훈련 시간(분)을 곱하여 산출하는 내적 부하(internal load) 지표.

> 근거: Foster (1998) [Ref #1], Foster et al. (2001) [Ref #2]

### 수식

```
sRPE = RPE × Duration (min)
```

| 파라미터 | 설명 | 단위 |
|----------|------|------|
| RPE | Borg CR-10 스케일 (0–10) 또는 수정 Borg 스케일 | 무차원 |
| Duration | 웜업·쿨다운 포함 세션 총 시간 | 분 (min) |
| sRPE | 세션 부하 | AU (arbitrary units) |

### 규칙

- **RPE 수집 시점**: 세션 종료 후 **30분 이내** 수집을 권장한다 (Foster et al., 2001 [Ref #2]).
- **RPE 스케일**: 본 프로젝트는 **Borg CR-10 (0–10)** 스케일을 표준으로 사용한다 [Ref #4].
- **결측 처리**: RPE 또는 Duration 중 하나라도 결측이면 해당 세션의 sRPE = `NULL` (결측). 0으로 대체하지 않는다.
- **휴식일**: 훈련이 없는 날은 `sRPE = 0`으로 기록한다 (세션 자체가 없으므로 RPE=0, Duration=0).
- **복수 세션**: 하루에 2회 이상 훈련 시, 각 세션의 sRPE를 합산하여 **일일 총 부하(daily load)**로 사용한다.

---

## 2. ATL (Acute Training Load)

### 정의

최근 단기간(통상 7일)의 훈련 부하 평균. "피로(fatigue)" 또는 단기 부하 수준을 반영한다.

> 근거: Banister et al. (1975) [Ref #15], Hulin et al. (2014) [Ref #7]

### 2.1 Rolling Average 방식

```
ATL_rolling(t) = (1/n) × Σ(i=0 to n-1) Load(t-i)
```

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| n | **7** (일) | 급성 부하 윈도우 크기 |
| Load(t) | — | t일의 일일 훈련 부하 (sRPE 등) |

### 2.2 EWMA 방식

```
ATL_ewma(t) = Load(t) × α_a + ATL_ewma(t-1) × (1 - α_a)
```

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| N_a | **7** | 급성 부하 기간 (일) |
| α_a | **2 / (N_a + 1) = 0.25** | 감쇠 계수 (decay factor) |

> 근거: Williams et al. (2017) [Ref #10], Murray et al. (2017) [Ref #11]
> α = 2/(N+1)은 금융공학의 표준 EWMA 정의를 스포츠과학에 적용한 것이다.

### 초기값 처리

- **EWMA 초기값**: `ATL_ewma(1) = Load(1)` — 첫째 날의 부하값을 초기값으로 사용한다.
- **Rolling Average Warm-up**: 최소 **n일(7일)** 이상의 데이터가 축적되어야 유효한 값으로 간주한다. 그 이전 구간은 `NULL` 또는 해당 시점까지의 누적 평균(expanding mean)으로 처리할 수 있다.

### 결측 처리

- 특정 일자의 Load 값이 결측(`NULL`)인 경우, 해당 일은 **윈도우 계산에서 제외**하고 유효 일수로 나눈다 (rolling). EWMA의 경우 전일 값을 유지한다: `ATL_ewma(t) = ATL_ewma(t-1)`.
- 연속 결측이 **3일 이상**이면 해당 구간의 ATL을 `NULL`로 표기한다.

---

## 3. CTL (Chronic Training Load)

### 정의

장기간(통상 28일)의 훈련 부하 평균. "체력(fitness)" 또는 만성적 부하 적응 수준을 반영한다.

> 근거: Banister et al. (1975) [Ref #15], Banister & Calvert (1980) [Ref #16]

### 3.1 Rolling Average 방식

```
CTL_rolling(t) = (1/n) × Σ(i=0 to n-1) Load(t-i)
```

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| n | **28** (일) | 만성 부하 윈도우 크기 |

### 3.2 EWMA 방식

```
CTL_ewma(t) = Load(t) × α_c + CTL_ewma(t-1) × (1 - α_c)
```

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| N_c | **28** | 만성 부하 기간 (일) |
| α_c | **2 / (N_c + 1) = 2/29 ≈ 0.0690** | 감쇠 계수 (decay factor) |

### 초기값 처리

- **EWMA 초기값**: `CTL_ewma(1) = Load(1)`.
- **Rolling Average Warm-up**: 최소 **28일** 이상 데이터 축적 후 유효. 이전 구간은 expanding mean 또는 `NULL`.

### 결측 처리

- ATL과 동일한 규칙을 적용한다.
- 연속 결측이 **7일 이상**이면 CTL을 `NULL`로 표기한다.

---

## 4. ACWR (Acute:Chronic Workload Ratio)

### 정의

급성 부하 대 만성 부하의 비율. 부상 위험도 평가에 활용된다.

> 근거: Hulin et al. (2014) [Ref #7], Blanch & Gabbett (2016) [Ref #8], Gabbett (2016) [Ref #9]

### 4.1 Rolling Average 방식 (Coupled)

```
ACWR_rolling(t) = ATL_rolling(t) / CTL_rolling(t)
```

> **주의**: 이 방식은 ATL 기간(7일)이 CTL 기간(28일)에 포함되어 **수학적 커플링(mathematical coupling)** 문제가 발생한다 (Lolli et al., 2019 [Ref #12]).

### 4.2 Rolling Average 방식 (Uncoupled)

```
ACWR_uncoupled(t) = ATL_rolling(t) / CTL_rolling(t - n_a)
```

여기서 `CTL_rolling(t - n_a)`는 급성 기간을 **제외한** 이전 21일(day t-28 ~ t-8)의 평균이다.

> 이 방식은 커플링 문제를 완화하지만, 근본적 한계는 여전히 존재한다 (Impellizzeri et al., 2020 [Ref #13]).

### 4.3 EWMA 방식

```
ACWR_ewma(t) = ATL_ewma(t) / CTL_ewma(t)
```

> 근거: Williams et al. (2017) [Ref #10], Murray et al. (2017) [Ref #11]

### Rolling Average vs EWMA 비교

| 항목 | Rolling Average | EWMA |
|------|----------------|------|
| **가중치** | 윈도우 내 모든 날에 동일 가중치 | 최근 데이터에 더 높은 가중치 (지수 감쇠) |
| **민감도** | 급격한 부하 변화에 덜 민감 | 급격한 부하 변화에 더 민감 [Ref #11] |
| **수학적 커플링** | Coupled 방식에서 발생 [Ref #12] | 구조적으로 발생하지 않음 |
| **윈도우 경계** | 윈도우 밖 데이터 즉시 탈락 (cliff effect) | 점진적 감쇠, 경계 효과 없음 |
| **부상 예측력** | 보통 | 더 높은 민감도 보고 [Ref #11] |
| **해석 용이성** | 직관적, 이해 쉬움 | 가중치 구조 설명 필요 |
| **권장** | 탐색적 분석, 기초 모니터링 | **본 프로젝트 기본 방식** |

### CTL = 0 일 때 처리 (Division by Zero)

```
if CTL(t) == 0:
    ACWR(t) = NULL   # 정의 불가 — 만성 부하가 0이면 비율 산출이 무의미
```

| 시나리오 | 처리 |
|----------|------|
| CTL = 0 이고 ATL = 0 | ACWR = `NULL` (훈련 이력 없음) |
| CTL = 0 이고 ATL > 0 | ACWR = `NULL` (비정상 상태; 경고 로그 출력) |
| CTL > 0 이고 ATL = 0 | ACWR = 0.0 (완전 휴식) |

### Warm-up 기간

- **최소 데이터**: ACWR 산출을 위해 최소 **28일**의 유효 데이터가 필요하다 (CTL의 윈도우 크기).
- **EWMA 방식**: 초기 **21일** 동안은 CTL_ewma 값이 불안정하므로, 이 기간의 ACWR은 `NULL`로 처리하거나 별도 표기한다.
- **권장 warm-up**: 프리시즌 시작 후 **최소 21일** 경과 후부터 ACWR을 의사결정에 활용한다.

### 위험 구간 (참고)

| ACWR 범위 | 해석 | 근거 |
|-----------|------|------|
| < 0.80 | 훈련 부족 (undertraining) | Blanch & Gabbett (2016) [Ref #8] |
| 0.80 – 1.30 | 최적 구간 (sweet spot) | Gabbett (2016) [Ref #9] |
| > 1.50 | 고위험 구간 (danger zone) | Hulin et al. (2014) [Ref #7] |

> **주의**: 위 임계값은 종목·포지션·개인 특성에 따라 달라질 수 있다.
> ACWR 단독 사용의 한계에 대한 비판도 존재한다 (Impellizzeri et al., 2020 [Ref #13]; Wang et al., 2020 [Ref #14]).

---

## 5. Monotony

### 정의

7일간 일일 훈련 부하의 평균을 표준편차로 나눈 값. 훈련의 단조로움(변동 부족)을 정량화한다.

> 근거: Foster (1998) [Ref #1], [Ref #5]

### 수식

```
Monotony(t) = mean(Load(t-6), ..., Load(t)) / sd(Load(t-6), ..., Load(t))
```

| 파라미터 | 값 | 설명 |
|----------|-----|------|
| 윈도우 | **7일** (고정) | Foster 원 정의 |
| mean | 7일간 일일 부하의 산술 평균 | |
| sd | 7일간 일일 부하의 **표본** 표준편차 (N-1 방식) | |

### 규칙

- **sd = 0 처리**: 7일간 부하가 완전히 동일하면 sd = 0이 되어 Monotony = ∞. 이 경우:
  - `Monotony = NULL` 또는 사전 정의된 **상한값(cap)**으로 처리한다.
  - 권장 상한값: `10.0` (실무적 최대치).
- **휴식일 포함**: 7일 윈도우에 훈련이 없는 날(Load=0)도 포함한다 (Foster 원 정의에 따름).
- **최소 데이터**: 7일 윈도우 내 결측이 **2일 이상**이면 Monotony = `NULL`.
- **해석**: Monotony > 2.0이면 훈련 변동성이 부족하여 과훈련/상병 위험 증가 (Foster, 1998 [Ref #5]).

---

## 6. Strain

### 정의

주간 총 훈련 부하에 Monotony를 곱한 값. 부하의 절대량과 단조로움을 동시에 반영한다.

> 근거: Foster (1998) [Ref #1], [Ref #5]

### 수식

```
Strain(t) = WeeklyLoad(t) × Monotony(t)
```

여기서:
```
WeeklyLoad(t) = Σ(i=0 to 6) Load(t-i)
```

| 파라미터 | 설명 |
|----------|------|
| WeeklyLoad | 7일간 일일 부하의 합계 |
| Monotony | 위 섹션 5의 Monotony 값 |
| Strain | AU² (arbitrary units squared) |

### 규칙

- Monotony = `NULL`이면 Strain = `NULL`.
- **해석**: 높은 Strain은 높은 부하 + 높은 단조로움을 의미하며, 상병(illness) 발생률과 양의 상관관계를 보인다 (Brink et al., 2010 [Ref #6]).
- WeeklyLoad와 Monotony는 **동일한 7일 윈도우**에서 산출한다.

---

## 7. Hooper Index

### 정의

선수의 주관적 회복/피로 상태를 4개 항목으로 평가하는 설문 지표.

> 근거: Hooper & Mackinnon (1995) [Ref #18], Hooper et al. (1995) [Ref #19]

### 수식

```
Hooper Index = Fatigue + Stress + DOMS + Sleep Quality
```

| 항목 | 스케일 | 설명 |
|------|--------|------|
| Fatigue | 1–7 | 1 = 매우 낮음, 7 = 매우 높음 |
| Stress | 1–7 | 1 = 매우 낮음, 7 = 매우 높음 |
| DOMS | 1–7 | 근육통 (Delayed Onset Muscle Soreness) |
| Sleep Quality | 1–7 | 1 = 매우 좋음, 7 = 매우 나쁨 |

> **주의 — Sleep 스케일 방향**: 원 논문에서는 높은 점수가 나쁜 수면을 의미한다.
> 일부 구현에서는 역코딩하여 높은 점수가 좋은 수면을 의미하도록 변환하는 경우도 있으므로
> 프로젝트 내에서 **방향을 통일**하는 것이 중요하다.

### 규칙

- **총점 범위**: 4 (최상) ~ 28 (최악)
- **수집 시점**: 매일 아침, 훈련 전에 수집한다.
- **결측 처리**: 4개 항목 중 1개라도 결측이면 Hooper Index = `NULL`. 부분 합산하지 않는다.
- **해석 기준** (참고):

| Hooper Index | 해석 |
|-------------|------|
| 4 – 12 | 양호한 회복 상태 |
| 13 – 18 | 주의 필요 |
| 19 – 28 | 고피로/고스트레스 상태 — 부하 조절 권장 |

> 위 기준은 절대적이지 않으며, 개인 내(intra-individual) 변화 추이를 함께 고려해야 한다 (Saw et al., 2016 [Ref #21]).

### 변형: 5점 스케일

일부 팀에서는 1–5 스케일을 사용하기도 한다. 이 경우 총점 범위는 4–20이 된다.
본 프로젝트에서 사용하는 스케일은 설정 파일(`config.json`)에서 지정한다.

---

## 8. HRV 지표 (rMSSD, SDNN)

### 정의

심박 변이도(Heart Rate Variability)의 시간 영역(time-domain) 지표.

> 근거: Task Force (1996) [Ref #22]

### 8.1 SDNN (Standard Deviation of NN intervals)

```
SDNN = sqrt( (1/(N-1)) × Σ(i=1 to N) (NN_i - mean(NN))² )
```

| 파라미터 | 설명 |
|----------|------|
| NN_i | i번째 정상(Normal-to-Normal) R-R 간격 (ms) |
| N | 총 NN 간격 수 |
| mean(NN) | NN 간격의 산술 평균 |

- **의미**: 전체 HRV의 총 변이를 반영. 교감 + 부교감 신경계 활동을 모두 포함.
- **측정 시간**: 표준 측정 시간은 **5분** (단기) 또는 **24시간** (장기). 상이한 측정 시간 간 비교는 불가 [Ref #22].
- **단위**: ms (밀리초)

### 8.2 rMSSD (Root Mean Square of Successive Differences)

```
rMSSD = sqrt( (1/(N-1)) × Σ(i=1 to N-1) (NN_(i+1) - NN_i)² )
```

| 파라미터 | 설명 |
|----------|------|
| NN_i | i번째 NN 간격 |
| NN_(i+1) | (i+1)번째 NN 간격 |
| N | 총 NN 간격 수 |

- **의미**: 인접 NN 간격 차이의 제곱평균제곱근. **부교감(vagal) 신경** 활동을 주로 반영.
- **스포츠 현장 권장**: 선수 모니터링 시 rMSSD가 SDNN보다 선호된다 — 짧은 측정 시간(1–5분)에도 안정적이며 부교감 신경 활동을 잘 반영하기 때문이다 (Plews et al., 2013 [Ref #23]; Buchheit, 2014 [Ref #24]).

### 8.3 ln(rMSSD) — 자연 로그 변환

```
ln_rMSSD = ln(rMSSD)
```

- 분포 정규화 및 변이 계수(CV) 감소를 위해 자연 로그 변환을 적용한다 (Plews et al., 2013 [Ref #23]).
- **추세 분석**: 7일 rolling average of ln(rMSSD) — 일상적 변동을 완화하고 추세를 파악한다.

```
ln_rMSSD_7d(t) = (1/7) × Σ(i=0 to 6) ln_rMSSD(t-i)
```

> 개인 내 변화(CV of ln(rMSSD))가 **SWC(Smallest Worthwhile Change)** 이상일 때 의미 있는 변화로 해석한다 (Buchheit, 2014 [Ref #24]).

### HRV 측정 프로토콜 규칙

| 항목 | 규칙 |
|------|------|
| 측정 자세 | 앙와위(supine) 또는 좌위(seated) — **프로젝트 내 통일** |
| 측정 시간 | 기상 직후, 동일 시간대 |
| 측정 구간 | 안정화 1분 후 → **측정 구간 최소 1분** (권장 2–5분) |
| 호흡 통제 | 자유 호흡 (paced breathing 미적용) |
| 이상치 필터 | 중앙값 필터 또는 NN 간격 ± 20% 벗어나는 값 제거 |
| 최소 데이터 | 측정 구간 내 유효 NN 간격 **150개 이상** |

### 결측 처리

- 유효 NN 간격이 150개 미만이면 해당 측정 = `NULL`.
- 연속 결측 3일 이상 시 ln_rMSSD_7d = `NULL`.

---

## 부록: EWMA Decay Factor 표준 정의

> 근거: Williams et al. (2017) [Ref #10]

본 프로젝트의 모든 EWMA 계산에 적용되는 감쇠 계수(decay factor) 정의:

```
α = 2 / (N + 1)
```

| 기간 (N) | α 값 | 용도 |
|----------|------|------|
| 7 | 2/8 = **0.2500** | ATL (급성 부하) |
| 14 | 2/15 = **0.1333** | 중기 부하 (필요 시) |
| 28 | 2/29 = **0.0690** | CTL (만성 부하) |
| 42 | 2/43 = **0.0465** | 장기 적응 (필요 시) |

### EWMA 일반 재귀식

```
EWMA(t) = α × Value(t) + (1 - α) × EWMA(t-1)
```

- **초기값**: `EWMA(1) = Value(1)`
- **해석**: α가 클수록 최근 값에 높은 가중치 부여, α가 작을수록 과거 값의 영향이 오래 지속.
- 데이터 포인트가 k일 전일 때 해당 값의 잔존 가중치: `(1 - α)^k`

---

## 부록: 전체 예외 처리 요약

| 상황 | 지표 | 처리 |
|------|------|------|
| 데이터 < warm-up 기간 | ATL(rolling) | 7일 미만: `NULL` 또는 expanding mean |
| 데이터 < warm-up 기간 | CTL(rolling) | 28일 미만: `NULL` 또는 expanding mean |
| 데이터 < warm-up 기간 | ACWR | 21일 미만: `NULL` (EWMA), 28일 미만: `NULL` (rolling) |
| CTL = 0 | ACWR | `NULL` (division by zero 방지) |
| sd = 0 | Monotony | `NULL` 또는 cap 값 (10.0) |
| Monotony = NULL | Strain | `NULL` |
| 단일 항목 결측 | Hooper Index | `NULL` (부분 합산 불가) |
| 유효 NN < 150 | rMSSD / SDNN | `NULL` |
| 연속 결측 ≥ 3일 | ATL (EWMA) | `NULL` |
| 연속 결측 ≥ 7일 | CTL (EWMA) | `NULL` |
| RPE 또는 Duration 결측 | sRPE | `NULL` |
| 휴식일 (훈련 없음) | sRPE / daily load | `0` (결측이 아닌 의도적 0) |

---

## 부록: 파라미터 설정 요약 (Default)

| 파라미터 | 기본값 | 설정 위치 |
|----------|--------|-----------|
| ATL 윈도우 (N_a) | 7일 | `config.json` |
| CTL 윈도우 (N_c) | 28일 | `config.json` |
| EWMA α (acute) | 0.25 | 자동 계산: 2/(N_a+1) |
| EWMA α (chronic) | 0.0690 | 자동 계산: 2/(N_c+1) |
| Monotony 윈도우 | 7일 | 고정 (Foster 정의) |
| RPE 스케일 | CR-10 (0–10) | `config.json` |
| Hooper 스케일 | 1–7 | `config.json` |
| HRV 측정 구간 | 2분 (최소 1분) | 측정 프로토콜 |
| ACWR 방식 | EWMA (기본) | `config.json` |
| ACWR warm-up | 21일 | 코드 상수 |
| Monotony cap | 10.0 | 코드 상수 |

---

*마지막 갱신: 2026-02-10*
*작성: research-librarian@soccer-rnd*
*근거 문헌 전체 목록: [REFERENCES.md](./REFERENCES.md)*
