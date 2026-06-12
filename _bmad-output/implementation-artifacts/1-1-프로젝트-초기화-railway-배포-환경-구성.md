# Story 1.1: 프로젝트 초기화 & Railway 배포 환경 구성

Status: done

## Story

As a 개발자,
I want Vinta nextjs-fastapi-template 기반으로 프로젝트를 초기화하고 Railway에 자동 배포되는 환경을 구성하고 싶다,
so that 팀 전체가 동일한 개발 환경에서 시작하고 코드 푸시 시 Railway에 자동 배포할 수 있다.

## Acceptance Criteria

1. `git clone`, `uv sync`, `pnpm install` 완료 후 `make start-backend`(:8000), `make start-frontend`(:3000) 정상 기동됨
2. main 브랜치 push → GitHub Actions CI(pytest) 통과 → Railway 자동 배포됨
3. `railway.toml`에 fastapi-backend, nextjs-frontend 두 서비스 정의. Railway에서 3개 서비스(FastAPI, Next.js, PostgreSQL)가 독립 빌드됨
4. `.env.example` 파일 존재. `python3 -c "import secrets; print(secrets.token_hex(32))"` 명령으로 SECRET_KEY 생성 가능.

## Tasks / Subtasks

- [x] Task 1: Vinta 템플릿 클론 및 초기 설정 (AC: #1)
  - [x] `git clone https://github.com/vintasoftware/nextjs-fastapi-template.git _template_tmp`
  - [x] `fastapi_backend/`, `nextjs-frontend/`, `Makefile`, `docker-compose.yml` 프로젝트 루트로 이동
  - [x] `fastapi_backend/.env.example` → `.env` 복사 안내 문서화
  - [x] `nextjs-frontend/.env.example` → `.env.local` 복사 안내 문서화

- [x] Task 2: Railway 배포 설정 (AC: #2, #3)
  - [x] `railway.toml` 파일 생성 (루트 디렉토리)
  - [x] fastapi-backend 서비스 정의 (build, start, pre_deploy, variables)
  - [x] nextjs-frontend 서비스 정의 (build, start, variables)
  - [x] Watch Paths 설정 (각 서비스 독립 빌드)

- [x] Task 3: GitHub Actions CI/CD 설정 (AC: #2)
  - [x] `.github/workflows/ci.yml` 생성
  - [x] test-backend job: PostgreSQL 서비스 컨테이너 + pytest 실행
  - [x] test-frontend job: pnpm + TypeScript 타입 체크

- [x] Task 4: 환경 변수 문서화 (AC: #4)
  - [x] `fastapi_backend/.env.example` 업데이트: SECRET_KEY, KAKAO_REST_API_KEY, SIMULATION_ENGINE 추가
  - [x] `nextjs-frontend/.env.example` 업데이트: FASTAPI_URL, NEXT_PUBLIC_APP_URL 추가

- [x] Task 5: 헬스체크 엔드포인트 & 테스트 (AC: #2)
  - [x] `app/main.py`에 `GET /health` 엔드포인트 추가 → `{"status": "ok"}`
  - [x] `tests/test_health.py` 생성: `GET /health` → 200 OK 검증

## Dev Notes

### 스타터 템플릿 정보
- **Repository**: `https://github.com/vintasoftware/nextjs-fastapi-template`
- **포함 내용**: fastapi-users(JWT), SQLAlchemy 2.0 async, Alembic, pytest-asyncio, TypeScript+Zod, pnpm, UV
- **디렉토리 구조**: 루트에 `fastapi_backend/`, `nextjs_frontend/` 두 폴더

### railway.toml 기본 구조

```toml
[build]
builder = "nixpacks"

[[services]]
name = "fastapi-backend"
source = "fastapi_backend"
build_command = "pip install uv && uv sync"
start_command = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

  [services.deploy]
  pre_deploy_command = "alembic upgrade head"

  [[services.variables]]
  name = "DATABASE_URL"
  value = "${{PostgreSQL.DATABASE_URL}}"

[[services]]
name = "nextjs-frontend"
source = "nextjs_frontend"
build_command = "npm install -g pnpm && pnpm install && pnpm build"
start_command = "pnpm start"

  [[services.variables]]
  name = "FASTAPI_URL"
  value = "http://fastapi-backend.railway.internal:8000"
```

### GitHub Actions CI 기본 구조

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        run: pip install uv
      - name: Install dependencies
        run: cd fastapi_backend && uv sync
      - name: Run tests
        run: cd fastapi_backend && pytest tests/
```

### 중요 주의사항
- **DB 드라이버**: `DATABASE_URL`은 반드시 `postgresql+asyncpg://` 형식 사용. `postgresql://` 사용 시 이벤트 루프 블로킹 발생.
- **Railway Hobby 플랜**: Free Plan 사용 금지 ($1 크레딧으로 DB 포함 시 수일 내 소진). Hobby $5/월 필수.
- **SECRET_KEY 생성**: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### Project Structure Notes

```
drksample1/                          ← 모노레포 루트
├── .github/workflows/ci.yml         ← 이 스토리에서 생성
├── railway.toml                     ← 이 스토리에서 생성
├── .gitignore
├── fastapi_backend/                 ← Vinta 템플릿 기본 제공
│   ├── pyproject.toml
│   ├── .env / .env.example          ← .env.example 업데이트
│   ├── app/main.py                  ← 변경 없음
│   └── tests/
│       ├── conftest.py
│       └── test_health.py           ← 이 스토리에서 생성
└── nextjs_frontend/                 ← Vinta 템플릿 기본 제공
    ├── package.json
    └── .env.example                 ← 업데이트
```

### References
- [Source: architecture.md#스타터-템플릿] Vinta nextjs-fastapi-template 초기화 커맨드
- [Source: architecture.md#인프라-&-배포] Railway 모노레포 배포 설정
- [Source: architecture.md#구현-패턴] postgresql+asyncpg:// 드라이버 필수

### Review Findings

- [x] [Review][Patch] pnpm 버전 불일치 수정: CI pnpm@9 → @10.7.1 [`.github/workflows/ci.yml:54`] — 적용 완료
- [x] [Review][Patch] railway.toml nextjs-frontend pnpm 버전 고정: `npm install -g pnpm@10.7.1` [`railway.toml:39`] — 적용 완료
- [x] [Review][Defer] `.env.example` 타이포 "genrated" [`fastapi_backend/.env.example:13`] — deferred, pre-existing (Vinta 템플릿 기존 이슈)

## Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Debug Log References

### Completion Notes List
- Vinta nextjs-fastapi-template 클론 완료 (fastapi_backend/, nextjs-frontend/ 프로젝트 루트에 배치)
- railway.toml: fastapi-backend + nextjs-frontend 서비스 정의, Watch Paths, pre_deploy=alembic upgrade head
- .github/workflows/ci.yml: test-backend (PostgreSQL 서비스 컨테이너 + pytest) + test-frontend (pnpm + tsc)
- GET /health 엔드포인트 추가 (app/main.py), 대응 테스트 (tests/test_health.py) 생성
- .env.example 파일 양쪽 모두 drksample1 전용 환경 변수 추가 문서화
- 주의: `uv sync`, `pnpm install`, Railway 대시보드 "Wait for CI" 설정은 수동 진행 필요

### File List
- NEW: `.github/workflows/ci.yml`
- NEW: `railway.toml`
- NEW: `fastapi_backend/tests/test_health.py`
- NEW: `fastapi_backend/` (Vinta 템플릿)
- NEW: `nextjs-frontend/` (Vinta 템플릿)
- NEW: `Makefile`
- NEW: `docker-compose.yml`
- UPDATE: `fastapi_backend/app/main.py` (GET /health 추가)
- UPDATE: `fastapi_backend/.env.example`
- UPDATE: `nextjs-frontend/.env.example`
