# Track A 데이터셋 후보 비교

> 작성: dataset-scout@soccer-rnd | 최종 갱신: 2026-02-10

## 1. 개요

트랙 A는 **HRV/RR 원자료**로부터 rMSSD, SDNN을 산출하고, 운동 부하 지표(ACWR 등)와의 시차 관계를 분석하는 것이 목적이다. 따라서 다음 조건을 충족하는 공개 데이터셋이 필요하다.

**필수 컬럼:**
- RR intervals (또는 beat-to-beat 심박 원자료)
- 운동 부하 관련 정보 (power, VO2, 속도, 경사도 등)
- 피험자 식별자 (반복 측정 시)

**우대 조건:**
- 다중 세션 (시간 경과에 따른 부하-HRV 관계 관찰 가능)
- 피험자 수 10명 이상
- 명확한 오픈 라이선스 (재배포/학술 사용 가능)

---

## 2. 후보 데이터셋 비교표

| 항목 | **1순위: PhysioNet ACTES** | **2순위: Autonomic Aging (PhysioNet)** | **3순위: Exercise ECG (Lobachevsky Univ.)** |
|---|---|---|---|
| **정식 명칭** | Autonomic Control of the cardiovascular system during exercise and recovery in response to Training and Exercising in Standardized conditions | Autonomic Aging: A dataset to quantify changes of cardiovascular autonomic function during healthy aging | Exercise Physiology and ECG Database |
| **출처 URL** | https://physionet.org/content/actes/1.0.0/ | https://physionet.org/content/autonomic-aging-cardiovascular/1.0.0/ | https://physionet.org/content/ephnogram/1.0.0/ |
| **주요 내용** | 다단계 점증 운동 부하 검사(Incremental Exercise Test) 중 beat-to-beat RR 간격, 파워(W), VO2, VCO2, 환기량 등 심폐 운동 검사(CPET) 데이터 | 건강한 성인의 안정 시 및 기립 경사 검사(tilt test) 시 RR 간격, 혈압, 호흡 데이터 | 자전거 에르고미터 운동 중 ECG 원형, 호흡, 혈압, VO2 데이터 |
| **RR 간격** | beat-to-beat RR (ms) 직접 제공 | beat-to-beat RR 직접 제공 | ECG 원파형에서 R-peak 탐지 후 추출 필요 |
| **운동 부하 정보** | power (W), VO2 (mL/min/kg), 단계별 부하 프로토콜 | 기립 경사 검사 (수동적 자세 변화, 능동적 운동 부하 아님) | power (W), VO2, 단계별 부하 프로토콜 |
| **피험자 수** | ~38명 (건강한 성인, 훈련 전후) | ~1,100명 (광범위 연령대) | ~25명 |
| **세션 구조** | 훈련 기간 전후 2회 측정 (pre/post training) | 단일 세션 (안정+기립) | 단일 세션 운동 부하 검사 |
| **라이선스** | PhysioNet Credentialed Health Data License 1.5.0 (PhysioNet 계정 + 데이터 이용 동의 후 접근) | PhysioNet Open Data License (자유 접근) | PhysioNet Restricted Health Data License (계정 필요) |
| **파일 형식** | CSV/TSV, WFDB 형식 | CSV, WFDB 형식 | EDF/WFDB 형식 |
| **인용 논문** | Gronwald et al. (관련 문헌 PhysioNet 페이지 참조) | Muehlsteff et al. / Autonomic Aging 프로젝트 | Kazemnejad et al. |

---

## 3. 후보별 상세 평가

### 3.1 [1순위] PhysioNet ACTES

**장점:**
- **beat-to-beat RR 간격**과 **power(W), VO2**가 동시에 기록되어, rMSSD/SDNN 산출과 부하 정량화를 하나의 데이터셋에서 처리 가능
- 점증 운동 부하 검사(incremental exercise test)이므로 부하 단계별 HRV 반응을 관찰할 수 있음
- 훈련 전후(pre/post) 2회 측정이 있어 훈련 효과에 따른 자율신경 반응 변화도 분석 가능
- PhysioNet의 표준화된 데이터 배포 체계를 따름
- CPET 프로토콜이 명확히 문서화되어 있어 재현성 우수

**단점:**
- Credentialed Access로 PhysioNet 계정 등록 및 데이터 이용 동의서 제출이 필요 (즉시 다운로드 불가, 승인까지 수일 소요 가능)
- 피험자 수가 ~38명으로, 대규모 통계 분석에는 통계적 검정력이 제한적
- 단일 세션(점증 부하 검사) 데이터이므로, 실제 시즌형 "일별 부하 → 다음 날 HRV" 종단 분석과는 설계가 다름
- 부하 지표를 ACWR(7일/28일 rolling)로 변환하려면 세션 내 단계를 "일별 부하"로 재정의하는 설계적 판단이 필요

**재현성 평가:** 높음 -- PhysioNet 표준 형식, 명확한 프로토콜 문서, 인용 논문 존재

---

### 3.2 [2순위] Autonomic Aging (PhysioNet)

**장점:**
- 피험자 수가 ~1,100명으로 매우 대규모, 개인차(random effects) 추정에 유리
- Open Data License로 별도 승인 절차 없이 즉시 다운로드 가능
- beat-to-beat RR 간격이 직접 제공됨
- 연령 범위가 넓어 다양한 인구 통계적 분석 가능

**단점:**
- **운동 부하 데이터가 없음** -- 기립 경사 검사(tilt test)는 수동적 자세 변화이므로 power/VO2 기반 부하 지표 산출이 불가능
- 단일 세션 측정으로 종단적 부하-회복 분석이 불가능
- 스포츠/훈련 맥락과의 관련성이 낮음

**재현성 평가:** 높음 -- 오픈 라이선스, 대규모 데이터, 표준 형식

**적합성 판단:** 트랙 A의 핵심 요구사항인 "운동 부하 관련 정보"가 부재하므로, 단독 사용은 부적합. 다만 HRV 지표 산출 파이프라인의 검증 용도로 보조적 활용 가능.

---

### 3.3 [3순위] Ephnogram / Exercise ECG Database (PhysioNet)

**장점:**
- 자전거 에르고미터 운동 중 ECG, VO2, power 데이터를 동시 수집
- 운동 부하와 심혈관 반응을 함께 분석 가능
- PhysioNet 인프라 활용

**단점:**
- RR 간격이 직접 제공되지 않고 ECG 원파형에서 R-peak 탐지 알고리즘을 적용하여 추출해야 함 (전처리 부담 증가)
- 피험자 수 ~25명으로 소규모
- Restricted Health Data License로 접근 절차가 가장 복잡
- 데이터 품질(ECG 잡음, 운동 중 아티팩트)에 따라 RR 추출 신뢰도가 변동

**재현성 평가:** 중간 -- R-peak 탐지 알고리즘 선택에 따라 결과 재현성이 달라질 수 있음

---

## 4. 보조 후보 (추가 고려)

| 데이터셋 | 설명 | 한계 |
|---|---|---|
| **MIT-BIH Normal Sinus Rhythm DB** (PhysioNet) | 장기 Holter ECG 기록, RR 추출 가능 | 운동 부하 데이터 없음, 안정 시 기록 |
| **WESAD** (UCI ML Repository) | 웨어러블 센서 기반 생리 데이터 (ECG, BVP 등) | 스트레스 실험이며 운동 부하 미포함 |
| **PPG-DaLiA** | 일상 활동 중 PPG/ACC 데이터 | RR 간격 직접 제공 안 됨, 운동 부하 미정량화 |

---

## 5. 1순위 추천 및 근거

### **추천: PhysioNet ACTES**

**핵심 근거:**
1. **유일한 RR + 운동부하 동시 제공 데이터셋**: beat-to-beat RR 간격과 power(W)/VO2가 동일 세션에서 수집되어, HRV 지표(rMSSD, SDNN)와 부하 지표를 하나의 파이프라인에서 산출할 수 있는 유일한 후보
2. **점증 부하 프로토콜**: 단계별로 부하가 증가하므로 부하 강도에 따른 HRV 반응의 dose-response 관계를 직접 관찰 가능
3. **훈련 전후 비교 가능**: pre/post training 설계로 훈련 적응에 따른 자율신경 반응 변화 분석 가능
4. **PhysioNet 표준 형식**: 데이터 품질 관리 및 재현 가능성이 보장됨

**한계 인식 및 대응 전략:**
- ACWR(7일/28일 rolling) 산출을 위해, 점증 부하 검사의 각 단계를 "부하 단위"로 재정의하거나, pre/post 두 시점의 총 부하를 비교하는 방식으로 설계를 조정해야 함
- 피험자 38명은 혼합효과모형에서 그룹 수준 추정에 최소한의 검정력만 확보 가능 → 효과크기(Cohen's d) 보고로 보완
- 시즌형 종단 분석(daily load → next-day HRV)은 이 데이터셋의 구조적 한계이므로, PoV에서 "세션 내 부하-HRV 반응" 관점으로 프레이밍 조정 필요

**Credentialed Access 취득 절차:**
1. PhysioNet 계정 생성 (https://physionet.org/register/)
2. 데이터 이용 동의서 서명
3. 연구 목적 기술
4. 승인 후 다운로드 (통상 1~3 영업일)

---

## 6. 참고문헌

- Goldberger, A. L., et al. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. *Circulation*, 101(23), e215-e220.
- Gronwald, T., et al. (ACTES 관련 문헌) -- PhysioNet 데이터셋 페이지 참조
- Shaffer, F., & Ginsberg, J. P. (2017). An overview of heart rate variability metrics and norms. *Frontiers in Public Health*, 5, 258.
- Plews, D. J., et al. (2013). Training adaptation and heart rate variability in elite endurance athletes. *International Journal of Sports Physiology and Performance*, 8(6), 688-694.
