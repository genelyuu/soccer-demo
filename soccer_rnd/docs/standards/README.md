# docs/standards/ — 공통 기준 (SSOT)

지표 수식·데이터 스키마·문헌처럼 **여러 문서가 반복 참조**하는 기준을 한곳에서 정의한다. 상위: [../README.md](../README.md).

| 문서 | 역할 |
|---|---|
| [METRICS_FORMULAS.md](METRICS_FORMULAS.md) | 지표 수식 원전(ATL/CTL/ACWR, Monotony/Strain, sRPE, Hooper, HRV). 모든 트랙·코드의 단일 출처 |
| [DATA_SCHEMA_MAPPING.md](DATA_SCHEMA_MAPPING.md) | 원천 데이터 → 표준 스키마 매핑(`src/data/loader.py`가 참조) |
| [REFERENCES.md](REFERENCES.md) | 참고 문헌 |

## SSOT 원칙

- 지표 수식은 **여기서만** 정의한다. 트랙 문서·코드 docstring·리포트는 정의를 복제하지 말고 이 문서를 **교차참조**한다.
- 수식·스키마 변경은 [../rnd/DECISIONS.md](../rnd/DECISIONS.md)에 ADR로 근거를 남긴다.
