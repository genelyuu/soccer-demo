# 환경변수 및 시크릿 관리

> 근거: `.env.local` (생성됨), `.env.example` (템플릿), `src/lib/supabase/client.ts:4-5`, `src/lib/auth.ts:32`

## 환경변수 키 목록

| 키 이름 | 용도 | 필수 | 공개 여부 | 근거 |
|---------|------|------|----------|------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 프로젝트 URL | 필수 | 공개 (NEXT_PUBLIC_) | `src/lib/supabase/client.ts:4` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 익명 키 (RLS 적용) | 필수 | 공개 (NEXT_PUBLIC_) | `src/lib/supabase/client.ts:5` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 역할 키 (서버 전용) | 필수 | 비공개 | `src/lib/supabase/server.ts:10` |
| `NEXTAUTH_URL` | NextAuth 콜백 URL | 필수 | 비공개 | `src/lib/auth.ts` |
| `NEXTAUTH_SECRET` | NextAuth JWT 서명 시크릿 | 필수 | 비공개 | `src/lib/auth.ts:32` |

## 환경변수 파일 구조

```
.env.example      # 키 이름만 포함 (버전 관리 O)
.env.local         # 실제 값 포함 (버전 관리 X, .gitignore에 포함)
```

> 근거: `.gitignore:34` — `.env*` 패턴으로 모든 env 파일 제외

## 보안 규칙

1. **시크릿 값은 절대 문서/로그/커밋에 기록하지 않는다** — 키 이름만 기록
2. `NEXT_PUBLIC_` 접두사가 있는 변수만 클라이언트에 노출됨
3. `SUPABASE_SERVICE_ROLE_KEY`는 RLS를 우회하므로 서버 사이드에서만 사용
4. `NEXTAUTH_SECRET`은 최소 32자 랜덤 문자열 권장

## 로컬 설정 방법

```bash
cp .env.example .env.local
# 에디터로 .env.local을 열어 실제 값을 입력
```

## [UNKNOWN] 항목

- 프로덕션 환경 시크릿 관리 방식 (Vercel env vars vs. 외부 시크릿 매니저)
- OAuth 프로바이더 추가 시 필요한 환경변수 (카카오, Google 등)

## 검증 체크리스트

- [ ] `.env.local` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] `NEXT_PUBLIC_` 접두사 없는 변수가 클라이언트 코드에서 참조되지 않는가?
- [ ] `.env.example`에 실제 시크릿 값이 포함되어 있지 않은가?
