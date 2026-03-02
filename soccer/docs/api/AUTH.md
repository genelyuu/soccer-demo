# 인증 (Authentication) 문서

> 근거: `src/lib/auth.ts`, `src/app/api/auth/`

## 인증 방식

- **라이브러리**: NextAuth.js v4 (JWT 전략)
- **제공자**: Credentials (이메일/비밀번호)
- **백엔드**: Supabase Auth (비밀번호 해시/검증)
- 근거: `src/lib/auth.ts:1-2`, `package.json:38`

## 토큰 흐름

```
[클라이언트] ─── POST /api/auth/callback/credentials ──→ [NextAuth]
                  (email, password)                         │
                                                            ▼
                                                    Supabase Auth
                                                    signInWithPassword
                                                            │
                                                            ▼
                                                    JWT 토큰 발급
                                                    (httpOnly 쿠키)
                                                            │
                                                            ▼
[클라이언트] ◄── Set-Cookie: next-auth.session-token ──── [응답]
```

## 세션/JWT 구조

### JWT 토큰 (서버 사이드)
```typescript
{
  sub: "user-uuid",  // 사용자 ID
  // NextAuth 기본 필드 포함
}
```
근거: `src/lib/auth.ts:54-59`

### 세션 객체 (클라이언트/서버)
```typescript
{
  user: {
    id: string;      // token.sub에서 전달
    name?: string;
    email?: string;
    image?: string;
  }
}
```
근거: `src/lib/auth.ts:68-76`

## 헤더 포맷

NextAuth는 쿠키 기반으로 동작하므로 별도 Authorization 헤더 불필요.
- 쿠키 이름: `next-auth.session-token`
- httpOnly: true (XSS 방어)

## 만료 정책

- JWT 기본 만료: 30일 (NextAuth 기본값)
- [UNKNOWN] 커스텀 만료 시간 설정 여부 — MVP에서는 기본값 사용

## API 엔드포인트

### POST /api/auth/signup
- **설명**: 회원가입 (Supabase Auth + users 테이블)
- **권한**: 공개
- **요청 바디**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "홍길동"
  }
  ```
- **검증**: zod 스키마 (`email`: 이메일 형식, `password`: 최소 6자, `name`: 필수)
- **성공 응답** (201):
  ```json
  { "user": { "id": "uuid", "email": "...", "name": "..." } }
  ```
- **실패 응답** (400/409/500):
  ```json
  { "error": "에러 메시지" }
  ```
- 근거: `src/app/api/auth/signup/route.ts`

### POST /api/auth/callback/credentials
- **설명**: 로그인 (NextAuth 내장 엔드포인트)
- **권한**: 공개
- 근거: `src/app/api/auth/[...nextauth]/route.ts`

### GET /api/auth/me
- **설명**: 현재 사용자 프로필 조회
- **권한**: 인증 필수
- **성공 응답** (200):
  ```json
  { "user": { "id": "...", "email": "...", "name": "...", "avatar_url": null, "created_at": "..." } }
  ```
- **실패 응답** (401): `{ "error": "인증이 필요합니다" }`
- 근거: `src/app/api/auth/me/route.ts`

## 환경변수 (키 이름만)

| 키 | 용도 | 근거 |
|---|------|------|
| `NEXTAUTH_URL` | NextAuth 콜백 URL | `src/lib/auth.ts` |
| `NEXTAUTH_SECRET` | JWT 서명 | `src/lib/auth.ts:64` |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase 엔드포인트 | `src/lib/supabase/client.ts:4` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase 공개 키 | `src/lib/supabase/client.ts:5` |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase 서비스 키 (서버 전용) | `src/lib/supabase/server.ts:10` |

## 테스트

| 테스트 파일 | 테스트 수 | 설명 |
|------------|---------|------|
| `src/features/auth/__tests__/signup-validation.test.ts` | 4 | 회원가입 입력 검증 (성공/이메일/비밀번호/이름) |
| `src/features/auth/__tests__/auth-options.test.ts` | 3 | 인증 설정 구조, JWT/세션 콜백 |

## [UNKNOWN]
- OAuth 프로바이더 추가 계획 (카카오, Google 등)
- 비밀번호 재설정 플로우
- 토큰 갱신/리프레시 전략
- rate limiting 적용 여부

## 검증 체크리스트
- [ ] 이메일/비밀번호로 회원가입이 가능한가?
- [ ] 회원가입 후 로그인이 가능한가?
- [ ] 로그인 후 세션(JWT)이 유지되는가?
- [ ] /api/auth/me가 인증된 사용자 정보를 반환하는가?
- [ ] 잘못된 입력에 적절한 에러 메시지가 반환되는가?
