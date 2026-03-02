# PoV 데이터베이스 설계 버그 리포트

> **대상 파일**: `soccer/supabase/migrations/00003_training_wellness_schema.sql`, `00004_etl_views.sql`, `seed.sql`
> **작성일**: 2026-02-11
> **검토 범위**: 00003 마이그레이션(ENUM 5종, 테이블 8개, RLS 16개), 00004 ETL 뷰 2개, seed.sql 확장부

---

## 1. 심각도 정의

| 등급 | 의미 | 기준 |
|:----:|------|------|
| **P0 — 치명** | 데이터 손실, 삽입 실패, 무결성 파괴 | 운영 환경 적용 시 즉시 장애 발생 |
| **P1 — 높음** | 비즈니스 로직 오류, 분석 결과 왜곡 | 기능은 동작하나 결과가 부정확 |
| **P2 — 중간** | 구조적 비효율, 유지보수 비용 증가 | 당장 장애는 아니나 기술 부채 누적 |
| **P3 — 낮음** | 컨벤션 불일치, 문서-구현 괴리 | 가독성·협업 효율 저하 |

---

## 2. 전체 버그 요약

| # | 심각도 | 분류 | 제목 | 위치 | 상태 |
|:-:|:------:|------|------|------|:----:|
| B-01 | **P0** | 무결성 | NULLS NOT DISTINCT로 훈련 세션 1개 제한 | 00003 L61 | 미수정 |
| B-02 | **P0** | 무결성 | user_id 이중 저장 — 불일치 방지 장치 없음 | 00003 L81,110,135 | 미수정 |
| B-03 | **P1** | 동기화 | has_* 플래그 — 트리거 없는 파생 데이터 | 00003 L54-56 | 미수정 |
| B-04 | **P1** | 의미론 | ETL 뷰 v_rnd_track_b에서 REST 일 누락 | 00004 L42 | 미수정 |
| B-05 | **P1** | 보안 | RLS "본인만" 정책 — 코치/매니저 조회 불가 | 00003 전체 RLS | 미수정 |
| B-06 | **P1** | 도메인 | session_rpe CHECK 1~10 — CR-10 스케일의 0 누락 | 00003 L112 | 미수정 |
| B-07 | **P2** | 정규화 | user_profiles 1:1 분리의 실익 부족 | 00003 L18-31 | 미수정 |
| B-08 | **P2** | 정규화 | Surrogate Key(id UUID) 남용 | 00003 L79,107,132 | 미수정 |
| B-09 | **P2** | 추적성 | computed_load_metrics — 산출 파라미터·이력 없음 | 00003 L156-180 | 미수정 |
| B-10 | **P2** | 모델링 | daily_hrv_metrics.measurement_id 다대일 모호 | 00003 L230 | 미수정 |
| B-11 | **P2** | 성능 | rr_intervals_ms FLOAT[] 크기 제한 없음 | 00003 L203 | 미수정 |
| B-12 | **P2** | 성능 | 뷰 ORDER BY — 무의미한 정렬 비용 | 00004 L43,73 | 미수정 |
| B-13 | **P2** | 성능 | session_date 단독 인덱스 누락 | 00003 L64 | 미수정 |
| B-14 | **P2** | 운영 | updated_at 자동 갱신 트리거 부재 | 00003 L30,58 | 미수정 |
| B-15 | **P3** | 컨벤션 | ENUM vs CHECK 혼재 | 00003 L9,23 | 미수정 |
| B-16 | **P3** | 컨벤션 | strain vs strain_value 명명 불일치 | 00003 L170 | 미수정 |
| B-17 | **P3** | 컨벤션 | soreness vs doms 이름 분기 | 00003 L84 / 00004 L24 | 미수정 |
| B-18 | **P3** | 보안 | phone TEXT 평문 — 문서의 암호화 요건 미반영 | 00003 L22 | 미수정 |
| B-19 | **P3** | 보안 | computed_load_metrics UPDATE 정책 없음 | 00003 L184-188 | 미수정 |

---

## 3. 상세 분석

### B-01 | P0 — NULLS NOT DISTINCT로 훈련 세션 1개 제한

| 항목 | 내용 |
|------|------|
| **위치** | `00003_training_wellness_schema.sql` L61 |
| **현재 코드** | `UNIQUE NULLS NOT DISTINCT (user_id, match_id)` |
| **증상** | TRAINING/REST/OTHER 세션은 `match_id=NULL`이므로, 사용자당 **경기 외 세션이 전체 기간 통틀어 1개**만 INSERT 가능. 두 번째 훈련 세션 INSERT 시 unique violation 발생. |
| **영향 범위** | training_sessions 테이블 전체. 120일 × 15명 × 6일/주 ≈ 1,500개 훈련 세션이 필요하나 15개만 삽입 가능. |
| **근본 원인** | `NULLS NOT DISTINCT`는 NULL을 동등하게 취급하여, `(user_A, NULL)` 쌍이 유일해야 한다고 강제함. "같은 경기 중복 방지"와 "다수 훈련 허용"을 하나의 제약으로 해결하려 한 설계 오류. |
| **미발견 이유** | 합성 데이터 생성(`generate_seed_data.py`)이 CSV 직접 생성 방식이라 DB 제약을 거치지 않음. `export_seed_sql.py`의 INSERT를 실제 PostgreSQL에 실행하면 즉시 발견됨. |
| **수정 방안** | UNIQUE 제약 제거 후, 경기 세션에만 적용되는 partial unique index로 교체: |
| **수정 SQL** | `CREATE UNIQUE INDEX idx_sessions_user_match ON training_sessions(user_id, match_id) WHERE match_id IS NOT NULL;` |
| **검증 방법** | 동일 사용자로 `match_id=NULL`인 행 2개 INSERT 성공 확인 |

---

### B-02 | P0 — user_id 이중 저장, 불일치 방지 장치 없음

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L81(`pre_session_wellness`), L110(`post_session_feedback`), L135(`next_day_reviews`) |
| **현재 코드** | 세 테이블 모두 `session_id UUID REFERENCES training_sessions(id)` + `user_id UUID REFERENCES users(id)` 보유 |
| **증상** | `session_id`를 통해 `training_sessions.user_id`를 JOIN으로 얻을 수 있으므로 `user_id`는 파생 데이터. 그러나 두 `user_id`가 불일치하는 것을 방지하는 **CHECK, 트리거, FK 조합 제약이 없음**. |
| **구체적 시나리오** | 사용자 A의 세션(session.user_id='A')에 사용자 B가 wellness 행을 `user_id='B'`로 INSERT → DB는 수용. RLS가 `user_id = auth.uid()`이므로, B가 A의 세션에 자신의 웰니스를 연결하는 논리적 오류 발생. |
| **영향 범위** | 3개 하위 테이블 × 전체 행. R&D 파이프라인에서 user_id 기준 집계 시 소속 세션과 불일치하면 분석 결과 왜곡. |
| **수정 방안 A** | `user_id` 컬럼 제거. RLS를 `session_id`를 통한 JOIN으로 전환: |
| | `USING (session_id IN (SELECT id FROM training_sessions WHERE user_id = auth.uid()))` |
| **수정 방안 B** | 비정규화 유지 시, FK를 복합키로 강화하고 `BEFORE INSERT` 트리거로 일관성 보장: |
| | `CREATE FUNCTION check_session_user() ... IF NEW.user_id != (SELECT user_id FROM training_sessions WHERE id = NEW.session_id) THEN RAISE ...` |
| **권장** | 방안 A (정규화). RLS 서브쿼리 비용은 `session_id` UNIQUE 인덱스로 O(1). |

---

### B-03 | P1 — has_* 플래그, 트리거 없는 파생 데이터

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L54-56 (`has_pre_wellness`, `has_post_feedback`, `has_next_day_review`) |
| **현재 코드** | `has_pre_wellness BOOLEAN DEFAULT FALSE` — 수동 갱신 의존 |
| **증상** | 하위 테이블에 행이 INSERT/DELETE되어도 플래그가 자동 갱신되지 않음. 애플리케이션 레이어에서 두 번의 INSERT(하위 행 + 플래그 UPDATE)를 트랜잭션으로 묶어야 하며, 하나라도 실패하면 불일치 발생. |
| **영향 범위** | 클라이언트 UI에서 "입력 완료 여부" 표시가 실제와 불일치 가능. 푸시 알림 트리거가 이 플래그에 의존하면 누락/중복 알림 발생. |
| **수정 방안 A** | 플래그 3개 제거. 조회 시 `EXISTS` 서브쿼리로 동적 판별: |
| | `SELECT *, EXISTS(SELECT 1 FROM pre_session_wellness pw WHERE pw.session_id = ts.id) AS has_pre_wellness FROM training_sessions ts` |
| **수정 방안 B** | `AFTER INSERT/DELETE` 트리거로 플래그 자동 갱신: |
| | `CREATE FUNCTION sync_has_pre() ... UPDATE training_sessions SET has_pre_wellness = TRUE WHERE id = NEW.session_id;` |
| **권장** | 방안 A. 성능 차이는 UNIQUE 인덱스 덕에 무시할 수준이며, 데이터 정합성이 구조적으로 보장됨. |

---

### B-04 | P1 — ETL 뷰 v_rnd_track_b에서 REST 일 누락

| 항목 | 내용 |
|------|------|
| **위치** | `00004_etl_views.sql` L42 |
| **현재 코드** | `WHERE ps.session_rpe IS NOT NULL` |
| **증상** | REST 세션은 `post_session_feedback` 행이 없으므로(`session_rpe IS NULL`), 뷰에서 완전히 제외됨. |
| **분석 결과 왜곡** | ACWR = ATL(7일)/CTL(28일). REST일(sRPE=0)이 빠지면 rolling window에 간극 발생 → ATL이 실제보다 높게 산출 → ACWR 과대추정. `data_migration.md`에도 "REST일: sRPE=0 (의도적 0, 결측 아님)"으로 명시. |
| **영향 범위** | `v_rnd_track_b` → `compute_daily_load_metrics()` → ACWR/Monotony/Strain 전체 왜곡 → 혼합효과모형·LOSO CV 결과에 전파. |
| **수정 SQL** | `WHERE ps.session_rpe IS NOT NULL` 제거 후, REST 세션을 sRPE=0으로 포함: |
| | `WHERE ts.session_type != 'REST' AND ps.session_rpe IS NOT NULL` → `OR ts.session_type = 'REST'` 추가, REST일의 srpe를 `COALESCE(ps.session_rpe * ts.duration_min, 0)` 처리 |
| **검증 방법** | 뷰 결과에서 `session_type='REST'` 행이 존재하고 `srpe=0`인지 확인 |

---

### B-05 | P1 — RLS "본인만" 정책, 코치/매니저 조회 불가

| 항목 | 내용 |
|------|------|
| **위치** | `00003` 전체 RLS 정책 (L34-39, L68-73, L97-102, L121-127, L145-151, L184-188, L216-220, L252-256) |
| **현재 코드** | 모든 신규 테이블: `USING (user_id = auth.uid())` |
| **기존 패턴과 충돌** | 00001의 `matches_read_team`, `attendances_read_team` 등은 **같은 팀이면 조회 가능**. 신규 테이블만 **본인만** 정책 적용. |
| **증상** | ADMIN/MANAGER 역할의 코치가 선수의 훈련 세션, 웰니스, ACWR, HRV를 조회할 수 없음. 팀 수준의 부하 관리 대시보드 구현 불가. |
| **영향 범위** | 신규 8개 테이블 전부. 서비스 MVP의 핵심 기능(팀 부하 모니터링)이 RLS에 의해 차단됨. |
| **수정 방안** | 기존 팀 기반 패턴 적용. 예시: |
| | `CREATE POLICY "sessions_read_team" ON training_sessions FOR SELECT USING (user_id = auth.uid() OR team_id IN (SELECT team_id FROM team_members WHERE user_id = auth.uid() AND role IN ('ADMIN', 'MANAGER')));` |
| **고려사항** | 하위 테이블(wellness, feedback)에 `team_id`가 없으므로, `session_id`를 통한 JOIN 또는 `user_id IN (같은 팀 멤버)` 조건 필요 |

---

### B-06 | P1 — session_rpe CHECK 범위 오류 (CR-10 스케일)

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L112 |
| **현재 코드** | `session_rpe SMALLINT NOT NULL CHECK (session_rpe BETWEEN 1 AND 10)` |
| **문제** | Borg CR-10 스케일은 **0**(Nothing at all)부터 시작. 현재 CHECK는 0을 거부함. |
| **영향** | "참여했지만 활동이 거의 없는" 세션(워밍업만 참여 후 빠진 경우 등)의 RPE=0을 기록할 수 없음. sRPE=0×duration=0을 표현 불가. |
| **수정 SQL** | `CHECK (session_rpe BETWEEN 0 AND 10)` |
| **참조** | Foster et al. (2001), "A New Approach to Monitoring Exercise Training" — CR-10 스케일 0~10 정의 |

---

### B-07 | P2 — user_profiles 1:1 분리의 실익 부족

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L18-31 |
| **현상** | `users`와 1:1 관계. `phone`과 `position` 두 컬럼만 보유. |
| **비효율** | 매 조회마다 `LEFT JOIN user_profiles` 필요. 시드에서 15명 전원 profile 생성하므로 "선택적 생성"의 이점 없음. |
| **근본 질문** | Supabase Auth에서 `auth.users`와 `public.users`가 분리되어 있어 `public.users`에 컬럼 추가가 자유로운지 여부. 자유롭다면 `ALTER TABLE users ADD COLUMN`이 단순. |
| **수정 방안** | `ALTER TABLE users ADD COLUMN phone TEXT, ADD COLUMN position TEXT CHECK (...)`. `user_profiles` 테이블 및 관련 RLS 제거. |
| **유보 조건** | "프로필은 별도 접근 권한"이 향후 요구되면 분리 정당화 가능. 그 경우 ADR로 의사결정 기록 필요. |

---

### B-08 | P2 — Surrogate Key(id UUID) 남용

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L79(`pre_session_wellness`), L107(`post_session_feedback`), L132(`next_day_reviews`) |
| **현상** | 세 테이블 모두 `id UUID PK` + `session_id UUID UNIQUE NOT NULL`. `session_id`가 자연 PK 역할 가능. |
| **비효율** | PK 인덱스 + UNIQUE 인덱스 = 인덱스 2개 유지. UUID 16바이트 × 행 수 × 3 테이블 = 불필요한 저장 비용. |
| **혼란** | 다른 테이블에서 FK 참조 시 `id`와 `session_id` 중 어느 것을 사용해야 하는지 모호. |
| **수정 방안** | `session_id`를 PK로 승격. `id` 컬럼 제거: |
| | `session_id UUID PRIMARY KEY REFERENCES training_sessions(id) ON DELETE CASCADE` |
| **유보 조건** | Supabase 클라이언트 라이브러리가 `id` PK 컨벤션에 의존하는 경우 유지 필요. 확인 후 결정. |

---

### B-09 | P2 — computed_load_metrics 산출 파라미터·이력 없음

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L156-180 |
| **현상** | ACWR window(7/28), EWMA span, Monotony window 등 산출 파라미터가 스키마에 기록되지 않음. `UNIQUE(user_id, metric_date)` + UPSERT 시 이전 값이 덮어쓰기되어 이력 소멸. |
| **위반 기준** | CLAUDE.md 품질 기준: "모든 지표/그림/표는 산출 코드 위치와 파라미터를 역추적 가능" — 추적성 위반 |
| **영향** | 파라미터 변경 후 재산출 시, 이전 결과와 비교 불가. "이 ACWR이 window=7로 산출된 건지 확인할 수 없음". |
| **수정 방안 A** | 파라미터 컬럼 추가: `atl_window INT DEFAULT 7`, `ctl_window INT DEFAULT 28`, `pipeline_version TEXT` |
| **수정 방안 B** | 이력 테이블 분리: `computed_load_metrics_history`에 old 행 보관, 현재 테이블은 최신만 유지 |
| **최소 수정** | `pipeline_version TEXT`, `params JSONB` 컬럼 추가로 산출 맥락 기록 |

---

### B-10 | P2 — daily_hrv_metrics.measurement_id 다대일 모호

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L230 |
| **현상** | 하루에 HRV 측정이 여러 번 가능(MORNING_REST, PRE_SESSION 등). `UNIQUE(user_id, metric_date)`이므로 일별 1행인데, `measurement_id`는 FK 1개만 참조. |
| **문제** | **어떤 측정을 대표로 선택하는 기준**이 스키마에 없음. MORNING_REST 우선? 가장 긴 측정 우선? rr_count 최대? |
| **영향** | ETL 파이프라인 구현자마다 다른 선택 기준을 적용할 위험. 분석 재현성 저하. |
| **수정 방안** | `selection_rule TEXT CHECK (selection_rule IN ('MORNING_FIRST', 'LONGEST', 'BEST_QUALITY'))` 컬럼 추가, 또는 `COMMENT ON COLUMN`으로 선택 기준 명시 |

---

### B-11 | P2 — rr_intervals_ms FLOAT[] 크기 제한 없음

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L203 |
| **현재 코드** | `rr_intervals_ms FLOAT[] NOT NULL` |
| **위험** | `NIGHT_SLEEP` 컨텍스트 8시간 측정 시 ~30,000개 beat ≈ 240KB/행. 크기 제한 없이 TOAST 처리되며, 단일 행 SELECT에도 큰 I/O 발생. 악의적·실수로 수백만 개 배열 INSERT 가능. |
| **수정 SQL** | `CHECK (array_length(rr_intervals_ms, 1) BETWEEN 1 AND 50000)` 추가 |
| **대안** | 장시간 측정은 청크 분할: 5분 단위로 별도 행 저장, `chunk_index INT` 추가 |

---

### B-12 | P2 — 뷰 ORDER BY 무의미

| 항목 | 내용 |
|------|------|
| **위치** | `00004` L43, L73 |
| **현재 코드** | `ORDER BY ts.user_id, ts.session_date` / `ORDER BY h.user_id, h.metric_date` |
| **문제** | SQL 표준상 뷰의 `ORDER BY`는 보장되지 않음. `SELECT * FROM v_rnd_track_b`에 별도 `ORDER BY`를 붙여야 하므로, 뷰 정의 내 `ORDER BY`는 불필요한 정렬 비용만 추가. PostgreSQL 옵티마이저가 제거할 수도 있으나, 의미론적으로 잘못된 기대를 유발. |
| **수정** | 뷰 정의에서 `ORDER BY` 절 제거 |

---

### B-13 | P2 — session_date 단독 인덱스 누락

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L64 |
| **현재 인덱스** | `idx_sessions_user_date ON training_sessions(user_id, session_date)` — 복합 인덱스 |
| **문제** | ETL 뷰·배치에서 `WHERE session_date BETWEEN ... AND ...` 날짜 범위 필터가 빈번. 복합 인덱스는 선행 컬럼(`user_id`) 없이 후행 컬럼(`session_date`) 단독 조건에 비효율적. |
| **수정 SQL** | `CREATE INDEX idx_sessions_date ON training_sessions(session_date);` 추가 |

---

### B-14 | P2 — updated_at 자동 갱신 트리거 부재

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L30(`user_profiles`), L58(`training_sessions`) |
| **현상** | `updated_at TIMESTAMPTZ DEFAULT now()` — INSERT 시점만 기록. UPDATE 시 자동 갱신 없음. |
| **영향** | `updated_at`이 영원히 `created_at`과 동일한 값. 변경 이력 추적 불가. |
| **수정 SQL** | 공용 트리거 함수 생성: |
| | `CREATE FUNCTION update_updated_at() RETURNS TRIGGER AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END; $$ LANGUAGE plpgsql;` |
| | `CREATE TRIGGER trg_user_profiles_updated BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();` |
| **비고** | 기존 00001도 동일 문제 보유. 확장 시 같이 해결 권장. |

---

### B-15 | P3 — ENUM vs CHECK 혼재

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L9(ENUM 5종), L23(CHECK IN) |
| **현상** | `session_type`, `post_condition` 등은 ENUM. `position`(14개 값)은 TEXT + CHECK IN(...). 동일 마이그레이션 내 두 패턴 혼재. |
| **판단 기준 부재** | "어떤 경우 ENUM, 어떤 경우 CHECK"의 결정 기준이 문서화되지 않음. |
| **참고** | PostgreSQL ENUM은 `ALTER TYPE ADD VALUE`로 확장 가능하나 값 제거 불가. 변경 빈도 높은 값(포지션)은 CHECK가 합리적일 수 있으나, 그 판단이 ADR에 없음. |
| **수정 방안** | docs/DECISIONS.md에 ADR 추가: "ENUM은 상태 머신(상태 전이가 명확한 경우), CHECK는 열거형 목록(변경 가능성 있는 경우)"와 같은 기준 명시 |

---

### B-16 | P3 — strain vs strain_value 명명 불일치

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L170 (`computed_load_metrics.strain_value`) |
| **불일치** | R&D 모듈(`monotony_strain.py`): `strain`. CSV 출력: `strain`. DB 컬럼: `strain_value`. ETL 뷰: 매핑 없음. |
| **영향** | 파이프라인에서 컬럼명 변환이 필요. 매핑 누락 시 `KeyError` 또는 조용한 NULL. |
| **수정** | DB 컬럼명을 `strain`으로 통일. PostgreSQL 예약어와 충돌 없음. |

---

### B-17 | P3 — soreness vs doms 이름 분기

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L84 (`pre_session_wellness.soreness`), `00004` L24 (`pw.soreness AS doms`) |
| **현상** | 서비스 측: `soreness`. R&D 측: `doms`. 뷰에서 alias로 변환. |
| **영향** | 코드베이스 전체에서 "이 두 이름이 같은 개념"이라는 매핑 지식이 암묵적으로만 존재. 신규 개발자 혼란. |
| **수정 방안** | 서비스 측 컬럼명을 `doms`로 통일하거나, docs/DATA_SCHEMA_MAPPING.md에 매핑 테이블 명시 |

---

### B-18 | P3 — phone TEXT 평문 저장

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L22 |
| **현상** | `data_migration.md`에 "AES-256 암호화, 출력 시 마스킹" 요건 기술. DDL은 `phone TEXT` 평문. |
| **영향** | DB 접근 권한이 있는 누구든 전화번호 평문 조회 가능. 개인정보보호법 위반 가능성. |
| **수정 방안 A** | `pgcrypto` 확장 활용: `phone BYTEA` + `pgp_sym_encrypt()/pgp_sym_decrypt()` |
| **수정 방안 B** | 애플리케이션 레이어 암호화 위임 시, `COMMENT ON COLUMN user_profiles.phone IS 'AES-256 암호화 필수. 평문 저장 금지.'` 최소 명시 |

---

### B-19 | P3 — computed_load_metrics UPDATE 정책 없음

| 항목 | 내용 |
|------|------|
| **위치** | `00003` L184-188 |
| **현재 정책** | SELECT(read_own) + INSERT(insert_own)만 존재. UPDATE 없음. |
| **영향** | 배치 파이프라인이 `ON CONFLICT (user_id, metric_date) DO UPDATE`로 재계산 결과를 갱신할 수 없음. `service_role` 키로 RLS 우회를 전제한다면 그 가정이 문서화되어야 함. |
| **수정 방안** | `CREATE POLICY "metrics_update_own" ON computed_load_metrics FOR UPDATE USING (user_id = auth.uid());` 추가, 또는 배치 전용 역할 문서화 |

---

## 4. 수정 우선순위 권장

| 순위 | 버그 | 수정 난이도 | 사유 |
|:----:|:----:|:----------:|------|
| 1 | B-01 | 낮음 | 제약 1줄 교체. 미수정 시 INSERT 전면 실패. |
| 2 | B-04 | 낮음 | WHERE 절 1줄 수정. 미수정 시 ACWR 전체 왜곡. |
| 3 | B-02 | 중간 | 3개 테이블 user_id 제거 + RLS 재작성. 미수정 시 데이터 불일치 가능. |
| 4 | B-06 | 낮음 | CHECK 범위 1 수정. CR-10 스케일 정합성. |
| 5 | B-05 | 중간 | 8개 테이블 RLS 재작성. 팀 기능 전면 차단 중. |
| 6 | B-03 | 중간 | 플래그 3개 제거 또는 트리거 3개 추가. |
| 7 | B-16 | 낮음 | 컬럼명 1개 변경. 파이프라인 매핑 오류 방지. |
| 8 | B-11 | 낮음 | CHECK 1개 추가. 대형 배열 방어. |
| 9~19 | 나머지 | 낮~중 | 기술 부채. 다음 마이그레이션에서 일괄 처리 가능. |

---

## 5. 긍정적 평가

위 비판과 별개로, 현재 설계에서 잘 된 부분도 기록한다:

| 항목 | 평가 |
|------|------|
| GENERATED STORED 활용 | `hooper_index`, `rr_count` — 애플리케이션 산출 부담 제거, 일관성 보장 |
| ON DELETE CASCADE 일관 적용 | 부모 삭제 시 고아 행 방지. FK 체인 전체에 적용됨 |
| UNIQUE 제약으로 멱등성 | `UNIQUE(user_id, metric_date)` 등으로 중복 삽입 방지 |
| ETL 뷰 분리 | 서비스 스키마 ↔ R&D 스키마 변환을 뷰로 캡슐화. 양측 독립 진화 가능 |
| 시드 ON CONFLICT DO NOTHING | 멱등 시드 — 반복 실행 안전 |
| ENUM으로 상태 제한 | 자유 텍스트 대비 입력 오류 방지, 인덱스 효율 향상 |

---

*본 리포트는 DDL 정적 분석 기반이며, 실제 PostgreSQL 인스턴스에서의 실행 검증은 포함하지 않는다.*
