# 트랙 B EDA 계획

> 목적: sRPE/ACWR/Monotony 부하 지표와 Hooper Index 웰니스 간 시차 관계 탐색

## 데이터셋
- 1순위: Carey et al. (Zenodo, CC BY 4.0, AFL ~45명, 1시즌)
- 웰니스 매핑: fatigue→fatigue, sleep quality→sleep, muscle soreness→DOMS, stress→stress (mood 제외)
- 파이프라인 검증: 합성 데모 데이터(12명, 120일) 사용

## EDA 4단계

### 1단계: 데이터 품질 점검
- 선수별 결측 비율 히트맵
- 일별 부하(sRPE) 분포 — 선수별 boxplot
- Hooper 4항목 분포 (fatigue, stress, DOMS, sleep)

### 2단계: 주간 부하 패턴 및 지표 산출
- 선수별 ACWR(rolling/EWMA), Monotony, Strain 산출
- 요일별 평균 부하 막대 그래프 (월~일 패턴)
- 대표 선수 시계열: daily_load, ATL, CTL, ACWR, Monotony, Strain

### 3단계: ACWR 급등 vs Hooper 변화
- ACWR(t) vs Hooper(t+1) 산점도 (lag=1일)
- Monotony(t) vs Hooper(t+1) 산점도
- Pearson 상관계수 표 (lag 0~3일)
- 집중 훈련 구간 전후 Hooper 변화 이벤트 플롯

### 4단계: Monotony/Strain 탐색
- Strain(t) vs Hooper(t+1) 산점도
- 고 Monotony (>2.0) 구간 하이라이트
- Monotony 임계값 전후 Hooper 평균 비교

## 산출물
- `notebooks/track_B_eda.ipynb` (13셀, 합성 데모 데이터 포함)
- `reports/figures/` 관련 그림
