---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - planning-artifacts/prds/prd-drksample1-2026-06-12/prd.md
  - planning-artifacts/ux-design-specification.md
  - planning-artifacts/research/technical-selfstorage-fullstack-tech-research-2026-06-12.md
  - docs/idea.md
workflowType: 'architecture'
project_name: 'drksample1'
user_name: 'HEMICOLON'
date: '2026-06-12'
lastStep: 8
status: 'complete'
completedAt: '2026-06-12'
---

# Architecture Decision Document
## 셀프스토리지 브랜드 입지분석 관리자 웹 서비스 (POC)

**완료일:** 2026-06-12 | **상태:** READY FOR IMPLEMENTATION

---

## 목차

1. [프로젝트 컨텍스트 분석](#1-프로젝트-컨텍스트-분석)
2. [스타터 템플릿](#2-스타터-템플릿)
3. [핵심 아키텍처 결정](#3-핵심-아키텍처-결정)
4. [구현 패턴 & 일관성 규칙](#4-구현-패턴--일관성-규칙)
5. [프로젝트 구조](#5-프로젝트-구조)
6. [아키텍처 검증](#6-아키텍처-검증)

---

## 1. 프로젝트 컨텍스트 분석

### 기능 요구사항 개요

| FR | 기능 | 아키텍처 난이도 |
|----|------|----------------|
| FR-1 | 입지 조건 입력 폼 (7 fields) | 낮음 |
| FR-2 | 수익 시뮬레이션 연산 (유사 지점 추출 알고리즘) | **높음** |
| FR-3 | 카카오맵 + 결과 화면 | **높음** |
| FR-4 | 제안서 팝업 (도표/차트) | 중간 |
| FR-5 | PDF 다운로드 | 중간 |
| FR-6~7 | 게시판 + 정렬/필터 (TanStack Table 서버사이드) | 중간 |
| FR-8 | 가상 데이터 생성/삭제 (~80만 건) | 중간 |

### NFR 아키텍처 제약

- 시뮬레이션 결과 **3초 이내** → DB 인덱싱 + asyncpg COPY 전략
- **API 키 서버사이드 처리** → FastAPI에서만 Kakao/공공데이터 호출
- **지도 프로바이더 추상화** → v2 네이버 부동산 교체 가능
- **Railway Hobby 배포** → 모노레포 3서비스

### 횡단 관심사

1. `MapProvider` 추상화 — Kakao(v1) ↔ Naver(v2) 교체
2. `SimulationEngine` 추상화 — 규칙 기반(v1) ↔ ML(v2+)
3. JWT 인증/세션 — 미들웨어로 전 페이지 보호
4. 서버사이드 API 키 보안
5. 가상 데이터 배치 생성 (asyncpg COPY)

---

## 2. 스타터 템플릿

**선택: Vinta `nextjs-fastapi-template`**

```bash
git clone https://github.com/vintasoftware/nextjs-fastapi-template.git drksample1
cd drksample1

# 백엔드
cd fastapi_backend && uv sync
cp .env.example .env
python3 -c "import secrets; print(secrets.token_hex(32))"  # SECRET_KEY 생성

# 프론트엔드
cd ../nextjs_frontend && pnpm install
cp .env.example .env.local
```

**포함 내용:** JWT 인증(fastapi-users), async SQLAlchemy 2.0, Alembic, pytest-asyncio, TypeScript + Zod, pnpm, UV

**Railway 추가 설정:** `railway.toml` 생성 — 각 서비스별 빌드/시작 커맨드 정의

---

## 3. 핵심 아키텍처 결정

### 3.1 데이터 아키텍처

**DB 스키마:**

```sql
-- 지점 (마스터)
CREATE TABLE branches (
    branch_name     TEXT PRIMARY KEY,
    address         TEXT NOT NULL,
    area_sqm        NUMERIC,
    monthly_rent    NUMERIC,
    maintenance_fee NUMERIC,
    building_usage  TEXT,
    ev_charging     BOOLEAN DEFAULT false,
    parking_count   INTEGER DEFAULT 0
);

-- 운영비 (월별)
CREATE TABLE operations (
    id              BIGSERIAL PRIMARY KEY,
    branch_name     TEXT REFERENCES branches(branch_name),
    month           DATE NOT NULL,  -- 월 첫째날로 정규화
    electricity_fee NUMERIC,
    operating_cost  NUMERIC
);

-- 회원
CREATE TABLE members (
    email   TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    phone   TEXT,
    address TEXT
);

-- 매출 (시계열 핵심 — Range Partitioning)
CREATE TABLE sales (
    id            BIGSERIAL,
    branch_name   TEXT REFERENCES branches(branch_name),
    member_email  TEXT REFERENCES members(email),
    sale_date     DATE NOT NULL,
    daily_revenue NUMERIC NOT NULL
) PARTITION BY RANGE (sale_date);

-- 연도별 파티션 (2016~2025)
CREATE TABLE sales_2016 PARTITION OF sales FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
-- ... 반복

-- 인덱스
CREATE INDEX idx_sales_branch_date ON sales (branch_name, sale_date);
CREATE INDEX idx_sales_date_brin ON sales USING BRIN (sale_date);
```

**ORM/마이그레이션:**
- SQLAlchemy 2.0 async (`create_async_engine`)
- 드라이버: `postgresql+asyncpg://` (**절대 `postgresql://` 사용 금지**)
- 마이그레이션: Alembic (`alembic upgrade head`)

### 3.2 인증 & 보안

- **라이브러리:** `fastapi-users`
- **방식:** JWT + HttpOnly Cookie
- **계정:** admin 단일 계정 (하드코딩, POC)
- **미들웨어:** `middleware.ts` — 미인증 요청 `/login` 리다이렉트
- **API 키:** `.env`에만 보관, FastAPI 서버에서만 사용

### 3.3 API & 통신

**엔드포인트 목록:**

```
POST /auth/login          ← 로그인
POST /auth/logout         ← 로그아웃

POST /simulation/run      ← 수익 시뮬레이션 실행
GET  /branches/nearby     ← 인근 지점 조회 (지도용)

GET  /sales               ← 게시판 목록 (페이지네이션, 정렬, 필터)
POST /data/generate       ← 가상 데이터 생성 (BackgroundTask → 202)
DELETE /data/all          ← 전체 데이터 삭제
```

**Next.js → FastAPI 통신:**
- 읽기: Server Component에서 직접 `fetch()`
- 쓰기: Server Actions → FastAPI POST/DELETE

### 3.4 시뮬레이션 엔진 (핵심 설계)

```python
# app/engines/base.py
class SimulationEngine(ABC):
    @abstractmethod
    async def predict(self, location: LocationConditions) -> SimulationResult: ...

# app/engines/rule_based.py — v1 완전 구현
class RuleBasedEngine(SimulationEngine):
    # config.py에서 로드 — 쉽게 조정 가능
    WEIGHTS = {"area": 0.45, "rent": 0.30, "region": 0.25}
    EV_BONUS = 1.08
    PARKING_BONUS_PER_SLOT = 0.02  # 최대 +10%

    async def predict(self, location) -> SimulationResult:
        # 1차: 면적±30%, 임대료±30%, 같은 구 → 유사 지점 추출
        # 2차: ±50%, 같은 시 (fallback)
        # 3차: 전체 평균 + amber 경고 배너 (최종 fallback)
        ...

# app/engines/ml_engine.py — stub, 나중 구현
class MLEngine(SimulationEngine):
    async def predict(self, location) -> SimulationResult:
        # TODO: 실제 ML 모델 추론으로 교체
        # 현재는 RuleBasedEngine으로 위임
        return await RuleBasedEngine().predict(location)

# app/config.py
SIMULATION_ENGINE = "rule_based"  # "rule_based" | "ml" — 관리자 선택 가능

# app/services/simulation_service.py
def get_engine() -> SimulationEngine:
    if settings.SIMULATION_ENGINE == "ml":
        return MLEngine()
    return RuleBasedEngine()
```

**ML 진화 경로:**
- v1 데이터(`branches`, `sales`, `operations`) = v2 ML 훈련 데이터
- `scripts/train_model.py`: scikit-learn RandomForestRegressor (나중 구현)
- 학습 피처: area, rent, region_code, ev, parking, building_usage
- 학습 타겟: monthly_revenue, occupancy_rate

### 3.5 지도 프로바이더 추상화

```python
# app/providers/base.py
class MapProvider(ABC):
    @abstractmethod
    async def geocode(self, address: str) -> Coordinates: ...

    @abstractmethod
    async def get_nearby_branches(self, coords: Coordinates, radius_km: float) -> list[BranchPin]: ...

# app/providers/kakao.py — v1
class KakaoMapProvider(MapProvider):
    BASE_URL = "https://dapi.kakao.com/v2/local"

    async def geocode(self, address: str) -> Coordinates:
        # GET /geo/address.json?query={address}
        # Authorization: KakaoAK {KAKAO_REST_API_KEY}
        ...
```

### 3.6 PDF 생성

- **방식:** `html2canvas` + `jsPDF` (클라이언트 사이드)
- **주의:** `proposal-document.tsx`는 Recharts 대신 **순수 CSS/SVG 차트** 사용
  → html2canvas가 SVG를 정확히 캡처하지 못하는 이슈 방지
- **파일명:** `수익분석제안서_{주소}_{날짜}.pdf`

### 3.7 가상 데이터 배치 생성

```python
# app/services/data_generator.py
async def generate_all_data(db: AsyncSession):
    branches = await get_all_branches(db)
    for branch in branches:          # 220개 지점 순차 처리
        records = _build_sales_records(branch, years=10)  # ~3,650건
        async with db.get_bind().connect() as conn:
            await conn.copy_records_to_table(
                'sales',
                records=records,
                columns=['branch_name', 'member_email', 'sale_date', 'daily_revenue']
            )

# router: 즉시 202 반환, 백그라운드 처리
@router.post("/data/generate", status_code=202)
async def generate(background_tasks: BackgroundTasks, db=Depends(get_db)):
    background_tasks.add_task(generate_all_data, db)
    return {"status": "generating"}
```

- **예상 속도:** asyncpg COPY ~80,000 rows/s → **10~20초** (Railway Hobby)
- **메모리:** 지점별 청크 → 한 번에 ~3,650건만 메모리에 상주

---

## 4. 구현 패턴 & 일관성 규칙

### 네이밍 규칙

| 대상 | 규칙 | 예시 |
|------|------|------|
| DB 테이블 | `snake_case` 복수형 | `branches`, `sales` |
| DB 컬럼 | `snake_case` | `branch_name`, `sale_date` |
| DB 인덱스 | `idx_{table}_{column}` | `idx_sales_branch_date` |
| API 엔드포인트 | `/snake_case` 복수형 | `/branches`, `/sales` |
| Python 함수/변수 | `snake_case` | `get_similar_branches()` |
| TypeScript 함수/변수 | `camelCase` | `getSimilarBranches()` |
| React 컴포넌트 | `PascalCase` | `SimulationResultCard` |
| 파일명 (Next.js) | `kebab-case` | `simulation-form.tsx` |
| 환경 변수 | `UPPER_SNAKE_CASE` | `KAKAO_REST_API_KEY` |

### API 응답 포맷 (전체 일관)

```python
# 성공 단건
{"data": {...}, "message": "ok"}

# 성공 목록
{"data": [...], "total": 100, "page": 1, "limit": 50}

# 에러
{"detail": "유사 지점을 찾을 수 없습니다", "code": "NO_SIMILAR_BRANCHES"}

# HTTP 코드
200 GET 성공 | 201 POST 생성 | 202 비동기 시작 | 422 검증 실패 | 500 서버 오류
```

### 날짜/시간 포맷

| 위치 | 포맷 | 예시 |
|------|------|------|
| DB | `DATE` | `2025-12-01` |
| API JSON | ISO 8601 | `"2025-12-01"` |
| UI 표시 | 한국어 | `2025년 12월` |
| 파일명 | `YYYY-MM-DD` | `제안서_2026-06-12.pdf` |

### AI 에이전트 필수 준수 사항

```
✅ DB: postgresql+asyncpg:// 드라이버 필수 (postgresql:// 절대 금지)
✅ DB 컬럼: snake_case만 사용 (camelCase 금지)
✅ API 응답: {"data": ...} 래퍼 필수
✅ API 키: FastAPI .env에만 보관, 프론트엔드 코드에 절대 포함 금지
✅ 날짜: API는 ISO 8601, UI는 한국어 포맷
✅ Server Action: throw 금지, {success, error} 반환
✅ 비동기 작업: BackgroundTasks 사용, 즉시 202 반환
✅ shadcn/ui 컴포넌트: src/components/ui/ 수정 금지 (자동 생성)
```

### 에러 처리 패턴

```python
# FastAPI — 커스텀 예외
class SimulationError(Exception):
    def __init__(self, message: str, code: str):
        self.code = code
        super().__init__(message)

@app.exception_handler(SimulationError)
async def handler(request, exc):
    return JSONResponse(status_code=400,
                        content={"detail": str(exc), "code": exc.code})
```

```typescript
// Server Action — throw 금지
export async function runSimulation(formData: FormData) {
  try {
    const result = await fetchSimulation(formData)
    return { success: true, data: result }
  } catch (e) {
    return { success: false, error: e.message }
  }
}
```

---

## 5. 프로젝트 구조

```
drksample1/                              ← 모노레포 루트
├── .github/workflows/ci.yml             ← pytest → Railway 자동 배포
├── railway.toml                         ← 서비스별 빌드/시작 설정
├── .gitignore
│
├── fastapi_backend/
│   ├── pyproject.toml                   ← UV 의존성
│   ├── .env / .env.example
│   ├── alembic.ini
│   ├── alembic/versions/                ← 마이그레이션 이력
│   │
│   ├── app/
│   │   ├── main.py                      ← FastAPI 진입점, CORS
│   │   ├── config.py                    ← SIMULATION_ENGINE, WEIGHTS, API 키
│   │   ├── database.py                  ← create_async_engine (asyncpg)
│   │   │
│   │   ├── models/                      ← SQLAlchemy ORM
│   │   │   ├── branch.py
│   │   │   ├── operations.py
│   │   │   ├── member.py
│   │   │   └── sales.py                 ← 파티셔닝 설정
│   │   │
│   │   ├── schemas/                     ← Pydantic
│   │   │   ├── simulation.py            ← LocationConditions, SimulationResult
│   │   │   ├── branch.py
│   │   │   └── sales.py
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py                  ← POST /auth/login, logout
│   │   │   ├── simulation.py            ← POST /simulation/run
│   │   │   └── data.py                  ← POST /data/generate, DELETE /data/all
│   │   │
│   │   ├── engines/                     ← 시뮬레이션 엔진
│   │   │   ├── base.py                  ← SimulationEngine (ABC)
│   │   │   ├── rule_based.py            ← RuleBasedEngine (완전 구현)
│   │   │   └── ml_engine.py             ← MLEngine (stub)
│   │   │
│   │   ├── providers/                   ← 지도 프로바이더
│   │   │   ├── base.py                  ← MapProvider (ABC)
│   │   │   └── kakao.py                 ← KakaoMapProvider
│   │   │
│   │   └── services/
│   │       ├── simulation_service.py    ← 엔진 팩토리 + 결과 조합
│   │       ├── data_generator.py        ← asyncpg COPY 배치 생성
│   │       └── map_service.py           ← 지오코딩, 인근 지점 조회
│   │
│   ├── scripts/
│   │   └── train_model.py               ← ML 학습 스크립트 (나중 구현)
│   │
│   └── tests/
│       ├── conftest.py                  ← AsyncSession, NullPool fixture
│       ├── test_simulation.py
│       ├── test_data_generator.py
│       └── test_routers/
│
└── nextjs_frontend/
    ├── package.json (pnpm)
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── .env.local / .env.example
    ├── public/logo.svg                  ← 다락 브랜드 로고
    │
    └── src/
        ├── middleware.ts                ← JWT 검증, 미인증 → /login
        │
        ├── app/
        │   ├── layout.tsx               ← Pretendard 폰트, 전역
        │   ├── login/page.tsx
        │   └── dashboard/
        │       ├── layout.tsx           ← 네비게이션 바
        │       ├── simulation/page.tsx  ← Page 1 (FR-1~5)
        │       └── board/page.tsx       ← Page 2 (FR-6~8)
        │
        ├── components/
        │   ├── ui/                      ← shadcn/ui (수정 금지)
        │   ├── simulation/
        │   │   ├── simulation-form.tsx       ← FR-1
        │   │   ├── kakao-map-view.tsx        ← FR-3
        │   │   ├── simulation-result-card.tsx ← FR-3
        │   │   ├── verdict-badge.tsx          ← FR-3
        │   │   └── comparison-bar-chart.tsx   ← FR-4 (Recharts)
        │   ├── proposal/
        │   │   ├── proposal-modal.tsx         ← FR-4
        │   │   └── proposal-document.tsx      ← FR-5 (순수 CSS/SVG, PDF용)
        │   └── board/
        │       ├── branch-data-table.tsx      ← FR-6 (TanStack Table)
        │       └── table-toolbar.tsx          ← FR-7/8
        │
        ├── actions/
        │   ├── simulation.ts            ← runSimulation() Server Action
        │   └── data.ts                  ← generateData(), deleteAllData()
        │
        ├── lib/
        │   ├── api-client.ts            ← FastAPI fetch wrapper
        │   ├── pdf-generator.ts         ← html2canvas + jsPDF
        │   └── utils.ts                 ← 날짜/숫자 포맷
        │
        └── types/index.ts               ← 공유 TypeScript 타입
```

---

## 6. 아키텍처 검증

### 요구사항 커버리지

| FR | 구현 위치 | 상태 |
|----|-----------|------|
| FR-1 | `simulation-form.tsx` + `POST /simulation/run` | ✅ |
| FR-2 | `RuleBasedEngine` + `MLEngine(stub)` | ✅ |
| FR-3 | `kakao-map-view.tsx` + `KakaoMapProvider` | ✅ |
| FR-4 | `proposal-modal.tsx` + `comparison-bar-chart.tsx` | ✅ |
| FR-5 | `proposal-document.tsx` + `pdf-generator.ts` | ✅ |
| FR-6 | `branch-data-table.tsx` + `GET /sales` | ✅ |
| FR-7 | `table-toolbar.tsx` + URL 쿼리 파라미터 | ✅ |
| FR-8 | `data_generator.py` + asyncpg COPY | ✅ |

### 주의 사항 (Minor Gaps)

1. **html2canvas + Recharts:** `proposal-document.tsx`는 Recharts 대신 순수 CSS/SVG 차트 사용
2. **카카오맵 API 한도:** 초과 시 텍스트 주소만 표시하는 fallback 구현 필요

### 아키텍처 완성도

**전체 상태: READY FOR IMPLEMENTATION** ✅
**신뢰도: 높음** — 16개 체크리스트 전부 충족, Critical Gap 없음

---

## 구현 시작 명령

```bash
# 1단계: 템플릿 클론
git clone https://github.com/vintasoftware/nextjs-fastapi-template.git drksample1

# 2단계: 백엔드 설정
cd drksample1/fastapi_backend
uv sync && cp .env.example .env

# 3단계: 프론트엔드 설정
cd ../nextjs_frontend
pnpm install && cp .env.example .env.local

# 4단계: DB 마이그레이션 (개발)
cd ../fastapi_backend
alembic upgrade head

# 5단계: 개발 서버
make start-backend   # FastAPI :8000
make start-frontend  # Next.js :3000
```

**다음 단계:** `bmad-create-epics-and-stories` — 에픽 및 스토리 작성
