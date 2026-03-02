# 리스크 레지스터 (skeptic 에이전트 산출물)

> 근거: `.claude/teams/config.json:117-127` (skeptic 에이전트 정의)
> 기본 가정: 항상 최악을 상정한다.

## 리스크 분류

| ID | 영역 | 리스크 | 심각도 | 가능성 | 현재 상태 | 완화 방안 | 근거 |
|----|------|--------|--------|--------|----------|----------|------|
| R-001 | 보안 | RLS 쓰기 정책 미구현 — Service Role Key로 우회 중 | **높음** | 확정 | 미해결 | MVP 이후 세분화된 쓰기 RLS 정책 추가 필요 | `docs/api/DB_SCHEMA.md:168` |
| R-002 | 보안 | GUEST 역할 투표 차단이 API에서 미검증 | **중간** | 높음 | 미해결 | 출석 투표 API에서 GUEST 역할 명시적 차단 로직 추가 | `docs/04_SECURITY_AND_ROLES/RBAC_MATRIX.md:51` |
| R-003 | 데이터 | soft delete 미적용 — hard delete로 데이터 복구 불가 | **중간** | 중간 | 수용 | MVP 범위에서 수용, 프로덕션 전 soft delete 전환 검토 | `docs/api/DB_SCHEMA.md:173` |
| R-004 | 인프라 | 마이그레이션 실행 방법 미정 (대시보드 vs CLI) | **낮음** | 확정 | 미해결 | Supabase CLI 기반 마이그레이션 파이프라인 문서화 필요 | `docs/api/DB_SCHEMA.md:175` |
| R-005 | 도메인 | 투표 마감 시간 자동 처리 로직 미정의 | **중간** | 높음 | 미해결 | 수동 확정으로 MVP 대체, 자동 마감은 MVP 이후 | `docs/product/MVP_STORIES.md:82` |
| R-006 | 보안 | UI에서 권한 없는 페이지 접근 허용 (API에서만 차단) | **중간** | 확정 | 수용 | MVP에서 수용, 프로덕션 전 미들웨어 레벨 접근 제어 추가 | `docs/04_SECURITY_AND_ROLES/RBAC_MATRIX.md:41` |
| R-007 | 테스트 | E2E 테스트 프레임워크(Playwright) 미설치 | **높음** | 확정 | 미해결 | Task 0020에서 결정 예정, 핵심 루프 검증 지연 리스크 | `docs/quality/TEST_STRATEGY.md:28` |
| R-008 | 동시성 | 경기 확정 중복 요청 시 기록실 생성 경합 | **낮음** | 낮음 | 해결 | record_rooms.match_id UNIQUE 제약으로 멱등성 보장 | `docs/api/DB_SCHEMA.md:109` |
| R-009 | 스코프 | 다중 팀 소속 UX 미정의 | **낮음** | 중간 | 미해결 | MVP에서 단일 팀 가정, 다중 팀은 MVP 이후 | `docs/product/MVP_STORIES.md:83` |
| R-010 | 인프라 | 프로덕션 배포 파이프라인 미정 | **중간** | 확정 | 미해결 | Vercel 기본 배포로 MVP 대응, CI/CD는 이후 구축 | `docs/05_OPERATIONS/DEPLOYMENT.md:62` |

## 최악 시나리오

1. **Service Role Key 노출**: RLS 전체 우회 가능 → 모든 테이블 무제한 접근. 완화: 환경변수 관리 철저, 클라이언트 코드에서 Service Role Key 참조 여부 정기 점검.
2. **투표 없는 경기 확정**: 0명 참석 상태에서 확정 가능 → 빈 기록실 생성. 완화: 최소 참석 인원 제약 추가 검토.
3. **E2E 미검증 배포**: 핵심 루프가 E2E로 보호되지 않은 상태에서 배포 → 회귀 버그. 완화: Playwright 설치 및 시나리오 5개 구현 우선.

## 검증 체크리스트

- [ ] R-001: Service Role Key가 클라이언트 번들에 포함되지 않는가?
- [ ] R-002: GUEST 역할로 투표 API 호출 시 403이 반환되는가?
- [ ] R-006: 미들웨어에서 역할 기반 라우트 가드가 적용되었는가?
- [ ] R-007: Playwright가 설치되고 CI에서 E2E가 실행되는가?
- [ ] 모든 [UNKNOWN] 항목에 검증 기한이 지정되었는가?
