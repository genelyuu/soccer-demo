# 트랙 B 통계 계획

> 목적: 부하 구조(ACWR, Monotony)가 다음날 웰니스(Hooper Index)를 설명하는지 검증

## 핵심 모형

```
Hooper_{t+1} ~ ACWR_t + Monotony_t + (1|athlete)
```

## 모형 비교 전략 (4개 모형)

| 모형 | 수식 | 목적 |
|------|------|------|
| M1: OLS 베이스라인 | hooper_next ~ acwr_rolling | 단순 회귀 기준선 |
| M2: Mixed (ACWR만) | hooper_next ~ acwr_rolling + (1\|athlete) | 개인 랜덤효과 추가 |
| M3: Mixed (ACWR + Monotony) | hooper_next ~ acwr_rolling + monotony + (1\|athlete) | Monotony 추가 효과 |
| M4: Mixed (EWMA + Monotony) | hooper_next ~ acwr_ewma + monotony + (1\|athlete) | EWMA 방식 비교 |

## 평가 지표
- AIC, BIC — 모형 복잡도 대비 적합도
- MAE, RMSE — 예측 정확도
- Cohen's f² — 효과크기
- 고정효과 계수 방향 및 p-value

## 기대 패턴
- ACWR 계수: 양의 방향 (부하↑ → 다음날 Hooper↑, 즉 웰니스 악화)
- Monotony 계수: 양의 방향 (단조로운 훈련 → 웰니스 악화)
- Mixed > OLS (개인차 반영으로 적합도 개선)
- M3/M4 > M2 (Monotony 추가의 설명력)

## 산출물
- `notebooks/track_B_stats.ipynb` (15셀)
- `reports/track_B_model_comparison.md`
