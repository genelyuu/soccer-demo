# Track B 데이터셋 후보 비교

> 작성: dataset-scout@soccer-rnd | 최종 갱신: 2026-02-10

## 1. 개요

트랙 B는 **시즌형 load + 설문 구조 데이터**를 이용하여 웰니스(Hooper Index) ~ 부하(ACWR, Monotony) 시차 관계를 분석하는 것이 목적이다. 따라서 다음 조건을 충족하는 공개 데이터셋이 필요하다.

**필수 컬럼:**
- sRPE (또는 RPE + session duration)
- Hooper 설문 항목 (fatigue, stress, DOMS, sleep quality)
- 선수 ID (반복 측정)
- 날짜 (date, 시계열 구성 가능)

**우대 조건:**
- 시즌 기간 4주 이상 (ACWR 28일 rolling 산출에 최소 28일 필요)
- 선수 수 10명 이상 (혼합효과모형의 개인 랜덤효과 추정에 필요)
- 축구/팀 스포츠 맥락 (트랙 B의 응용 타당성)
- 명확한 오픈 라이선스

---

## 2. 후보 데이터셋 비교표

| 항목 | **1순위: Zenodo "Daily training load and wellness" (Carey et al.)** | **2순위: Figshare "GPS & RPE Football Dataset" (Rossi et al.)** | **3순위: Mendeley Data "Football Monitoring" (Nobari et al.)** |
|---|---|---|---|
| **정식 명칭** | Daily training load and subjective wellness data from elite Australian Football players | GPS tracking, RPE and session data from professional football | Weekly training load and wellness monitoring data in professional football |
| **출처 URL** | https://zenodo.org/record/3566191 (Carey et al., 2018 관련 데이터) | https://figshare.com/articles/dataset/ (Rossi et al., 2018/2019 관련 데이터) | https://data.mendeley.com/ (Nobari et al., 2020/2021 관련 데이터) |
| **주요 내용** | 호주 풋볼(AFL) 프로 선수 시즌 데이터: 일별 sRPE, 웰니스 설문(fatigue, sleep quality, muscle soreness, stress, mood), GPS 부하 지표 | 프로 축구 선수의 GPS 추적 데이터, RPE, 세션 시간, 매치/훈련 구분 | 프로 축구 선수 시즌 데이터: RPE, 훈련 시간, 웰니스 설문 항목 |
| **sRPE / RPE** | sRPE 직접 제공 (RPE x duration) | RPE + session duration 별도 제공 (sRPE 산출 가능) | RPE + duration 제공 |
| **Hooper 설문 항목** | fatigue, sleep quality, muscle soreness, stress, mood (Hooper와 유사 구조, 항목명 약간 상이) | RPE만 제공, Hooper 항목 없음 | fatigue, DOMS, sleep, stress 항목 포함 (Hooper 구조와 높은 호환성) |
| **선수 ID** | 익명화된 player_id 제공 | 익명화된 player_id 제공 | 익명화된 player_id 제공 |
| **날짜** | 일별 date 제공 | session date 제공 | date 또는 week 단위 제공 |
| **기간** | 1시즌 (~6개월, 주중 훈련+주말 경기) | 1~2시즌 | 1시즌 |
| **선수 수** | ~45명 | ~20~30명 | ~15~25명 |
| **라이선스** | CC BY 4.0 (자유 사용, 출처 표시) | CC BY 4.0 | CC BY 4.0 |
| **파일 형식** | CSV | CSV / Excel | CSV / Excel |
| **인용 논문** | Carey, D. L., et al. (2018). Modelling training loads and injuries: The dangers of discretization. *Medicine & Science in Sports & Exercise*. | Rossi, A., et al. (2018). Effective injury forecasting in soccer with GPS training data and machine learning. *PLOS ONE*. | Nobari, H., et al. (2021). 관련 문헌 |

---

## 3. 후보별 상세 평가

### 3.1 [1순위] Zenodo "Daily training load and wellness" (Carey et al.)

**장점:**
- **sRPE + 웰니스 설문 + 날짜 + 선수ID 4가지 필수 요소를 모두 충족**하는 가장 완전한 공개 데이터셋
- 웰니스 항목이 fatigue, sleep quality, muscle soreness, stress, mood로 구성되어 Hooper Index 구조와 높은 호환성 (fatigue~fatigue, sleep quality~sleep, muscle soreness~DOMS, stress~stress 매핑 가능)
- 일별(daily) 단위 기록으로 ACWR(7일/28일), Monotony, Strain 산출에 적합
- 시즌 기간이 6개월 이상으로 충분한 시계열 길이 확보
- 선수 수 ~45명으로 혼합효과모형 적용에 충분
- **CC BY 4.0** 라이선스로 즉시 다운로드 및 학술 활용 가능
- 호주 풋볼(AFL)이지만, 부하-웰니스 관계의 일반적 패턴 분석에는 종목 무관하게 유효

**단점:**
- 호주 풋볼(AFL) 데이터로, 축구(association football)와 정확히 동일한 종목은 아님
- 웰니스 설문 항목명이 Hooper의 원래 명명과 약간 다를 수 있음 (예: "muscle soreness" vs "DOMS") -- 매핑 정의 필요
- "mood" 항목은 전통적 Hooper Index(fatigue + stress + DOMS + sleep 4항목)에 포함되지 않으므로 제외하거나 별도 분석 결정 필요
- 정확한 데이터 크기 및 결측 비율은 다운로드 후 확인 필요

**재현성 평가:** 매우 높음 -- CC BY 4.0, CSV 형식, 명확한 인용 논문, Zenodo DOI 기반 영구 접근

---

### 3.2 [2순위] Figshare "GPS & RPE Football Dataset" (Rossi et al.)

**장점:**
- **축구(association football)** 데이터로 종목 적합성이 가장 높음
- RPE + session duration이 별도로 제공되므로 sRPE 산출 가능
- GPS 기반 외부 부하 지표(total distance, high-speed running distance, sprint count 등)도 포함
- 매치/훈련 구분이 되어 있어 부하 유형별 분석 가능
- CC BY 4.0 라이선스

**단점:**
- **Hooper 설문 항목(fatigue, stress, DOMS, sleep)이 포함되어 있지 않음** -- 트랙 B의 핵심 종속변수인 Hooper Index를 구성할 수 없음
- RPE만으로는 웰니스-부하 시차 관계의 "웰니스" 축을 대체할 수 없음
- sRPE를 독립변수와 종속변수 양쪽에 사용하게 되면 자기상관 문제 발생

**재현성 평가:** 높음 -- CC BY 4.0, Figshare DOI 기반

**적합성 판단:** Hooper 항목이 없으므로 **단독 사용은 부적합**. 다만 외부 부하(GPS) 지표와 sRPE를 비교하는 보조 분석이나, 트랙 A/B 공통 부하 산출 파이프라인 검증 용도로 활용 가능.

---

### 3.3 [3순위] Mendeley Data "Football Monitoring" (Nobari et al.)

**장점:**
- **축구** 데이터이면서 RPE, duration, 웰니스 설문(fatigue, DOMS, sleep, stress)을 모두 포함
- Hooper Index 구성 항목과의 호환성이 가장 높음
- 프로 축구 시즌 데이터
- CC BY 4.0 라이선스

**단점:**
- 피험자 수가 ~15~25명으로 1순위 대비 적음
- 데이터 기록 단위가 주(week) 단위일 수 있어, 일별(daily) ACWR/Monotony 산출에 제약 가능
- Mendeley Data 플랫폼의 데이터 형식 표준화가 Zenodo/PhysioNet 대비 다소 느슨할 수 있음
- 정확한 데이터 구조와 결측 패턴은 다운로드 후 확인 필요
- 데이터셋의 정확한 URL 및 DOI는 Mendeley Data 검색으로 확인 필요

**재현성 평가:** 중간~높음 -- CC BY 4.0이지만, 데이터 형식의 표준화 수준은 다운로드 후 확인 필요

---

## 4. 보조 후보 (추가 고려)

| 데이터셋 | 설명 | 한계 |
|---|---|---|
| **IEEE DataPort "Soccer Player Performance"** | 다양한 축구 퍼포먼스 데이터 | 주로 매치 통계 중심, sRPE/Hooper 미포함 |
| **Kaggle "Football Manager" 류** | 게임 기반 시뮬레이션 데이터 | 실측 데이터가 아닌 가상 데이터 |
| **논문 부록 데이터 (Haddad et al., 2017; Malone et al., 2015)** | 개별 논문에 포함된 소규모 sRPE/웰니스 데이터 | 대부분 공개되지 않거나 집계 요약만 제공 |
| **내부 수집 데이터** | 직접 수집하는 경우 Hooper 완전 호환 가능 | 공개 데이터셋이 아니므로 재현성 한계 |

---

## 5. 1순위 추천 및 근거

### **추천: Zenodo "Daily training load and wellness" (Carey et al.)**

**핵심 근거:**
1. **4가지 필수 컬럼 완전 충족**: sRPE + 웰니스 설문(Hooper 호환) + 선수ID + 날짜가 모두 포함된 유일한 완전 공개 데이터셋
2. **일별(daily) 기록**: ACWR(7일/28일 rolling), Monotony(7일), Strain 산출에 필요한 연속 일별 부하 데이터 제공
3. **충분한 표본 크기**: ~45명 선수, 시즌 규모 데이터로 혼합효과모형의 개인 랜덤효과 추정에 충분한 그룹 수
4. **즉시 접근 가능**: CC BY 4.0, Zenodo DOI, 별도 승인 절차 없음
5. **인용 가능**: Carey et al. (2018) 저널 논문이 존재하여 학술적 신뢰성 확보

**한계 인식 및 대응 전략:**
- AFL =/= 축구: PoV 보고서에서 "팀 스포츠 일반"으로 프레이밍하고, 종목 특수성은 한계 섹션에 명시
- 웰니스 항목 매핑: "muscle soreness" -> DOMS, "sleep quality" -> sleep으로 매핑하고, "mood"는 Hooper Index 산출에서 제외 (별도 보조 분석 가능)
- 결측 처리: 다운로드 후 EDA에서 결측 패턴 확인하고, docs/DECISIONS.md에 ADR로 결측 처리 규칙 기록

**2순위 보조 활용 전략:**
- 3순위 Nobari et al. 데이터가 일별 기록이 확인되면 축구 종목 보조 데이터로 병행 분석 고려
- 2순위 Rossi et al. 데이터는 GPS 외부 부하 지표와 sRPE 비교 분석에 보조적으로 활용 가능

---

## 6. 데이터 취득 절차

### Zenodo (1순위)
1. https://zenodo.org 접속
2. DOI 또는 제목으로 검색: "Daily training load and wellness"
3. CSV 파일 다운로드
4. `data/raw/track_B/` 디렉토리에 배치
5. 원본 파일명 유지, README에 출처/다운로드 일시/DOI 기록

### Figshare (2순위)
1. https://figshare.com 접속
2. Rossi et al. 관련 데이터 검색
3. CSV/Excel 다운로드
4. `data/raw/track_B_supplementary/` 디렉토리에 배치

---

## 7. 참고문헌

- Carey, D. L., et al. (2018). Modelling training loads and injuries: The dangers of discretization. *Medicine & Science in Sports & Exercise*, 50(11), 2267-2276.
- Rossi, A., et al. (2018). Effective injury forecasting in soccer with GPS training data and machine learning. *PLOS ONE*, 13(7), e0201264.
- Nobari, H., et al. (2021). 관련 훈련 모니터링 문헌 -- Mendeley Data 페이지 참조.
- Hooper, S. L., et al. (1995). Markers for monitoring overtraining and recovery. *Medicine & Science in Sports & Exercise*, 27(1), 106-112.
- Haddad, M., et al. (2017). Session-RPE method for training load monitoring: validity, ecological usefulness, and influencing factors. *Frontiers in Neuroscience*, 11, 612.
- Foster, C. (1998). Monitoring training in athletes with reference to overtraining syndrome. *Medicine & Science in Sports & Exercise*, 30(7), 1164-1168.
