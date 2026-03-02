# 토큰 흐름 문서 (Task 0011)

> 근거: `src/lib/auth.ts`, `docs/api/AUTH.md`

## 인증 흐름

### 1. 회원가입
```
Client → POST /api/auth/signup → Supabase Auth (createUser) → users 테이블 INSERT
```

### 2. 로그인
```
Client → POST /api/auth/callback/credentials
  → NextAuth authorize()
    → Supabase Auth signInWithPassword()
    → users 테이블에서 프로필 조회
  → JWT 발급 (httpOnly 쿠키)
  ← Set-Cookie: next-auth.session-token
```

### 3. 인증된 요청
```
Client (쿠키 자동 전송) → API Route
  → getServerSession(authOptions)
    → JWT 검증 + session 객체 반환
  → session.user.id로 권한 확인
```

### 4. 세션 만료
```
JWT 만료 (30일 기본) → 401 응답 → 로그인 페이지로 리다이렉트
```

## JWT 구조

```
Header: { alg: "HS256" }
Payload: {
  sub: "user-uuid",    // 사용자 ID
  name: "...",
  email: "...",
  iat: 1234567890,     // 발급 시간
  exp: 1237159890      // 만료 시간 (30일 후)
}
Signature: HMAC-SHA256(header.payload, NEXTAUTH_SECRET)
```

근거: `src/lib/auth.ts:60-64`

## [UNKNOWN]
- 토큰 갱신 전략 (sliding session vs. fixed expiry)
- 다중 디바이스 로그인 제한 여부
- 로그아웃 시 서버 사이드 세션 무효화 방법

## 검증 체크리스트
- [ ] JWT가 httpOnly 쿠키로 전달되는가?
- [ ] 만료된 토큰으로 API 호출 시 401이 반환되는가?
- [ ] NEXTAUTH_SECRET이 코드에 하드코딩되어 있지 않은가?
