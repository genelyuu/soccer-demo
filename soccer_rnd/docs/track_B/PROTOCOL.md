# 트랙 B 프로토콜 (부하 + 설문)

## 목적
부하 구조(ACWR, Monotony, Strain)가 선수 웰니스(Hooper Index)에 미치는 시차 효과를 정량적으로 설명한다.

## 데이터셋
- 1순위: Carey et al. (Zenodo, CC BY 4.0) — AFL 프로 선수 ~45명, 1시즌
- 컬럼 매핑: fatigue→fatigue, sleep quality→sleep, muscle soreness→DOMS, stress→stress
- mood 항목은 Hooper Index 산출에서 제외 (별도 보조 분석 가능)

## 핵심 지표
- **독립변수**: sRPE, ACWR (rolling/EWMA), Monotony, Strain
- **종속변수**: Hooper Index (다음날, t+1)
- **통제**: 개인 랜덤효과 (1|athlete)

## 분석 흐름
1. 데이터 품질 점검 → 결측/이상치 파악
2. 주간 부하 패턴 탐색 → 요일별/세션유형별 차이
3. 시차(lag) 관계 탐색 → ACWR(t) vs Hooper(t+1)
4. Monotony/Strain 역할 탐색
5. 혼합효과모형 적합 → 모형 비교 (AIC/BIC/MAE/RMSE)
6. 효과크기 보고 및 해석

## 결과변수 정의
- Hooper Index = fatigue + stress + DOMS + sleep (1-7 스케일, 총점 4-28)
- 높은 값 = 나쁜 웰니스 상태

## 품질 기준
- 재현성: np.random.seed(42), 파라미터 문서화
- reviewer-safe 톤: "시사한다/관찰된다/일관된 경향"
- ACWR 단독 사용 한계 명시 (Impellizzeri et al., 2020)
