---
stepsCompleted: [1, 2, 3, 4, 5, 6]
inputDocuments: []
workflowType: 'research'
lastStep: 1
research_type: 'technical'
research_topic: '셀프스토리지 브랜드 입지분석 서비스 풀스택 기술 리서치 (Next.js + FastAPI + Railway + PostgreSQL)'
research_goals: 'POC 이전 단계 최소 기능 구현을 위한 전체 기술 스택 검증 — Next.js+FastAPI 통합 패턴, Railway 풀스택 배포 전략, 지도/상권 외부 API 연동 설계, PostgreSQL 10년 시계열 데이터 처리'
user_name: 'HEMICOLON'
date: '2026-06-12'
web_research_enabled: true
source_verification: true
---

# Research Report: technical

**Date:** 2026-06-12
**Author:** HEMICOLON
**Research Type:** technical

---

## Research Overview

국내 셀프스토리지(미니창고) 브랜드는 2025~2026년 기준 급성장 중이며, 220개 지점을 운영하는 주요 브랜드는 입지 선정의 의사결정 고도화를 핵심 과제로 인식하고 있다. 본 리서치는 이 문제를 해결하기 위한 관리자 웹 서비스 POC 구현에 필요한 전체 기술 스택을 웹 검색 기반 다중 소스 검증을 통해 종합적으로 분석한다.

리서치 대상 스택은 **Next.js 15 (프론트엔드) + FastAPI (백엔드) + PostgreSQL (DB) + Railway (배포)** 이며, 카카오맵 API 및 소상공인시장진흥공단 공공데이터 API 연동을 포함한다. 분석 범위는 기술 스택 적합성 검증, 통합 패턴, 아키텍처 설계, 구현 전략, 비용 및 위험 관리까지 아우른다.

핵심 발견: 이 기술 스택 조합은 2025~2026 기준 프로덕션에서 검증된 공식 템플릿이 존재하며, POC 수준의 구현은 약 2.5~3주 내에 가능하다. Railway Hobby 플랜($5/월)이 현실적인 최소 배포 환경이며, 상권 데이터는 무료 공공 API로 즉시 활용 가능하다. 상세 내용은 아래 각 섹션의 Executive Summary를 참고하라.

---

---

## Executive Summary

셀프스토리지 브랜드 입지분석 관리자 웹 서비스 POC를 위한 기술 스택 종합 검증 결과, **Next.js 15 + FastAPI + PostgreSQL + Railway** 조합은 2025~2026 기준 프로덕션 검증된 최적의 선택임이 확인되었다. Vinta Software의 공개 템플릿([github.com/vintasoftware/nextjs-fastapi-template](https://github.com/vintasoftware/nextjs-fastapi-template))이 이 스택을 완전히 구현하고 있으며, Railway도 이 풀스택에 대한 공식 One-Click 배포 템플릿을 제공한다.

**핵심 기술 발견:**

- **Next.js ↔ FastAPI 통합**: Server Components(읽기) + Server Actions(쓰기) 패턴으로 FastAPI를 내부 서비스로 완전 은닉 가능. OpenAPI → TypeScript 클라이언트 자동 생성으로 API 계약 안전성 확보
- **PostgreSQL 10년 시계열**: `sale_date` 기준 Range Partitioning + BRIN 인덱스가 검증된 표준. 220지점 × 10년 ≈ 80만 건은 파티셔닝 없이도 관리 가능하지만, 초기 설계에 포함 권장
- **Railway 배포**: Hobby 플랜($5/월) 필수. Free Plan은 DB 포함 시 수일 내 소진. 모노레포로 3개 서비스(Next.js/FastAPI/PostgreSQL) 단일 프로젝트 운영 가능
- **상권 데이터**: 소상공인시장진흥공단 공공 API(무료, data.go.kr)로 행정동 단위 매출/유동인구 즉시 활용 가능. 카카오맵 REST API가 한국 지도 표준
- **샘플 → 실제 API 교체 구조**: FastAPI 라우터 내부만 교체하는 패턴으로 idea.md의 요구사항("나중에 외부 API로 교체") 구현 가능

**기술 권장사항 Top 5:**

1. Vinta nextjs-fastapi-template 클론으로 시작 (인증/async DB/테스트 기반 포함)
2. `postgresql+asyncpg://` 드라이버 사용 필수 (일반 `postgresql://` 사용 시 이벤트 루프 블로킹)
3. Railway Hobby $5/월 플랜으로 시작, Free Plan 사용 금지
4. 관리자 대시보드는 TanStack Table v8 + shadcn/ui DataTable 표준 패턴 적용
5. 공공데이터 API 키 사전 신청 (data.go.kr, 1~2시간 소요)

---

## 목차 (Table of Contents)

1. [기술 리서치 범위 확인](#기술-리서치-범위-확인)
2. [Technology Stack Analysis](#technology-stack-analysis)
   - 프론트엔드: Next.js + TypeScript
   - 백엔드: FastAPI + Python
   - 데이터베이스: PostgreSQL 10년 시계열 처리
   - 배포 플랫폼: Railway 비용 구조
   - 외부 API: 카카오맵 + 공공데이터
3. [Integration Patterns Analysis](#integration-patterns-analysis)
   - Next.js ↔ FastAPI 통신 패턴
   - FastAPI ↔ PostgreSQL 비동기 연동
   - 공공데이터 API 연동 (샘플→실제 교체 구조)
   - 인증 패턴 (JWT + HttpOnly Cookie)
4. [Architectural Patterns and Design](#architectural-patterns-and-design)
   - 모노레포 아키텍처 (Railway)
   - 관리자 대시보드 아키텍처 (TanStack Table)
   - PostgreSQL 스키마 설계 (파티셔닝 포함)
   - Railway 내부 네트워크 배포 구조
5. [Implementation Approaches](#implementation-approaches-and-technology-adoption)
   - POC 구현 로드맵 (3단계, 2.5~3주)
   - CI/CD 파이프라인 (Railway + GitHub Actions)
   - 테스트 전략 (pytest-asyncio)
   - 위험 요소 및 완화 전략

---

## 기술 리서치 범위 확인

**리서치 주제:** 셀프스토리지 브랜드 입지분석 서비스 풀스택 기술 검증 (Next.js + FastAPI + Railway + PostgreSQL)
**리서치 목표:** POC 이전 단계 최소 기능 구현을 위한 전체 기술 스택 의사결정 근거 확보

**기술 리서치 범위:**

- Architecture Analysis — Next.js + FastAPI 통합 패턴, 설계 방식
- Implementation Approaches — 개발 방법론, 코딩 패턴
- Technology Stack — 언어, 프레임워크, 도구, 플랫폼
- Integration Patterns — 외부 API(지도/상권), 통신 프로토콜
- Performance Considerations — PostgreSQL 10년 시계열 데이터 처리

**리서치 방법론:**

- 현재 웹 데이터 기반 다중 소스 검증
- 불확실한 기술 정보에 대한 신뢰도 수준 명시
- 아키텍처 특화 인사이트 포함

**범위 확인일:** 2026-06-12

---

## Technology Stack Analysis

### 프로그래밍 언어 및 프레임워크

**프론트엔드: Next.js (TypeScript)**

Next.js 15 + FastAPI 조합은 2025~2026 기준 실제 프로덕션에서 검증된 풀스택 아키텍처로 자리잡았다.
Vinta Software의 오픈소스 템플릿([nextjs-fastapi-template](https://github.com/vintasoftware/nextjs-fastapi-template))과 Vercel 공식 템플릿([Full stack FastAPI template](https://vercel.com/templates/other/full-stack-fastapi-template-with-next-js))이 이를 뒷받침한다.

- TypeScript + Zod (프론트) ↔ Python + Pydantic (백엔드): 양단 타입 안전성 확보
- FastAPI의 OpenAPI 스키마에서 타입드 클라이언트를 자동 생성 가능 → API 계약 자동화
- SSR/SSG/Server Components 지원으로 관리자 대시보드 구현에 적합
- ShadcnUI + TailwindCSS v4 조합이 현재 표준으로 수렴 중

_신뢰도: 높음 — 공식 문서 및 다수의 실사용 템플릿으로 검증됨_
_출처: [Vinta Blog](https://www.vintasoftware.com/blog/next-js-fastapi-template), [DEV Community](https://dev.to/alexmayhewdev/fastapi-nextjs-15-the-full-stack-nobodys-building-1hl9)_

**백엔드: FastAPI (Python)**

- 비동기(async) 지원으로 DB 쿼리, 외부 API 호출 등 I/O 바운드 작업에 최적
- Pydantic v2 기반 자동 요청 검증 및 OpenAPI 문서 자동생성
- 의존성 주입(Dependency Injection)으로 인증, DB 세션, 서비스 레이어 패턴 구현 용이
- 프론트엔드(Next.js)와 완전한 관심사 분리 — 독립적 교체 가능

_신뢰도: 높음_
_출처: [Vercel Template](https://vercel.com/templates/other/full-stack-fastapi-template-with-next-js)_

---

### 데이터베이스: PostgreSQL (Railway 호스팅)

**10년치 시계열 데이터 처리 전략**

이 프로젝트는 1일 매출, 월별 점유율 등의 시계열 데이터를 10년치 기준으로 저장/조회해야 한다.
220개 지점 × 10년 = 약 800,000건 이상의 일 단위 매출 레코드 예상 (규모는 관리 가능).

**권장 전략: 범위 파티셔닝 (Range Partitioning)**

```sql
-- 예: 매출 테이블을 연도 단위로 파티셔닝
CREATE TABLE sales (
    branch_name TEXT,
    customer_email TEXT,
    sale_date DATE NOT NULL,
    daily_revenue NUMERIC
) PARTITION BY RANGE (sale_date);

CREATE TABLE sales_2016 PARTITION OF sales
    FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
-- 연도별 파티션 반복...
```

- BRIN 인덱스: 타임스탬프 컬럼에 효과적. 크기가 매우 작고 순차 데이터에 최적
- 파티션 프루닝: WHERE 절에 파티션 키(날짜)가 포함되어야 작동 → 조회 쿼리 설계 시 필수
- 오래된 파티션 삭제: `DROP TABLE`로 즉시 처리 — `DELETE` 대비 압도적으로 빠름
- `pg_partman` 확장: 파티션 자동 생성 및 유지보수 자동화

_POC 단계에서는 파티셔닝 없이도 충분히 작동하나, 초기 설계에 포함하는 것이 권장됨_

_신뢰도: 높음_
_출처: [AWS RDS 시계열 설계 가이드](https://aws.amazon.com/blogs/database/designing-high-performance-time-series-data-tables-on-amazon-rds-for-postgresql/), [PostgreSQL 공식 파티셔닝 문서](https://www.postgresql.org/docs/current/ddl-partitioning.html), [Neon 시계열 가이드](https://neon.com/guides/timeseries-data)_

---

### 배포 플랫폼: Railway

**공식 지원 현황 (2026 기준)**

Railway는 Next.js + FastAPI + PostgreSQL 풀스택을 하나의 플랫폼에서 공식 지원한다.
- 공식 배포 템플릿 존재: [Deploy Next.js + FastAPI Full-Stack Starter](https://railway.com/deploy/nextjs-fastapi-full-stack-starter)
- PostgreSQL 자동 프로비저닝 및 환경 변수 자동 주입 (`DATABASE_URL`, `PGHOST` 등)
- 프리-배포 마이그레이션(pre-deploy migration) 자동화 지원

**비용 구조 (주의 필요)**

| 플랜 | 월 비용 | 내용 |
|------|---------|------|
| Free Trial | $0 (30일) | $5 크레딧, 카드 불필요 |
| Free Plan | $1 크레딧/월 | DB 포함 시 수일 내 소진 |
| **Hobby** | **$5/월** | POC 운영에 권장 최소 플랜 |
| Pro | $20/월~ | 팀/프로덕션 용도 |

**⚠️ 중요 주의사항:** PostgreSQL 단독으로도 월 $1 크레딧을 초과할 수 있음. POC 시연 목적이라면 **Hobby 플랜($5/월)** 이 현실적인 최소 요건.

대안: Next.js는 Vercel 무료 티어, FastAPI + PostgreSQL만 Railway에 배포하는 분리 전략도 유효.

_신뢰도: 높음_
_출처: [Railway 공식 가이드 - Next.js](https://docs.railway.com/guides/nextjs), [Railway 가격 정책](https://railway.com/pricing), [Medium 배포 가이드](https://medium.com/@zafarobad/ultimate-guide-to-deploying-next-js-d57ab72f6ba6)_

---

### 외부 API: 지도 및 상권 데이터

**한국 지도 API**

| API | 특징 | 비용 |
|-----|------|------|
| **카카오맵 API** | 장소 검색, 지오코딩, 지도 렌더링 | 일정 호출 수까지 무료 |
| 네이버 지도 API | 유사 기능 | 부분 유료 |
| Google Maps | 글로벌 표준, 한국 데이터 일부 미흡 | 유료 |

카카오맵이 한국 POI 데이터 정확도 및 REST API 사용 편의성 측면에서 권장.
JSON 응답으로 장소명, 주소, 좌표(위경도), 카테고리 등 제공.

_출처: [Kakao 지도 API](https://apis.map.kakao.com/), [Kakao Developers REST API](https://developers.kakao.com/docs/latest/ko/local/dev-guide)_

**한국 상권 데이터 API (공공데이터)**

**소상공인시장진흥공단 상가(상권)정보 API** — 가장 핵심적인 무료 공공 API

- 제공처: [공공데이터포털 (data.go.kr)](https://www.data.go.kr/data/15012005/openapi.do)
- 제공 항목: 상가업소번호, 상호명, 주소, 상권업종명, 표준산업분류, **경도/위도**
- 업종 분류: 대분류 10개 → 중분류 75개 → 소분류 247개 (표준산업분류 10차 기반)
- 소상공인365 상권분석: 행정동 단위 **매출, 배달 건수, 업종 분포, 유동인구** 제공
- 신청 방법: data.go.kr 회원가입 → OpenAPI 신청 → 1~2시간 내 호출 가능

**POC 전략:** 외부 API가 준비되기 전까지는 이 공공 API 데이터를 샘플 JSON으로 변환하여 자체 제작 후, 실제 API 연동 시 교체하는 방식으로 구현.

_신뢰도: 높음_
_출처: [소상공인시장진흥공단 상가정보 API](https://www.data.go.kr/data/15012005/openapi.do), [PublicDataReader 가이드](https://github.com/WooilJeong/PublicDataReader/blob/main/assets/docs/portal/SmallShop.md)_

---

### 기술 채택 트렌드 요약

| 영역 | 현재 표준 | 비고 |
|------|-----------|------|
| 프론트엔드 | Next.js 15 + TypeScript | Server Components가 주류로 자리잡음 |
| 백엔드 | FastAPI + Pydantic v2 | AI/ML 연동 확장성 고려 시 최적 |
| DB | PostgreSQL + Range Partitioning | 10년 시계열에 충분한 성능 |
| 배포 | Railway (Hobby) or Vercel+Railway | POC는 단일 플랫폼(Railway) 권장 |
| 지도 | 카카오맵 API | 한국 POI 정확도 최고 |
| 상권 데이터 | 공공데이터포털 (무료) | 소상공인시장진흥공단 API |

---

## Integration Patterns Analysis

### API 설계 패턴 — Next.js ↔ FastAPI 통신

이 프로젝트의 프론트엔드(Next.js)와 백엔드(FastAPI) 사이의 통신 패턴은 크게 3가지로 구분된다.

**패턴 1: Server Components에서 직접 호출 (권장 — 읽기 전용 데이터)**

```typescript
// app/dashboard/page.tsx (Server Component)
async function DashboardPage() {
  const res = await fetch('http://fastapi-internal/branches', {
    cache: 'no-store'  // 또는 revalidate 설정
  });
  const data = await res.json();
  return <BranchTable data={data} />;
}
```
Next.js 서버 → FastAPI를 내부 서비스로 처리. 클라이언트에 FastAPI URL 노출 없음.

**패턴 2: Server Actions (쓰기/변이 작업)**

```typescript
// actions/branch.ts
'use server'
export async function generateData(formData: FormData) {
  await fetch('http://fastapi-internal/data/generate', { method: 'POST' });
  revalidatePath('/dashboard');
}
```
데이터 생성, 삭제, 랜덤 생성 버튼 등에 적합.

**패턴 3: OpenAPI 타입드 클라이언트 자동생성**

FastAPI가 자동 생성하는 OpenAPI 스키마(`/openapi.json`)를 `@hey-api/client-next`로 변환하면 TypeScript 타입드 API 클라이언트 자동 생성 가능 → API 계약 이탈 방지.

_신뢰도: 높음_
_출처: [Next.js Server Actions + FastAPI 통합](https://nemanjamitic.com/blog/2026-01-03-nextjs-server-actions-fastapi-openapi/), [Vinta Template](https://www.vintasoftware.com/blog/next-js-fastapi-template)_

---

### 통신 프로토콜 및 데이터 형식

**HTTP/REST + JSON (기본)**

- 모든 API 통신은 HTTP/HTTPS + JSON
- FastAPI 응답: Pydantic 모델 기반 자동 직렬화
- 페이지네이션: `?skip=0&limit=100` 쿼리 파라미터 패턴 표준
- 게시판 형식의 정렬/필터: `?sort_by=date&order=desc&branch=강남점` 등

**외부 API 연동 데이터 형식**

카카오맵 API JSON 응답 예시 (좌표→주소):
```json
GET /v2/local/geo/coord2address.json?x=127.1&y=37.5&input_coord=WGS84
Authorization: KakaoAK {REST_API_KEY}

{
  "documents": [{
    "address": { "address_name": "서울 강남구 역삼동 123", ... },
    "road_address": { "address_name": "서울 강남구 테헤란로 123", ... }
  }],
  "meta": { "total_count": 1 }
}
```
- XML/JSON 모두 지원, JSON 권장
- WGS84 좌표계 사용 (표준)
- 헤더: `Authorization: KakaoAK {REST_API_KEY}`

_출처: [Kakao Local API 공식 문서](https://developers.kakao.com/docs/latest/en/local/dev-guide)_

---

### FastAPI ↔ PostgreSQL 연동 패턴

**비동기 스택 (권장)**

```python
# database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@host/dbname",  # asyncpg 드라이버 필수
    pool_size=10, max_overflow=20
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# 의존성 주입
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**⚠️ 주의:** `postgresql://` 대신 반드시 `postgresql+asyncpg://` 사용. 잘못 사용 시 에러 없이 이벤트 루프 블로킹 발생.

**마이그레이션: Alembic**

스키마 변경 이력 관리. Railway 배포 시 pre-deploy 훅으로 자동 마이그레이션 실행 가능.

_신뢰도: 높음_
_출처: [FastAPI + SQLAlchemy Async 프로덕션 패턴](https://dev.to/rosewabere/building-a-production-grade-async-backend-with-fastapi-sqlalchemy-postgresql-and-alembic-2ca4)_

---

### 공공데이터 API 연동 패턴 (상권 데이터)

POC 단계 권장 전략 — 2단계 접근:

**1단계 (POC 현재):** 공공데이터 API → 샘플 JSON 파일로 변환 → FastAPI에서 파일 서빙

```python
# FastAPI에서 샘플 JSON 서빙 (외부 API 교체 전)
@router.get("/commercial-area/{address}")
async def get_commercial_area(address: str):
    with open("data/sample_commercial.json") as f:
        return json.load(f)  # 나중에 실제 API 호출로 교체
```

**2단계 (실제 API 연동 후):**
```python
@router.get("/commercial-area/{address}")
async def get_commercial_area(address: str, client: httpx.AsyncClient = Depends()):
    resp = await client.get(
        "https://api.data.go.kr/openapi/tn_pubr_public_cmrcl_zone_info_api",
        params={"ServiceKey": API_KEY, "address": address},
        headers={"Accept": "application/json"}
    )
    return resp.json()
```

이 구조는 idea.md의 요구사항("나중에 외부 API가 완성되면 이걸 바꿔서 적용할 수 있어야 함")을 정확히 충족.

_신뢰도: 높음_
_출처: [공공데이터포털 소상공인 API](https://www.data.go.kr/data/15012005/openapi.do)_

---

### 인증 패턴 (관리자 대시보드)

POC 단계에서 관리자 전용 단일 대시보드이므로, 경량 인증으로 충분.

**권장: JWT + HttpOnly Cookie**

```python
# FastAPI — 로그인 시 JWT 발급
@router.post("/auth/login")
async def login(credentials: LoginRequest):
    # 검증 후
    token = create_jwt_token(user_id)
    response.set_cookie("token", token, httponly=True, secure=True)
    return {"status": "ok"}
```

```typescript
// Next.js — 미들웨어로 보호
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('token');
  if (!token) return NextResponse.redirect('/login');
}
```

- `fastapi-users` 라이브러리: 인증 라우트 완성형 제공, JWT 통합
- `fastapi-nextauth-jwt` 패키지: NextAuth.js와 FastAPI JWT 연동 지원
- POC 단계에서는 단순 Bearer token + localStorage도 가능 (XSS 위험 감수)

_신뢰도: 높음_
_출처: [FastAPI + Next.js JWT 인증](https://medium.com/@sl_mar/building-a-secure-jwt-authentication-system-with-fastapi-and-next-js-301e749baec2), [NextAuth + FastAPI](https://tom.catshoek.dev/posts/nextauth-fastapi/)_

---

### 통합 패턴 요약

| 연동 구간 | 패턴 | 비고 |
|-----------|------|------|
| Next.js → FastAPI (읽기) | Server Component fetch | SSR, 캐시 제어 용이 |
| Next.js → FastAPI (쓰기) | Server Actions | 데이터 생성/삭제 버튼 |
| FastAPI → PostgreSQL | AsyncSession + asyncpg | 비동기 필수, Alembic 마이그레이션 |
| FastAPI → 외부 API | httpx.AsyncClient | 샘플 JSON으로 시작, API 교체 구조 |
| 지도/좌표 | 카카오 REST API | WGS84, Authorization 헤더 |
| 상권 데이터 | 공공데이터포털 OpenAPI | 키 발급 후 1~2시간 내 사용 가능 |
| 인증 | JWT + HttpOnly Cookie | fastapi-users 라이브러리 권장 |

---

## Architectural Patterns and Design

### 시스템 아키텍처 패턴 — 모노레포 vs 분리 서비스

**Railway 기준 두 가지 선택지:**

| 방식 | 구조 | 장점 | 단점 |
|------|------|------|------|
| **모노레포 (권장 — POC)** | 하나의 레포, Railway에서 서비스별 빌드 분리 | 관리 단순, 코드 공유 용이 | 서비스 간 빌드 트리거 관리 필요 |
| **Vercel + Railway 분리** | Next.js → Vercel / FastAPI+DB → Railway | 각 플랫폼 최적화 | 두 플랫폼 관리, CORS 설정 필요 |

**POC 권장 구조 (모노레포):**
```
drksample1/
├── frontend/          # Next.js
│   ├── app/
│   └── package.json
├── backend/           # FastAPI
│   ├── main.py
│   └── requirements.txt
└── railway.toml       # 서비스별 빌드 설정
```

Railway의 Watch Paths 기능으로 `frontend/` 변경 시 프론트만, `backend/` 변경 시 백엔드만 재빌드 가능.

_신뢰도: 높음_
_출처: [Railway 모노레포 가이드](https://docs.railway.com/guides/monorepo), [Next.js + FastAPI 모노레포 API 클라이언트 생성](https://www.vintasoftware.com/blog/nextjs-fastapi-monorepo)_

---

### 관리자 대시보드 아키텍처

**표준 스택: TanStack Table v8 + shadcn/ui DataTable**

이 프로젝트의 핵심 UI인 "10년치 데이터 소팅 게시판"에 가장 적합한 패턴.

```
[URL 쿼리 파라미터] ←→ [TanStack Table] ←→ [FastAPI 서버사이드 페이지네이션]
?page=1&sort=date&order=desc&branch=강남점
```

**서버사이드 페이지네이션/정렬/필터링 패턴:**

```typescript
// FastAPI 엔드포인트
@router.get("/sales")
async def get_sales(
    page: int = 1,
    limit: int = 50,
    sort_by: str = "sale_date",
    order: str = "desc",
    branch_name: Optional[str] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Sales).order_by(...)
    # 필터/정렬/페이지네이션 적용
    return {"data": results, "total": total_count, "page": page}
```

```typescript
// Next.js — URL 쿼리 파라미터로 상태 관리
// app/dashboard/sales/page.tsx
export default async function SalesPage({ searchParams }) {
  const { page, sort_by, order, branch_name, year } = searchParams;
  const data = await fetch(`/api/sales?${new URLSearchParams(searchParams)}`);
  return <DataTable data={data} />;
}
```

**핵심 UI 구성 요소 (idea.md 요구사항 매핑):**

| 요구사항 | 구현 방식 |
|---------|-----------|
| 10년치 데이터 소팅 게시판 | TanStack Table + 서버사이드 정렬 + URL 쿼리 상태 |
| 지점별 수익분석표 | 집계 API 엔드포인트 + 차트 컴포넌트 (recharts/nivo) |
| 점유율 추이 | 날짜 범위 필터 + 라인 차트 |
| 랜덤 데이터 생성 버튼 | Server Action → FastAPI POST `/data/generate` |
| 삭제 버튼 | Server Action → FastAPI DELETE + confirm dialog |

_신뢰도: 높음_
_출처: [shadcn DataTable 필터 템플릿](https://www.shadcn.io/template/openstatushq-data-table-filters), [TanStack Table + 서버사이드 페이지네이션](https://medium.com/@clee080/how-to-do-server-side-pagination-column-filtering-and-sorting-with-tanstack-react-table-and-react-7400a5604ff2), [Next.js 공식 페이지네이션 가이드](https://nextjs.org/learn/dashboard-app/adding-search-and-pagination)_

---

### 데이터 아키텍처 패턴 — PostgreSQL 스키마 설계

**설계 원칙: 정규화 + 날짜 파티셔닝**

idea.md의 DB 설계를 기반으로 분석 최적화 관점에서 보완:

```sql
-- 지점 (Branch) — 마스터 테이블
CREATE TABLE branch (
    branch_name     TEXT PRIMARY KEY,
    address         TEXT NOT NULL,
    area_sqm        NUMERIC,          -- 면적 (㎡)
    monthly_rent    NUMERIC,          -- 임대료
    maintenance_fee NUMERIC,          -- 관리비
    building_usage  TEXT,             -- 건축물용도
    ev_charging     BOOLEAN DEFAULT false,
    parking_count   INTEGER DEFAULT 0
);

-- 운영비 (Operations) — 월별
CREATE TABLE operations (
    id              SERIAL PRIMARY KEY,
    branch_name     TEXT REFERENCES branch(branch_name),
    month           DATE NOT NULL,    -- 해당 월 (월 첫째날로 정규화)
    electricity_fee NUMERIC,
    operating_cost  NUMERIC
);

-- 회원 (Member) — 마스터 테이블
CREATE TABLE member (
    email   TEXT PRIMARY KEY,
    name    TEXT NOT NULL,
    phone   TEXT,
    address TEXT
);

-- 매출 (Sales) — 시계열 핵심 테이블, 파티셔닝 대상
CREATE TABLE sales (
    id            BIGSERIAL,
    branch_name   TEXT REFERENCES branch(branch_name),
    member_email  TEXT REFERENCES member(email),
    sale_date     DATE NOT NULL,
    daily_revenue NUMERIC NOT NULL
) PARTITION BY RANGE (sale_date);

-- 연도별 파티션 예시
CREATE TABLE sales_2016 PARTITION OF sales FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
CREATE TABLE sales_2017 PARTITION OF sales FOR VALUES FROM ('2017-01-01') TO ('2018-01-01');
-- ... 2026까지 반복

-- 성능 인덱스
CREATE INDEX idx_sales_branch_date ON sales (branch_name, sale_date);
CREATE INDEX idx_sales_date_brin ON sales USING BRIN (sale_date);
```

**집계 쿼리 패턴 (점유율/수익분석):**

```sql
-- 지점별 월간 매출 집계
SELECT
    branch_name,
    DATE_TRUNC('month', sale_date) AS month,
    SUM(daily_revenue)             AS monthly_revenue,
    COUNT(DISTINCT member_email)   AS unique_customers
FROM sales
WHERE sale_date BETWEEN '2020-01-01' AND '2025-12-31'
GROUP BY branch_name, DATE_TRUNC('month', sale_date)
ORDER BY month DESC;
```

**10년치 랜덤 데이터 생성 전략:**

```python
# FastAPI — 랜덤 데이터 생성 엔드포인트
@router.post("/data/generate")
async def generate_sample_data(db: AsyncSession = Depends(get_db)):
    # 수도권 220개 가상 지점 × 10년 × 365일 ≈ 803,000건
    # 배치 INSERT로 처리 (1000건씩)
    ...
```

_신뢰도: 높음_
_출처: [PostgreSQL 시계열 스키마 설계 모범 사례](https://www.tigerdata.com/learn/best-practices-time-series-data-modeling-single-or-multiple-partitioned-tables-aka-hypertables), [스토어 분석 PostgreSQL](https://www.alibabacloud.com/blog/postgresql-time-series-best-practices-stock-exchange-system-database_594815)_

---

### 보안 아키텍처

- **CORS 설정**: FastAPI에서 Next.js 도메인만 허용 (Railway 내부 통신 시 생략 가능)
- **환경 변수**: Railway가 `DATABASE_URL`, `SECRET_KEY` 등 자동 주입
- **API 키 보안**: 카카오맵/공공데이터 API 키는 FastAPI 서버에서만 사용 (프론트 노출 금지)
- **관리자 인증**: JWT HttpOnly Cookie — XSS 방어

---

### 배포 아키텍처 (Railway 기준)

```
Railway Project
├── Service: next-frontend     (Next.js, Port 3000)
│   └── Env: FASTAPI_URL=http://fastapi-backend.railway.internal
├── Service: fastapi-backend   (FastAPI, Port 8000)
│   └── Env: DATABASE_URL=${{PostgreSQL.DATABASE_URL}}
└── Service: PostgreSQL        (Railway 관리형 DB)
```

- Railway 내부 네트워크(`*.railway.internal`)로 서비스 간 통신 → 외부 노출 최소화
- Pre-deploy 훅으로 `alembic upgrade head` 자동 실행

_신뢰도: 높음_
_출처: [Railway 공식 배포 가이드](https://docs.railway.com/guides/fastapi), [Medium 배포 전략 비교](https://medium.com/@zafarobad/ultimate-guide-to-deploying-next-js-d57ab72f6ba6)_

---

## Implementation Approaches and Technology Adoption

### 기술 채택 전략 — POC 시작점

**권장: 공식 템플릿으로 시작**

처음부터 설정을 직접 구성하는 대신, 검증된 템플릿을 기반으로 POC를 시작하는 것이 가장 빠른 경로다.

| 템플릿 | 특징 | 적합 시나리오 |
|--------|------|---------------|
| **[Vinta nextjs-fastapi-template](https://github.com/vintasoftware/nextjs-fastapi-template)** | FastAPI + Next.js + JWT 인증 + async PostgreSQL + Alembic + pytest | 이 프로젝트에 가장 적합 |
| [Vercel nextjs-fastapi-starter](https://vercel.com/templates/next.js/nextjs-fastapi-starter) | 경량, Vercel 배포 최적화 | Vercel 배포 시 |
| [Full Stack FastAPI Template (공식)](https://fastapi.tiangolo.com/project-generation/) | FastAPI 공식 권장 | 백엔드 우선 |

**POC 구현 단계 (권장 순서):**

```
1. 템플릿 클론 + Railway 연결 (1일)
2. DB 스키마 정의 + Alembic 마이그레이션 (1일)
3. 샘플 데이터 생성 엔드포인트 구현 (1일)
4. 관리자 대시보드 페이지 구현 (2~3일)
   - 지점별 수익분석표
   - 10년치 데이터 게시판 (정렬/필터)
   - 랜덤 생성/삭제 버튼
5. 카카오맵 + 공공데이터 API 샘플 연동 (1일)
6. Railway 배포 및 환경 변수 설정 (0.5일)
```

_신뢰도: 높음_
_출처: [Vinta Template 시작 가이드](https://vintasoftware.github.io/nextjs-fastapi-template/get-started/), [Full Stack Next.js FastAPI PostgreSQL 튜토리얼](https://www.travisluong.com/how-to-build-a-full-stack-next-js-fastapi-postgresql-boilerplate-tutorial/)_

---

### 개발 워크플로우 및 CI/CD

**Railway + GitHub 자동 배포:**

Railway는 GitHub 저장소와 직접 연동되어, `main` 브랜치 푸시 시 자동 빌드/배포가 트리거된다.

```yaml
# .github/workflows/deploy.yml (선택사항 — Railway 자체 자동배포로도 충분)
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest backend/tests/
  # Railway는 "Wait for CI" 옵션으로 GitHub Actions 성공 후 배포 가능
```

**권장 워크플로우:**
1. 로컬 개발 → Git Push
2. GitHub Actions: pytest 자동 실행
3. Railway "Wait for CI" 옵션: 테스트 통과 후 자동 배포
4. Railway Pre-deploy: `alembic upgrade head` 자동 실행

_신뢰도: 높음_
_출처: [Railway GitHub 자동배포](https://docs.railway.com/deployments/github-autodeploys), [Railway CI/CD 가이드](https://blog.railway.com/p/cicd-for-modern-deployment-from-manual-deploys-to-pr-environments)_

---

### 테스트 전략

**FastAPI 테스트 스택:**

```python
# requirements-test.txt
pytest
pytest-asyncio
httpx          # FastAPI TestClient 기반
sqlalchemy[asyncio]
asyncpg

# conftest.py — 테스트 DB 격리
@pytest.fixture(scope="function")
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# 테스트 예시
async def test_get_sales(client: AsyncClient, db_session):
    response = await client.get("/sales?page=1&limit=10")
    assert response.status_code == 200
    assert "data" in response.json()
```

**POC 단계 테스트 범위:**
- API 엔드포인트 기본 동작 (200 OK / 404 / 422)
- 데이터 생성/조회/삭제 기능
- 페이지네이션 파라미터 처리

_신뢰도: 높음_
_출처: [FastAPI + pytest 공식 문서](https://fastapi.tiangolo.com/tutorial/testing/), [비동기 테스트 가이드](https://testdriven.io/blog/fastapi-crud/)_

---

### 비용 최적화 및 리소스 관리

**Railway 비용 시나리오:**

| 구성 | 예상 월 비용 | 비고 |
|------|-------------|------|
| Free Plan | $0 + $1 크레딧 | DB 포함 시 수일 내 소진, POC 불가 |
| **Hobby Plan (권장)** | **$5 + 사용량** | 3개 서비스(Next.js/FastAPI/DB) 운영 가능 |
| Vercel(무료) + Railway Hobby | ~$5 | Next.js를 Vercel로 분리하면 Railway 비용 절감 |

**비용 최소화 팁:**
- Railway 수면 모드(Sleeping): 트래픽 없을 때 서비스 자동 절전 → POC 시연 전 워밍업 필요
- PostgreSQL 볼륨: 10년치 220지점 데이터(~80만 건) ≈ 약 500MB ~ 1GB 예상, Hobby 허용 범위

---

### 위험 요소 및 완화 전략

| 위험 | 발생 가능성 | 영향도 | 완화 전략 |
|------|------------|--------|-----------|
| Railway 비용 초과 (Free Plan) | **높음** | 중 | Hobby $5/월 필수, 시작 전 카드 등록 |
| `postgresql://` vs `postgresql+asyncpg://` 오류 | **높음** | 높음 | 환경 변수 설정 시 드라이버 접두사 필수 확인 |
| 공공데이터 API 키 발급 지연 | 낮음 | 낮음 | 사전 신청 (1~2시간 소요), 샘플 JSON으로 대체 가능 |
| 카카오맵 API 일일 호출 한도 | 낮음 | 낮음 | POC 수준은 무료 한도 내 충분 |
| 10년 데이터 랜덤 생성 속도 | 중간 | 중간 | 배치 INSERT(1000건) + 백그라운드 작업 or 직접 SQL COPY |
| Next.js ↔ FastAPI CORS 오류 | **높음** | 중 | FastAPI `CORSMiddleware` 초기 설정 필수 |

---

## Technical Research Recommendations

### 구현 로드맵

**Phase 1 — 기반 구축 (1주):**
- Vinta 템플릿 클론 → Railway 연결 → PostgreSQL 프로비저닝
- DB 스키마(branch/operations/member/sales) 정의 + Alembic 마이그레이션
- FastAPI CORSMiddleware, 환경 변수 설정

**Phase 2 — 핵심 기능 (1~2주):**
- 관리자 대시보드 레이아웃 (shadcn/ui + TailwindCSS)
- 수익분석표 API + 차트 컴포넌트
- 10년 데이터 게시판 (TanStack Table + 서버사이드 페이지네이션)
- 랜덤 데이터 생성/삭제 버튼

**Phase 3 — 외부 API 연동 + 완성 (0.5~1주):**
- 카카오맵 API 샘플 연동
- 공공데이터 상권 API 샘플 연동 (샘플 JSON 구조 결정)
- Railway 배포 최종 확인 + 시연 준비

### 기술 스택 최종 권장

```
프론트엔드:  Next.js 15 + TypeScript + shadcn/ui + TailwindCSS + TanStack Table
백엔드:      FastAPI + Pydantic v2 + SQLAlchemy 2.0 (async) + Alembic
DB:          PostgreSQL (Railway) + Range Partitioning (sale_date)
배포:        Railway (Hobby $5/월) — 모노레포 단일 프로젝트
지도:        카카오맵 REST API
상권 데이터: 소상공인시장진흥공단 공공데이터 API (data.go.kr)
인증:        fastapi-users + JWT HttpOnly Cookie
테스트:      pytest + pytest-asyncio + httpx
```

### 성공 지표

- [ ] Railway에서 3개 서비스 정상 운영 (Next.js + FastAPI + PostgreSQL)
- [ ] 10년치 샘플 데이터 생성 버튼 동작 (< 30초)
- [ ] 게시판 페이지에서 날짜/지점별 정렬 동작
- [ ] 수익분석표(매출/전기세/운영비) 집계 정확성
- [ ] 카카오맵 API + 공공데이터 API 샘플 JSON 연동 확인

---

## 미래 기술 전망

### 단기 (1~2년)

- **AI 입지 예측 연동 가능성**: 공공데이터(유동인구, 소득, 아파트 정보) + 브랜드 내부 데이터(점유율, 매출) 조합으로 ML 기반 수익 예측 모델 추가 가능. FastAPI는 Python ML 라이브러리(scikit-learn, pandas)와 자연스럽게 연동됨
- **실시간 부동산 알림**: 적합 물건 신규 등록 시 자동 알림 기능 — FastAPI 백그라운드 태스크 또는 메시지 큐(Redis) 추가로 구현 가능
- **모바일 대응**: Next.js 반응형 UI로 태블릿/모바일 지원은 별도 작업 없이 TailwindCSS 기반으로 자연스럽게 확장

### 중기 (3~5년)

- **수익 시뮬레이션 정교화**: 220개 지점 실제 데이터 누적 후 더 정밀한 입지 수익성 예측 모델 가능
- **외부 API 생태계 확대**: 국토교통부 실거래가 API, 건축물대장 API 등 추가 공공 데이터 연동으로 분석 고도화

---

## 리서치 방법론 및 출처 목록

### 웹 검색 쿼리 목록

1. `Next.js FastAPI integration patterns full stack 2025 2026`
2. `Railway deployment Next.js FastAPI PostgreSQL full stack 2025 2026`
3. `Korea map API 카카오맵 상권분석 API commercial area analysis JSON 2025`
4. `PostgreSQL time series data 10 years performance indexing partitioning 2025`
5. `소상공인시장진흥공단 상권분석 API 공공데이터포털 2025`
6. `Railway.app pricing limits free tier PostgreSQL 2025 2026`
7. `Next.js call FastAPI REST API patterns server components server actions 2025`
8. `FastAPI SQLAlchemy async PostgreSQL integration pattern 2025`
9. `Kakao map API REST integration JSON response format geocoding 2025`
10. `Next.js admin dashboard JWT authentication FastAPI 2025`
11. `Next.js FastAPI monorepo vs separate services architecture Railway deployment 2025`
12. `admin dashboard architecture Next.js data table sorting filtering pagination best practices 2025`
13. `PostgreSQL schema design time series sales data branch store analytics 2025`
14. `FastAPI pytest async testing PostgreSQL 2025 best practices`
15. `Railway CI/CD GitHub Actions deployment pipeline 2025`
16. `Next.js FastAPI POC starter project setup steps 2025 2026`
17. `셀프스토리지 미니창고 입지분석 AI 디지털전환 기술 동향 2025 2026`

### 주요 출처

| 분야 | 출처 | URL |
|------|------|-----|
| Next.js + FastAPI 템플릿 | Vinta Software | [vintasoftware.com](https://www.vintasoftware.com/blog/next-js-fastapi-template) |
| Next.js + FastAPI 공식 템플릿 | Vercel | [vercel.com/templates](https://vercel.com/templates/other/full-stack-fastapi-template-with-next-js) |
| Railway 풀스택 배포 | Railway 공식 | [railway.com/deploy](https://railway.com/deploy/nextjs-fastapi-full-stack-starter) |
| Railway 모노레포 가이드 | Railway Docs | [docs.railway.com](https://docs.railway.com/guides/monorepo) |
| Railway 가격 정책 | Railway | [railway.com/pricing](https://railway.com/pricing) |
| 카카오맵 REST API | Kakao Developers | [developers.kakao.com](https://developers.kakao.com/docs/latest/en/local/dev-guide) |
| 소상공인 상권 API | 공공데이터포털 | [data.go.kr](https://www.data.go.kr/data/15012005/openapi.do) |
| PostgreSQL 파티셔닝 공식 문서 | PostgreSQL | [postgresql.org](https://www.postgresql.org/docs/current/ddl-partitioning.html) |
| FastAPI async SQLAlchemy | DEV Community | [dev.to](https://dev.to/rosewabere/building-a-production-grade-async-backend-with-fastapi-sqlalchemy-postgresql-and-alembic-2ca4) |
| Server Actions + FastAPI | Nemanja Mitic | [nemanjamitic.com](https://nemanjamitic.com/blog/2026-01-03-nextjs-server-actions-fastapi-openapi/) |
| TanStack Table + 서버사이드 | Medium | [medium.com](https://medium.com/@clee080/how-to-do-server-side-pagination-column-filtering-and-sorting-with-tanstack-react-table-and-react-7400a5604ff2) |
| FastAPI 테스트 공식 | FastAPI | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/tutorial/testing/) |
| JWT + Next.js 인증 | Medium | [medium.com](https://medium.com/@sl_mar/building-a-secure-jwt-authentication-system-with-fastapi-and-next-js-301e749baec2) |
| 다락 브랜드 현황 | HelloT | [hellot.net](https://www.hellot.net/news/article.html?no=112282) |

### 신뢰도 평가

- **높음**: 공식 문서, 공식 템플릿, Railway/Vercel/FastAPI/PostgreSQL 공식 가이드 기반 내용
- **중간**: 커뮤니티 블로그(DEV Community, Medium) 기반 내용 — 다수 출처 교차 검증 완료
- **낮음**: 해당 없음 (불확실한 내용은 별도 표기)

---

## 결론

셀프스토리지 브랜드 입지분석 관리자 웹 서비스 POC는 **Next.js 15 + FastAPI + PostgreSQL + Railway** 스택으로 약 **2.5~3주** 내에 구현 가능하며, 기술적 위험은 관리 가능한 수준이다.

가장 중요한 즉각적 조치사항:
1. **Railway Hobby 플랜 등록** (Free Plan 절대 불가)
2. **data.go.kr API 키 사전 신청** (소상공인시장진흥공단 상권 API)
3. **Vinta 템플릿 클론으로 시작** — 처음부터 만들지 말 것

이 POC가 성공하면, 이후 AI 기반 수익 시뮬레이션, 실시간 부동산 알림, ML 예측 모델 추가로 자연스럽게 확장 가능한 아키텍처다.

---

**리서치 완료일:** 2026-06-12
**리서치 기간:** 종합 기술 분석 (2026-06-12 단일 세션)
**소스 검증:** 17개 웹 검색, 14개 이상 독립 출처 교차 검증
**기술 신뢰도:** 높음 — 공식 문서 및 다수 검증된 출처 기반

_본 리서치 문서는 drksample1 프로젝트의 PRD 및 아키텍처 설계의 기술적 근거 자료로 활용된다._
