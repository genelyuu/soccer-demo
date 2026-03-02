# 통합 합성 데이터 가설 검증 실험 보고서

**생성일**: 2026-02-11
**ADR**: ADR-012
**재현 명령**: `python notebooks/run_integrated_hypothesis.py`

---

## 1. 실험 개요

실제 데이터 분석에서 도출된 세 가지 핵심 발견을 통합 합성 데이터(DGP)로 검증한다.

### 1.1 DGP 구조

| 파라미터 | 값 | 근거 |
|----------|-----|------|
| N_athletes | 30 | Track A(18)+B(44) 중간 |
| N_days | 120 | ~17주 시즌 |
| seed | 2024 | 기존 42와 독립 |
| sigma_u_hooper | 1.25 | Track B ICC≈0.48 역산 |
| sigma_u_hrv | 0.35 | Track A ICC≈0.14 역산 |
| beta_acwr_hooper | -0.08 | Track B M4 실제 계수 |
| beta_mono_hooper | +0.14 | Track B M4 실제 계수 |
| beta_strain_hooper | -0.00007 | Track B M4 실제 계수 |
| beta_hrv_hooper | -0.50 | HRV→Hooper 직접 경로 |
| beta_acwr_hrv | -0.15 | Track A 방향 반영 |
| sigma_e_hooper | 1.35 | Track B 잔차 |
| sigma_e_hrv | 0.50 | Track A 잔차 |
| cor_u | -0.30 | HRV-Hooper 랜덤효과 상관 |

---

## 2. 가설별 결과

### H1: 개인화된 기저선 추적의 중요성 — **4/4 PASS**

| 검증 | 측정값 | 기준 | 판정 |
|------|--------|------|------|
| AIC 차이 (Hooper) | ΔAIC = 1403.7 | ΔAIC > 100 | **PASS** |
| R² 도약 | OLS=0.029, Mixed=0.454 | OLS R² < 0.05 AND Mixed R² > 0.30 | **PASS** |
| ICC 순서 | Hooper=0.450, HRV=0.297 | ICC_hooper > ICC_hrv | **PASS** |
| LOSO MAE | Mixed LOSO=1.608 > OLS 전체=1.563 | Mixed LOSO MAE > OLS 전체 MAE | **PASS** |

Simpson's Paradox 재현에 성공하였다. OLS의 R²는 3% 미만으로 거의 무의미하나, 개인 기저선을 반영한 Mixed 모형은 R²=0.45로 도약한다. ICC가 높은 Hooper(0.45)에서 이 효과가 더 뚜렷하다.

### H2: 다중 지표 통합 모니터링 우위 — **2/3 PASS**

| 검증 | 측정값 | 기준 | 판정 |
|------|--------|------|------|
| AIC 차이 | ΔAIC = 54.9 | ΔAIC > 4 | **PASS** |
| 증분 Cohen's f² | f² = 0.0214 | f² > 0.02 | **PASS** |
| LOSO CV | MAE 개선 3.1% | MAE 5% 이상 개선 | FAIL |

ln_rmssd를 통합 모형에 추가하면 AIC가 크게 개선(ΔAIC=54.9)되고 Cohen's f²도 기준을 충족한다. 다만 LOSO MAE 개선은 3.1%로, 새 선수에 대한 일반화 측면에서는 실용적 개선이 제한적이다. 이는 HRV의 개인 간 변동(랜덤효과)이 LOSO에서 활용되지 못하기 때문으로 시사된다.

### H3: Monotony 독립 효과 및 억제변수 재현 — **2/3 PASS**

| 검증 | 측정값 | 기준 | 판정 |
|------|--------|------|------|
| Monotony 유의성 | p = 0.564 | p < 0.05 | FAIL |
| 억제변수 효과 | 262.1% | Strain 전/후 Mono 계수 변화 > 50% | **PASS** |
| 참값 복원 | 26.7% | \|β_mono - 0.14\| / 0.14 < 0.30 | **PASS** |

억제변수 효과가 뚜렷하게 재현되었다: Strain 투입 전 Mono β=-0.063 → 투입 후 β=+0.103 (부호 반전, 262% 변화). 참값 복원 오차도 26.7%로 기준 이내이다. 다만 개별 데이터셋에서의 통계적 유의성(p=0.564)은 달성하지 못하였으며, 이는 30선수 규모에서 β=0.14의 효과가 공선성 하에서 충분한 검정력을 확보하기 어렵기 때문이다. Monte Carlo 100회 평균(β=0.138)은 참값에 매우 근접한다.

VIF 점검 결과 모든 변수의 VIF < 3으로 심각한 다중공선성은 관찰되지 않았다.

### H4: 결측 민감도 분석 — **1/3 PASS**

| 검증 | 측정값 | 기준 | 판정 |
|------|--------|------|------|
| MCAR 편향 | 3.35% | \|bias\|/\|true\| < 10% | **PASS** |
| 편향 순서 | MNAR=4.1% < MAR=9.5% > MCAR=3.4% | bias_MNAR > bias_MAR > bias_MCAR | FAIL |
| Coverage 순서 | MNAR=97% = MAR=97% = MCAR=97% | Coverage_MNAR < Coverage_MAR < Coverage_MCAR | FAIL |

MCAR 편향은 3.35%로 기준(10%)을 충족하여, 무작위 결측은 추정에 실질적 영향을 주지 않음을 확인하였다. 다만 편향 순서(MNAR > MAR > MCAR)와 Coverage 순서는 엄격하게 성립하지 않았다. 이는 다음 요인으로 설명된다:

1. **MAR의 높은 결측률**: logistic(-2.0 + 0.005×load)에서 평균 부하 ~400일 때 P(missing)≈50%로, 관측수 대폭 감소가 추정 분산을 증가시킴
2. **MNAR 효과 크기**: β_mnar_slope=0.15로 설정되었으나, Hooper 범위(~8-12)에서 결측 확률 변동이 제한적

---

## 3. 종합 결과

| 가설 | Pass | Total | 상태 |
|------|------|-------|------|
| H1: 개인 기저선 | 4 | 4 | PASS |
| H2: 통합 모니터링 | 2 | 3 | PARTIAL |
| H3: Monotony 억제 | 2 | 3 | PARTIAL |
| H4: 결측 민감도 | 1 | 3 | PARTIAL |
| **전체** | **9** | **13** | |

---

## 4. 시각화

| 그림 | 파일 | 설명 |
|------|------|------|
| H1 OLS vs Mixed R² | `figures/h1_ols_vs_mixed_r2.png` | Hooper/HRV 양쪽의 R² 비교 |
| H3 Monotony 순차 투입 | `figures/h3_monotony_sequential.png` | Strain 투입 전후 계수 변화 |
| H4 결측 민감도 | `figures/h4_missing_sensitivity.png` | 편향/Coverage 4개 메커니즘 비교 |

---

## 5. 해석 및 시사점

### 5.1 핵심 시사점

1. **개인 기저선은 필수적이다** (H1 완전 검증): ICC=0.45인 Hooper에서 Mixed 모형의 R² 도약(0.03→0.45)은, 팀 평균 기반 접근이 근본적으로 부적절함을 보여준다.

2. **HRV 통합은 통계적으로 유의미하나 실용적 이득은 제한적이다** (H2 부분 검증): AIC와 f²는 기준을 충족하지만, LOSO MAE 개선은 3%에 불과하다. 새 선수에 대한 예측에서는 HRV의 추가 가치가 제한적일 수 있다.

3. **Monotony 억제변수 효과는 구조적으로 존재한다** (H3 부분 검증): 부호 반전과 참값 복원은 성공하였으나, 단일 데이터셋 유의성은 검정력 부족으로 달성하지 못한다. 실무적으로는 100회 Monte Carlo 평균이 참값에 근접(β=0.138 vs 0.14)함이 중요하다.

4. **MCAR 결측은 안전하다** (H4 부분 검증): 무작위 결측 10% 이하에서 편향은 미미하다. MNAR의 위험은 이론적으로 존재하나, 현재 DGP 규모에서 명확한 순서 관계로 나타나지 않는다.

### 5.2 한계

- DGP가 실제 데이터의 모든 복잡성(비선형, 상호작용, 시간 자기상관)을 반영하지 못한다.
- 30선수 × 120일은 중규모 데이터로, 작은 효과(β=0.14)의 개별 유의성 확보에는 제한적이다.
- Strain-Monotony 구조적 상관(Strain = weekly_sum × Monotony)은 현실에서도 동일하게 존재하는 제약이다.

---

## 6. 재현 방법

```bash
# 테스트
python -m pytest tests/test_synthetic_integrated.py -v

# 실행
python notebooks/run_integrated_hypothesis.py

# 노트북
jupyter nbconvert --execute notebooks/integrated_hypothesis.ipynb
```
