# docs/rnd/ — 연구·요구·통제·실행

R&D의 핵심 문서가 모인 디렉토리다. 상위 허브는 [../README.md](../README.md), 공통 기준은 [../standards/](../standards/README.md)를 참조한다.

## 읽는 순서

| 순서 | 문서 | 핵심 질문 |
|---:|---|---|
| 1 | [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) | 무엇을 검증하는가? |
| 2 | [TRD_v1.0.md](TRD_v1.0.md) | 무엇을 만족해야 하는가? |
| 3 | [GOVERNANCE.md](GOVERNANCE.md) | 어떤 기준으로 통제·승인하는가? |
| 4 | [PLAYBOOK.md](PLAYBOOK.md) | 어떻게 실행·재현하는가? |
| 5 | [DECISIONS.md](DECISIONS.md) | 왜 그렇게 결정했는가? |

## 하위 구조

| 경로 | 역할 |
|---|---|
| [INJURY_PREDICTION_REFERENCES.md](INJURY_PREDICTION_REFERENCES.md) | Stage 8 부상예측 문헌·데이터 |
| [requirements/](requirements/README.md) | 데이터 요구사항(DRD 이력)·현 명세(DATA_SPEC) |
| `tracks/track_A/` | HRV 중심(ACTES) 분석 문서 6종 |
| `tracks/track_B/` | 부하+설문(SoccerMon) 분석 문서 7종(INJURY_PREDICTION 포함) |

## 관계 규칙

- `RESEARCH_PROTOCOL → TRD → PLAYBOOK → tracks/`: 연구 설계를 요구사항·실행 절차·트랙 분석으로 전개.
- `GOVERNANCE → DECISIONS`: 통제 기준에 따라 결정을 ADR로 기록.
- 지표 수식·스키마·문헌은 여기서 정의하지 않고 [../standards/](../standards/README.md)를 **교차참조**한다(SSOT).
