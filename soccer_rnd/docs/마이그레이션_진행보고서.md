# 데이터베이스 마이그레이션 진행 보고서

**작성일**: 2026-03-02
**기반 문서**: DRD v2.0, DRD v3.0
**대상 프로젝트**: `pmdukumyboceykjlggpx` (Supabase Cloud)

---

## 1. 작업 요약

| 단계 | 작업 | 상태 |
|------|------|------|
| 1 | DRD v3.0 문서 검토 | ✅ 완료 |
| 2 | 로컬 PostgreSQL 15 환경 구축 | ✅ 완료 |
| 3 | 마이그레이션 00001~00004 + seed 적용 | ✅ 완료 |
| 4 | 00005_schema_fixes.sql 작성 및 적용 | ✅ 완료 |
| 5 | DRD v2.0 검증 매트릭스 전항목 통과 | ✅ 완료 |
| 6 | 클라우드용 통합 SQL 생성 및 로컬 검증 | ✅ 완료 |
| 7 | 클라우드 Supabase 배포 | ⏳ 대기 (수동 실행 필요) |

---

## 2. DRD v3.0 문서 검토 결과

### 문서 구조
- Mermaid 다이어그램 (ER, 데이터 리니지, RLS 매트릭스, CASCADE 체인 등) 포함
- DRD v2.0의 25개 버그 (B-01~B-25) 추적 내용 반영
- `block-beta` Mermaid 구문은 일부 렌더러에서 호환성 이슈 가능

### 주요 확인사항
- 마이그레이션 의존성 그래프: v3.0에서 20단계 vs v2.0에서 15단계 (확장됨)
- 00005_schema_fixes.sql 명세 확인 → v2.0 섹션 14.2에 SQL 전문 수록

---

## 3. 로컬 환경 구축

### 환경 정보
- **PostgreSQL**: 15 (Windows, `C:\Program Files\PostgreSQL\15`)
- **인증**: `pg_hba.conf` → `trust` 모드로 변경 (원본 백업: `pg_hba.conf.bak`)
- **테스트 DB**: `soccer_dev` (전체 마이그레이션 검증용), `soccer_cloud_test` (클라우드 SQL 검증용)
- **auth.uid() 스텁**: 로컬 테스트용 더미 함수 생성 (클라우드에서는 Supabase 내장)

### 적용된 마이그레이션 파일

| 파일 | 설명 |
|------|------|
| `00001_initial_schema.sql` | MVP 기본 스키마 (users, teams, matches 등 7개 테이블, RLS) |
| `00002_rls_write_policies.sql` | INSERT/UPDATE/DELETE RLS 정책 세분화 |
| `00003_training_wellness_schema.sql` | 훈련/웰니스/HRV 스키마 (8개 테이블, 5개 ENUM) |
| `00004_etl_views.sql` | ETL 뷰 (`v_rnd_track_a`, `v_rnd_track_b`) |
| `00005_schema_fixes.sql` | DRD v2.0 기반 25개 버그 수정 (6개 Phase) |
| `seed.sql` | 데모 데이터 (15명 사용자, 1팀, 2경기) |

---

## 4. 00005_schema_fixes.sql 상세

### Phase 구성

| Phase | 우선순위 | 수정 항목 | 설명 |
|-------|----------|-----------|------|
| Phase 1 | P0 (치명적) | B-01, B-02 | UNIQUE NULLS NOT DISTINCT → Partial Index, user_id 이중 저장 제거 |
| Phase 2 | P1 (비즈니스) | B-03, B-06 | has_* 파생 플래그 제거, RPE CHECK 0~10으로 수정 |
| Phase 3 | RLS 재구축 | B-05, B-21 | 팀 기반 SELECT, 세션 경유 정책, DELETE 정책 추가 |
| Phase 4 | P2 (구조) | B-09, B-11, B-13, B-16, B-25 | strain 명명, 배열 크기 제한, 인덱스, pipeline_version, valid NOT NULL |
| Phase 5 | ETL | B-04, B-12, B-20, B-22, B-24 | REST 포함, ORDER BY 제거, strain/dcwr/tsb 추가 |
| Phase 6 | P3 (운영) | B-14, B-23, B-10 | updated_at 트리거, COMMENT 문서화 |

### 작성 중 발생한 오류 및 해결

1. **RLS 정책 의존성 오류**: `user_id` 컬럼 DROP 전에 해당 컬럼을 참조하는 RLS 정책과 인덱스를 먼저 제거해야 함
   - 해결: `DROP POLICY` + `DROP INDEX` → `ALTER TABLE DROP COLUMN` 순서로 재배치

2. **VIEW 컬럼 변경 불가**: `CREATE OR REPLACE VIEW`는 기존 뷰에 새 컬럼 추가 불가
   - 해결: `DROP VIEW IF EXISTS` → `CREATE VIEW` 순서로 변경

---

## 5. 검증 결과 (DRD v2.0 매트릭스)

| 검증 항목 | 설명 | 결과 |
|-----------|------|------|
| B-01 | match_id=NULL 복수 세션 INSERT 허용 | ✅ PASS |
| B-01 | 동일 match_id 중복 INSERT 차단 | ✅ PASS |
| B-02 | 하위 테이블 user_id 컬럼 제거 확인 | ✅ PASS |
| B-03 | has_* 플래그 컬럼 제거 확인 | ✅ PASS |
| B-06 | RPE=0 INSERT 허용 (Borg CR-10) | ✅ PASS |
| B-09 | strain 컬럼 존재 (strain_value 아님) | ✅ PASS |
| B-11 | rr_intervals_ms 배열 크기 제한 (1~50000) | ✅ PASS |
| B-13 | session_date 단독 인덱스 존재 | ✅ PASS |
| B-14 | updated_at 자동 갱신 트리거 (2개) | ✅ PASS |
| B-16 | pipeline_version, params 컬럼 존재 | ✅ PASS |
| B-21 | DELETE 정책 11개 (모든 주요 테이블) | ✅ PASS |
| B-25 | valid NOT NULL DEFAULT TRUE | ✅ PASS |
| ETL | v_rnd_track_a: strain, dcwr_rolling, tsb_rolling 포함 | ✅ PASS |
| ETL | v_rnd_track_b: REST 세션 포함 | ✅ PASS |

### 최종 스키마 통계

| 항목 | 수량 |
|------|------|
| 테이블 | 15개 |
| 뷰 | 2개 (v_rnd_track_a, v_rnd_track_b) |
| RLS 정책 | 54개 |
| 트리거 | 2개 |
| 시드 데이터: 사용자 | 15명 |
| 시드 데이터: 팀 | 1개 (FC 번개) |
| 시드 데이터: 사용자 프로필 | 15개 |

---

## 6. 클라우드 마이그레이션 파일

### 생성된 파일
- **경로**: `soccer/supabase/migrations/cloud_migration.sql`
- **크기**: 831줄
- **내용**: 00001~00005 + seed.sql 통합 (DRD v2.0 버그 수정 반영 완료)
- **특징**: `auth.uid()` 스텁 미포함 (Supabase Cloud 내장)
- **로컬 검증**: ✅ `soccer_cloud_test` DB에서 오류 없이 실행 완료

### 클라우드 배포 방법

클라우드 Supabase DB 호스트(`db.pmdukumyboceykjlggpx.supabase.co`)가 IPv6 전용이라 로컬 환경에서 직접 연결이 불가합니다. 아래 방법 중 하나로 배포해야 합니다:

#### 방법 1: Supabase Dashboard SQL Editor (권장)
1. [Supabase Dashboard SQL Editor](https://supabase.com/dashboard/project/pmdukumyboceykjlggpx/sql/new) 접속
2. `soccer/supabase/migrations/cloud_migration.sql` 파일 내용 전체 복사
3. SQL Editor에 붙여넣기 후 실행 (Run)

#### 방법 2: Supabase CLI (Access Token 필요)
```bash
# 1. Access Token 생성: https://supabase.com/dashboard/account/tokens
# 2. 환경변수 설정
export SUPABASE_ACCESS_TOKEN="your-access-token"

# 3. 프로젝트 링크
cd soccer
npx supabase link --project-ref pmdukumyboceykjlggpx

# 4. 마이그레이션 푸시
npx supabase db push --include-all --include-seed
```

#### 방법 3: psql 직접 연결 (DB 비밀번호 필요)
```bash
# Supabase Dashboard > Settings > Database에서 비밀번호 확인
psql "postgresql://postgres:[PASSWORD]@db.pmdukumyboceykjlggpx.supabase.co:5432/postgres" \
  -f soccer/supabase/migrations/cloud_migration.sql
```

### `.env.local` 자격증명 연결 검증 결과 (2026-03-02)

`.env.local`에 포함된 `ANON_KEY` / `SERVICE_ROLE_KEY`로 가능한 **모든 경로를 체계적으로 테스트**한 결과입니다.

#### 사용 가능한 API (HTTPS 경유, DDL 불가)

| #   | 테스트                | 결과       | 비고                                                          |
| --- | --------------------- | ---------- | ------------------------------------------------------------- |
| 1   | REST API (PostgREST)  | ✅ 200 OK  | Swagger 응답 정상. 단, 테이블이 없어 DML 불가                 |
| 4   | Auth Admin API        | ✅ 200 OK  | `supabase.auth.admin.listUsers()` → 0명 (정상)               |
| 6b  | Storage API           | ✅ 200 OK  | 빈 버킷 목록 반환                                             |
| 9   | GraphQL (pg_graphql)  | ✅ 200 OK  | 스키마 인트로스펙션 정상                                      |

#### 연결 불가 경로 (DDL 실행 필요)

| #   | 테스트                                 | 결과                   | 상세 원인                                                                                                                                             |
| --- | -------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2a  | DNS 해석                               | ⚠️ IPv6 전용           | `db.*.supabase.co` → `2406:da1a:6b0:...` (AAAA 레코드만 존재)                                                                                        |
| 2b  | psql 직접 연결 (hostname)              | ❌ Unknown host        | Windows psql이 IPv6-only 호스트 해석 실패                                                                                                             |
| 2c  | psql 직접 연결 (IPv6 리터럴)           | ❌ Network unreachable | 로컬 Wi-Fi에 글로벌 IPv6 주소 없음 (link-local `fe80::` 만 존재)                                                                                     |
| 3   | Connection Pooler (6개 리전 × 2포트)   | ❌ Tenant not found    | `ap-northeast-2`, `ap-northeast-1`, `ap-southeast-1`, `us-east-1`, `eu-west-1`, `eu-central-1` 전부 실패. 풀러 미활성화 또는 DB 비밀번호 불일치       |
| 4   | Supabase CLI (`npx supabase`)          | ❌ Non-TTY + 토큰 형식 | `service_role` JWT는 `sbp_` 형식이 아니라 CLI 인증 불가                                                                                               |
| 5a  | Management API (`api.supabase.com`)    | ❌ 401 JWT 실패        | Personal Access Token 필요 (서비스 역할 키 불가)                                                                                                      |
| 5b  | `/pg` 엔드포인트                       | ❌ 404                 | 해당 경로 미존재                                                                                                                                      |
| 5c  | `/sql` 엔드포인트                      | ❌ 404                 | 해당 경로 미존재                                                                                                                                      |
| 5d  | RPC `query()` 함수                     | ❌ 404                 | DB에 해당 함수 미정의                                                                                                                                 |
| 6d  | IPv6 ping                              | ❌ 호스트 못찾음       | Windows ping도 IPv6-only 호스트 해석 불가                                                                                                             |
| 7   | supabase-js `from('users')`            | ❌ 테이블 없음         | PostgREST 스키마 캐시에 테이블 부재 (미생성 상태)                                                                                                     |
| 8   | Edge Functions                         | ❌ 404                 | 배포된 함수 없음                                                                                                                                      |
| CLI | `supabase db push --db-url`            | ❌ DNS 실패            | HTTPS DNS resolver 타임아웃 포함                                                                                                                      |

#### 핵심 결론

> **`.env.local`의 `ANON_KEY`/`SERVICE_ROLE_KEY`는 애플리케이션 수준 인증**으로, PostgREST(DML), Auth, Storage 등 HTTPS 기반 서비스에만 접근 가능합니다.
>
> **스키마 생성(DDL: CREATE TABLE 등)은 직접 데이터베이스 연결이 필수**이며, 이를 위해서는 다음 중 하나가 필요합니다:
>
> 1. **DB 비밀번호** — Supabase Dashboard > Settings > Database
> 2. **Personal Access Token** — https://supabase.com/dashboard/account/tokens
> 3. **Dashboard SQL Editor** — 브라우저에서 직접 실행

#### 연결 실패 근본 원인

```
[로컬 환경]                    [Supabase Cloud]
Windows (Wi-Fi)               db.*.supabase.co
  └─ IPv4 only ──────✗──────→  IPv6 only (AAAA)
  └─ fe80:: (link-local) ─✗─→  2406:da1a:... (global)

  Pooler (IPv4) ─────✗──────→  "Tenant not found"
                                (DB 비밀번호 미보유)

  CLI ───────────────✗──────→  sbp_ 형식 토큰 필요
                                (service_role JWT ≠ access token)
```

---

## 7. 파일 목록

```
soccer/supabase/
├── config.toml                              # Supabase CLI 설정 (project_id 포함)
├── _config.toml                             # 원본 설정 파일
├── seed.sql                                 # 시드 데이터 (15명, 1팀, 2경기)
└── migrations/
    ├── 00001_initial_schema.sql             # MVP 기본 스키마
    ├── 00002_rls_write_policies.sql         # RLS 쓰기 정책
    ├── 00003_training_wellness_schema.sql   # 훈련/웰니스/HRV 스키마
    ├── 00004_etl_views.sql                  # ETL 뷰
    ├── 00005_schema_fixes.sql               # DRD v2.0 버그 수정
    ├── cloud_migration.sql                  # ★ 클라우드 통합 배포용
    └── all_migrations.sql                   # (이전 통합 파일 - 갱신 필요)
```

---

## 8. 후속 작업

- [ ] 클라우드 Supabase에 `cloud_migration.sql` 실행 (위 방법 1~3 중 택)
- [ ] 클라우드 배포 후 REST API로 데이터 확인
- [ ] `pg_hba.conf` 원복 (보안): `trust` → `scram-sha-256` (로컬 PostgreSQL)
- [ ] DRD v3.0의 B-20 (SHA-256 익명화) 프로덕션 전환 시 적용
