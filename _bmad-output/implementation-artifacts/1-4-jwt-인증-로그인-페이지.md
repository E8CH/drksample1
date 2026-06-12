# Story 1.4: JWT 인증 & 로그인 페이지

Status: done

## Story

As a 관리자,
I want admin 계정으로 로그인하고 싶다,
So that 보호된 대시보드 페이지에 접근할 수 있다.

## Acceptance Criteria

1. **Given** `/login` 페이지에서 admin 자격증명 입력 **When** "로그인" 버튼 클릭 **Then** JWT HttpOnly Cookie(`access_token`)가 발급되고 `/dashboard/simulation`으로 리다이렉트됨

2. **Given** 로그인하지 않은 상태 **When** `/dashboard/*` 경로 직접 접근 **Then** `middleware.ts`가 `/login`으로 리다이렉트함

3. **Given** 잘못된 비밀번호 입력 **When** 로그인 시도 **Then** "로그인 정보가 올바르지 않습니다" 오류 표시. FastAPI `HTTP 401` 응답.

4. **Given** JWT 토큰 만료 **When** 보호된 페이지 접근 **Then** `/login`으로 자동 리다이렉트됨

5. **Given** `POST /auth/logout` 요청 **When** 로그아웃 실행 **Then** JWT Cookie가 삭제되고 `/login`으로 리다이렉트됨

## Tasks / Subtasks

- [x] Task 1: 백엔드 Config 확장 (AC: #1, #3)
  - [x] `app/config.py`에 `ADMIN_USERNAME: str`, `ADMIN_PASSWORD: str` 필수 필드 추가
  - [x] `fastapi_backend/.env`에 `ADMIN_USERNAME=admin`, `ADMIN_PASSWORD=Admin1234!` 추가

- [x] Task 2: 커스텀 인증 라우터 생성 (AC: #1, #3, #5)
  - [x] `app/routes/auth.py` 생성 (`routes/` 디렉토리는 기존 `routes/items.py`와 동일한 위치)
  - [x] `POST /auth/login` 엔드포인트: `{username: str, password: str}` JSON 수신, `settings.ADMIN_USERNAME`/`settings.ADMIN_PASSWORD` 검증, PyJWT로 JWT 생성, `access_token` HttpOnly Cookie 설정
    - [x] 잘못된 자격증명 시 `HTTPException(status_code=401, detail="로그인 정보가 올바르지 않습니다")`
    - [x] JWT payload: `{"sub": username, "exp": datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)}`
    - [x] Cookie: `httponly=True, samesite="lax", secure=False, max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS`
  - [x] `POST /auth/logout` 엔드포인트: `response.delete_cookie("access_token")` 후 `{"message": "ok"}` 반환

- [x] Task 3: main.py에 커스텀 인증 라우터 등록 (AC: #1, #3, #5)
  - [x] `app/main.py`에 `from app.routes.auth import router as custom_auth_router` 추가
  - [x] `app.include_router(custom_auth_router)` 추가

- [x] Task 4: 백엔드 테스트 작성 (AC: #1, #3, #5)
  - [x] `tests/test_auth_router.py` 생성 — `AsyncClient` + `ASGITransport` 패턴 사용 (conftest.py 참고)
  - [x] `test_login_success()`: 올바른 자격증명 → 200, 응답 헤더에 `Set-Cookie: access_token=...` 확인
  - [x] `test_login_wrong_password()`: 잘못된 비밀번호 → 401, detail="로그인 정보가 올바르지 않습니다"
  - [x] `test_login_wrong_username()`: 잘못된 아이디 → 401
  - [x] `test_logout_deletes_cookie()`: `POST /auth/logout` → 200, 응답 헤더에 `access_token` 쿠키 삭제 확인

- [x] Task 5: 프론트엔드 환경변수 설정 (AC: #1, #4)
  - [x] `nextjs-frontend/.env.local` 생성
  - [x] `NEXT_PUBLIC_API_URL=http://localhost:8000` 추가
  - [x] `JWT_SECRET=<SECRET_KEY와 동일한 값>` 추가 (middleware.ts에서 JWT 검증용, edge runtime에서 사용 가능)

- [x] Task 6: `jose` 패키지 추가 (AC: #2, #4)
  - [x] `nextjs-frontend/package.json`에 `jose` 의존성 추가 (edge-compatible JWT 라이브러리)
  - [x] `pnpm add jose` 실행

- [x] Task 7: Next.js `middleware.ts` 생성 (AC: #2, #4)
  - [x] `nextjs-frontend/middleware.ts` 생성 (패키지 루트, `app/` 디렉토리와 동일 레벨)
  - [x] `config.matcher: ['/dashboard/:path*']` — `/dashboard` 하위 경로만 보호
  - [x] `access_token` 쿠키 존재 확인 → 없으면 `/login`으로 `NextResponse.redirect`
  - [x] 쿠키 있으면 `jose`의 `jwtVerify`로 서명/만료 검증 → 실패(`JWTExpired`, `JWSSignatureVerificationFailed` 등) 시 `/login` 리다이렉트
  - [x] 검증 성공 시 `NextResponse.next()` (통과)

- [x] Task 8: 로그인 서버 액션 재작성 (AC: #1, #3)
  - [x] `nextjs-frontend/components/actions/login-action.ts` 재작성
  - [x] 기존 `authJwtLogin` 호출 제거
  - [x] `fetch(NEXT_PUBLIC_API_URL/auth/login, ...)` 호출
  - [x] HTTP 401 → `{server_validation_error: "로그인 정보가 올바르지 않습니다"}` 반환
  - [x] 네트워크 오류 → `{server_error: "서버 오류가 발생했습니다. 다시 시도해주세요."}` 반환
  - [x] 성공 → `redirect('/dashboard/simulation')` (try/catch 외부에서 호출)
  - [x] `loginSchema`는 기존에 이미 `username: z.string().min(1)` — 수정 불필요

- [x] Task 9: 로그아웃 서버 액션 재작성 (AC: #5)
  - [x] `nextjs-frontend/components/actions/logout-action.ts` 재작성
  - [x] `fetch(NEXT_PUBLIC_API_URL/auth/logout, ...)` 호출
  - [x] 완료 후 `redirect('/login')`

- [x] Task 10: 로그인 페이지 UI 한국어화 (AC: #1, #3)
  - [x] `nextjs-frontend/app/login/page.tsx` 수정
  - [x] 제목: "다락 관리자 로그인"
  - [x] `username` input: label "아이디", type="text"
  - [x] `password` input: label "비밀번호"
  - [x] 버튼 텍스트: "로그인"
  - [x] "Forgot your password?", "Don't have an account? Sign up" 링크 제거
  - [x] 오류 메시지 인라인 빨간 텍스트로 표시

- [x] Task 11: `/dashboard/simulation` placeholder 페이지 생성 (AC: #1)
  - [x] `nextjs-frontend/app/dashboard/simulation/page.tsx` 생성

## Dev Notes

### 아키텍처 결정: 커스텀 auth 라우터 위치

기존 `app/routes/items.py` 패턴에 따라 `app/routes/auth.py`로 생성. `app/main.py`에서 `from app.routes.items import router as items_router` 패턴 동일하게 적용.

```python
# app/routes/auth.py
from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
from app.config import settings

router = APIRouter(prefix="/auth", tags=["custom-auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(request: LoginRequest, response: Response):
    if request.username != settings.ADMIN_USERNAME or request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="로그인 정보가 올바르지 않습니다")
    expire = datetime.now(timezone.utc) + timedelta(seconds=settings.ACCESS_TOKEN_EXPIRE_SECONDS)
    token = jwt.encode({"sub": request.username, "exp": expire}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=settings.ACCESS_TOKEN_EXPIRE_SECONDS, samesite="lax", secure=False)
    return {"message": "ok"}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "ok"}
```

### PyJWT 가용성

`fastapi-users`가 `PyJWT`를 의존성으로 포함. `import jwt` (PyJWT 패키지명은 PyJWT지만 import는 `jwt`)로 사용 가능. 추가 설치 불필요.

### middleware.ts 구현 (jose)

```typescript
// nextjs-frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { jwtVerify } from 'jose';

export async function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }
  try {
    const secret = new TextEncoder().encode(process.env.JWT_SECRET);
    await jwtVerify(token, secret);
    return NextResponse.next();
  } catch {
    return NextResponse.redirect(new URL('/login', request.url));
  }
}

export const config = {
  matcher: ['/dashboard/:path*'],
};
```

`JWT_SECRET` = 백엔드 `SECRET_KEY`와 동일한 값. 프론트엔드 `.env.local`에 설정.

### 로그인 서버 액션 패턴

Next.js Server Actions에서 `redirect()`는 `NEXT_REDIRECT` 오류를 throw하므로 **반드시 try/catch 외부**에서 호출해야 함. 내부에서 호출 시 catch에 잡혀 redirect가 동작하지 않음.

```typescript
export async function login(prevState: unknown, formData: FormData) {
  const validated = loginSchema.safeParse({...});
  if (!validated.success) return { errors: validated.error.flatten().fieldErrors };
  
  let success = false;
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(validated.data),
    });
    if (res.status === 401) return { server_validation_error: '로그인 정보가 올바르지 않습니다' };
    if (!res.ok) return { server_error: '서버 오류가 발생했습니다. 다시 시도해주세요.' };
    success = true;
  } catch {
    return { server_error: '서버에 연결할 수 없습니다.' };
  }
  if (success) redirect('/dashboard/simulation');
}
```

### loginSchema 수정 (`lib/definitions.ts`)

기존 스키마가 `username: z.string().email()` 검증. 어드민 로그인은 이메일이 아니라 일반 문자열이므로 `z.string().min(1, "아이디를 입력하세요")`로 변경.

### 백엔드 테스트 패턴

conftest.py의 `test_client` fixture는 DB 연결 필요. 커스텀 auth 라우터는 DB 미사용이므로 독립 fixture 사용:

```python
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000") as c:
        yield c
```

환경변수 `ADMIN_USERNAME`, `ADMIN_PASSWORD`는 `.env`에서 로드됨 (conftest.py import 시 Settings 초기화).

### 로그아웃 액션 패턴

HttpOnly Cookie는 JavaScript/서버 액션에서 직접 삭제 불가 → 백엔드 `/auth/logout` 호출로 백엔드가 `Set-Cookie: access_token=; Max-Age=0` 응답.

```typescript
export async function logout() {
  try {
    await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
  } catch { /* 오류 무시, 리다이렉트 우선 */ }
  redirect('/login');
}
```

### 기존 파일 수정 대상 목록

| 파일 | 변경 유형 |
|------|----------|
| `fastapi_backend/app/config.py` | 수정 — ADMIN_USERNAME, ADMIN_PASSWORD 필드 추가 |
| `fastapi_backend/app/main.py` | 수정 — custom_auth_router 등록 |
| `fastapi_backend/.env` | 수정 — ADMIN_USERNAME, ADMIN_PASSWORD 추가 |
| `nextjs-frontend/app/login/page.tsx` | 수정 — 한국어 UI, 불필요 링크 제거 |
| `nextjs-frontend/components/actions/login-action.ts` | 재작성 — 커스텀 /auth/login 호출 |
| `nextjs-frontend/components/actions/logout-action.ts` | 재작성 — 커스텀 /auth/logout 호출 |
| `nextjs-frontend/lib/definitions.ts` | 수정 — loginSchema username 검증 변경 |

| 파일 | 변경 유형 |
|------|----------|
| `fastapi_backend/app/routes/auth.py` | 신규 |
| `fastapi_backend/tests/test_auth_router.py` | 신규 |
| `nextjs-frontend/middleware.ts` | 신규 |
| `nextjs-frontend/app/dashboard/simulation/page.tsx` | 신규 (placeholder) |
| `nextjs-frontend/.env.local` | 신규 |

### Story 1-3 학습 사항 반영

- `.env` 없으면 모듈 import 단계에서 `ValidationError` → `ADMIN_USERNAME`, `ADMIN_PASSWORD` 반드시 `.env`에 즉시 추가
- try/finally 패턴: 테스트에서 환경변수 패치 후 복원 필수
- 백엔드 테스트는 `AsyncClient` + `ASGITransport` 패턴 사용

### Review Findings

- [x] [Review][Patch] F1: Cookie 브라우저 미전달(login) — Server Action `fetch` `credentials:"include"` 무효; `cookies().set()` 사용 필요 [login-action.ts:22-33]
- [x] [Review][Patch] F2: Logout cookie 삭제 브라우저 미전달 — 동일 원인; `cookies().delete()` 사용 필요 [logout-action.ts:7-14]
- [x] [Review][Patch] F3: JWT secret 변수명 불일치 (`JWT_SECRET` vs `SECRET_KEY`) — 프로덕션에서 검증 전체 실패 [middleware.ts:13, .env.local]
- [x] [Review][Patch] F4: `.env.example` 신규 필수 환경변수 누락 — ADMIN_USERNAME/PASSWORD, SECRET_KEY [.env.example x2]
- [x] [Review][Patch] F5: middleware matcher `/dashboard` root 미보호 — `/dashboard/:path*`가 `/dashboard` 자체 미매칭 [middleware.ts:22]
- [x] [Review][Patch] F6: `jwtVerify` algorithm 미지정 — `{ algorithms: ['HS256'] }` 옵션 추가 필요 [middleware.ts:14]
- [x] [Review][Patch] F8: `delete_cookie` attribute 불일치 — `httponly=True, samesite="lax"` 명시 필요 [auth.py:39]
- [x] [Review][Defer] F7: `secure=False` 하드코딩 [auth.py:33] — deferred, POC 단계; Railway 배포 시 True로 변경 예정
- [x] [Review][Defer] F9: dashboard layout.tsx `onClick={logout}` 패턴 — deferred, pre-existing (Story 1.5에서 레이아웃 재작성 시 개선)
- [x] [Review][Defer] F10: 테스트가 실제 credentials 사용 — deferred, .env placeholder 값 사용으로 CI 안전
- [x] [Review][Defer] F11: 로그인 rate limiting 없음 — deferred, POC 단계
- [x] [Review][Defer] F12: timing-safe 비교 미사용 — deferred, POC 단계
- [x] [Review][Defer] F13: NEXT_PUBLIC_API_URL 서버-only 변수에 불필요한 클라이언트 노출 — deferred, API_URL로 rename 패치에 포함

## Dev Agent Record

### Implementation Plan

1. 백엔드: `config.py`에 ADMIN_USERNAME/PASSWORD 추가 → `app/routes/auth.py` 커스텀 라우터 생성 → `main.py` 등록
2. 백엔드 테스트: `test_auth_router.py` 4개 테스트 (login success/wrong-password/wrong-username/logout)
3. 프론트엔드: jose 설치 → middleware.ts 생성 → login/logout 액션 재작성 → login 페이지 한국어화 → dashboard/simulation placeholder

### Debug Log

- PyJWT는 `import jwt`로 import (fastapi-users 의존성으로 이미 설치됨)
- `loginSchema`는 이미 `z.string().min(1)` 형태 — email 검증 없어 수정 불필요
- `pnpm` 없어 `npx pnpm add jose` 방식으로 설치 성공 (jose 6.2.3)
- TypeScript 타입 체크 오류 없음

### Completion Notes

- 백엔드: POST /auth/login, POST /auth/logout 구현 완료. 4개 테스트 100% 통과.
- 프론트엔드: middleware.ts로 /dashboard/* 보호, jose jwtVerify로 만료 검증. login/logout 서버 액션 재작성. 로그인 페이지 한국어 UI.
- 기존 테스트 리그레션 없음 (DB 의존 테스트들의 ERROR는 로컬 Postgres 미실행으로 인한 기존 문제).

## File List

**신규 생성:**
- `fastapi_backend/app/routes/auth.py`
- `fastapi_backend/tests/test_auth_router.py`
- `nextjs-frontend/middleware.ts`
- `nextjs-frontend/app/dashboard/simulation/page.tsx`
- `nextjs-frontend/.env.local`

**수정:**
- `fastapi_backend/app/config.py` — ADMIN_USERNAME, ADMIN_PASSWORD 필드 추가
- `fastapi_backend/app/main.py` — custom_auth_router 등록
- `fastapi_backend/.env` — ADMIN_USERNAME, ADMIN_PASSWORD 값 추가
- `nextjs-frontend/components/actions/login-action.ts` — 커스텀 /auth/login 호출로 재작성
- `nextjs-frontend/components/actions/logout-action.ts` — 커스텀 /auth/logout 호출로 재작성
- `nextjs-frontend/app/login/page.tsx` — 한국어 UI로 재작성
- `nextjs-frontend/package.json` — jose 6.2.3 의존성 추가

## Change Log

- 2026-06-12: Story 1-4 구현 완료. JWT HttpOnly Cookie 인증, middleware.ts 라우트 보호, 한국어 로그인 UI 구현.
- 2026-06-12: 코드 리뷰 패치 7건 적용 (F1~F6, F8). cookies() next/headers 패턴, SECRET_KEY 통일, middleware matcher 수정, HS256 algorithm 고정.
