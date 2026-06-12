---
stepsCompleted: [1, 2, 3, 4]
status: complete
completedAt: '2026-06-12'
inputDocuments:
  - planning-artifacts/prds/prd-drksample1-2026-06-12/prd.md
  - planning-artifacts/architecture.md
  - planning-artifacts/ux-design-specification.md
---

# drksample1 - Epic Breakdown

## Overview

셀프스토리지 브랜드 입지분석 관리자 웹 서비스 POC의 전체 에픽 및 스토리 분해 문서.
PRD(FR 8개), UX 설계, 아키텍처 결정을 구현 가능한 스토리로 분해한다.

---

## Requirements Inventory

### Functional Requirements

FR-1: 관리자는 주소, 면적(㎡), 월 임대료, 관리비, 건축물용도, EV충전 여부, 주차 가능 대수를 입력하여 시뮬레이션을 요청할 수 있다. 필수 항목(주소, 면적, 임대료) 미입력 시 제출 버튼 비활성화, 제출 시 3초 이내 결과 화면 전환.

FR-2: 시스템은 입력된 입지 조건과 유사한 기존 가상 지점군을 추출하여 예상 수익 지표를 산출한다. 면적±30%/임대료±30%/지역(구) 기준 유사 지점 추출 → 가중 평균(area 0.45/rent 0.30/region 0.25) → EV/주차 보정 → 순수익 계산 → 백분위 → 종합 판정(추천/검토필요/비추천). 유사 지점 5개 미만 시 단계적 완화(±50% → 전체 평균) + 경고 배너.

FR-3: 시뮬레이션 결과를 카카오맵(★핀+●인근지점), 입지 조건 요약, 결과 수치+비교 차트+판정 배지, "제안서 출력" 버튼으로 표시한다. 지오코딩은 서버사이드 처리. 결과 카드는 슬라이드인 애니메이션.

FR-4: 관리자가 "제안서 출력" 클릭 시 2초 이내 모달 팝업이 열린다. 제안서 구성: 브랜드 로고+날짜, 물건 정보, 시뮬레이션 결과 도표, 유사 지점 비교 차트, 종합 판정 배지. A4 비율, 인쇄/PDF 최적화 서식.

FR-5: 관리자는 팝업 내 "PDF 저장" 버튼으로 제안서를 PDF 파일로 다운로드할 수 있다. 파일명: `수익분석제안서_{주소}_{날짜}.pdf`. 레이아웃 유지.

FR-6: 관리자는 전체 지점 수익 실적을 테이블로 조회할 수 있다. 컬럼: 지점명, 주소, 기준연월, 월 매출, 전기세, 운영비, 순수익, 점유율. 기본 정렬: 기준연월 내림차순, 페이지당 50건, 페이지네이션.

FR-7: 관리자는 컬럼 헤더 클릭으로 오름/내림차순 정렬, 지점명·연도 필터를 사용할 수 있다. 필터·정렬 상태가 URL 쿼리 파라미터에 반영되어 공유 가능.

FR-8: 관리자는 전체 가상 데이터를 재생성하거나 삭제할 수 있다. 각 액션 전 확인 다이얼로그 필수. 재생성: 수도권 가상 지점, 2016~2025년 10년치, 30초 이내 완료.

### NonFunctional Requirements

NFR-1: 반응형 웹, 데스크탑 기준 설계 (1280px 이상 기본, 1024px 이상 지원).

NFR-2: 카카오맵/공공데이터 API 키는 FastAPI 서버에서만 처리. 프론트엔드 코드 및 클라이언트에 절대 노출 금지.

NFR-3: 지도 데이터 프로바이더 추상화 레이어(MapProvider ABC) — v2에서 네이버 부동산 API 교체 시 프론트엔드 변경 없음.

NFR-4: 시뮬레이션 엔진 추상화(SimulationEngine ABC) — rule_based(v1) ↔ ml(나중 구현) 전환을 config.py로 제어 가능.

NFR-5: 단순 로그인 (admin 하드코딩 계정). JWT HttpOnly Cookie. 세션 만료 시 /login 리다이렉트.

NFR-6: Railway Hobby 플랜 ($5/월) 배포. Free Plan 사용 금지. asyncpg postgresql+asyncpg:// 드라이버 필수.

NFR-7: WCAG AA 접근성 — 텍스트 명도대비 4.5:1 이상, 최소 터치 영역 44px, 키보드 탐색.

### Additional Requirements

ARCH-1: [스타터 템플릿] Vinta nextjs-fastapi-template 클론으로 프로젝트 초기화. `git clone`, `uv sync`, `pnpm install`, `.env` 설정, `railway.toml` 생성.

ARCH-2: DB 스키마 4개 테이블(branches, operations, members, sales) 생성. sales 테이블은 sale_date 기준 Range Partitioning (연도별). Alembic 마이그레이션.

ARCH-3: SimulationEngine ABC 구현 — RuleBasedEngine(완전 구현) + MLEngine(stub, RuleBasedEngine 위임). 엔진 팩토리 get_engine() 함수.

ARCH-4: MapProvider ABC 구현 — KakaoMapProvider(v1). geocode(address) + get_nearby_branches() 인터페이스.

ARCH-5: 가상 데이터 생성 — asyncpg.copy_records_to_table() COPY 프로토콜. BackgroundTasks → 즉시 202 응답.

ARCH-6: GitHub Actions CI/CD — pytest → Railway 자동 배포. Railway "Wait for CI" 옵션.

ARCH-7: PDF 생성 — html2canvas + jsPDF. proposal-document.tsx는 순수 CSS/SVG 차트 (Recharts 미사용).

### UX Design Requirements

UX-DR1: 다락 브랜드 컬러 토큰 구현 — Primary #2563EB, Success #16A34A, Warning #D97706, Danger #DC2626, Background #FFFFFF, Surface #F8FAFC, Border #E2E8F0, Text-1 #0F172A, Text-2 #64748B.

UX-DR2: Pretendard 폰트 전역 적용 — H1 28px/Bold, H2 20px/SemiBold, H3 16px/SemiBold, Body 14px/Regular, Small 12px/Regular.

UX-DR3: Page 1 레이아웃 — 좌측 패널 380px 고정 + 우측 지도 flex-1. 네비게이션 바(입지분석|게시판).

UX-DR4: LocationInput 컴포넌트 — 주소 입력 + 지오코딩 인라인 스피너.

UX-DR5: KakaoMapView 컴포넌트 — ★핀(분석대상, 파란) + ●핀(인근지점, 회색) 렌더링. 핀 페이드인 0.3s 애니메이션.

UX-DR6: SimulationResultCard 컴포넌트 — 예상 월매출/점유율/순수익 수치 + 슬라이드인 애니메이션.

UX-DR7: VerdictBadge 컴포넌트 — 추천(green, 상위 30%↑)/검토필요(amber, 30~60%)/비추천(red, 하위 40%↓).

UX-DR8: ComparisonBarChart 컴포넌트 — 유사 지점 대비 막대그래프. 분석 대상 바 파란색 강조 (Recharts).

UX-DR9: ProposalModal 컴포넌트 — shadcn Dialog 기반, 680px 너비(A4 비율), 스크롤 가능. X 버튼으로만 닫기.

UX-DR10: ProposalDocument 컴포넌트 — PDF 출력용 레이아웃. 순수 CSS/SVG 차트. html2canvas 타겟.

UX-DR11: BranchDataTable 컴포넌트 — TanStack Table v8 서버사이드. 컬럼: 지점명/주소/기준연월/월매출/전기세/운영비/순수익/점유율.

UX-DR12: TableToolbar 컴포넌트 — 연도 필터(셀렉트) + 지점명 검색(텍스트) + 전체재생성 버튼 + 전체삭제 버튼.

UX-DR13: 버튼 계층 구현 — Primary(#2563EB 배경+흰 텍스트), Secondary(흰 배경+테두리), Destructive(흰 배경+빨간 테두리).

UX-DR14: 로딩 상태 패턴 — 시뮬레이션 실행 중: 버튼 비활성 + 인라인 스피너 + "분석 중..." 텍스트.

UX-DR15: 빈 상태 구현 — 게시판 데이터 없음 시: "데이터가 없습니다. 전체 재생성 버튼을 눌러주세요." + 버튼.

UX-DR16: WCAG AA 접근성 — 지도 aria-label, 비활성 버튼 disabled+aria-disabled, Tab 순서 논리적.

UX-DR17: 반응형 — 1280px+(기본), 1024~1279px(laptop: 패널 320px), 768~1023px(tablet: 상하 분할).

### FR Coverage Map

FR-1 → Epic 2 (입지 조건 입력 폼)
FR-2 → Epic 2 (수익 시뮬레이션 연산)
FR-3 → Epic 2(결과 카드/판정) + Epic 3(지도 시각화)
FR-4 → Epic 3 (제안서 팝업)
FR-5 → Epic 3 (PDF 다운로드)
FR-6 → Epic 4 (게시판 테이블)
FR-7 → Epic 4 (정렬/필터)
FR-8 → Epic 4 (데이터 생성/삭제)
ARCH-1~4,6 → Epic 1 (기반 구축)
ARCH-5 → Epic 4 (asyncpg COPY 배치 생성)
ARCH-7 → Epic 3 (PDF 생성)
NFR-1,7 → Epic 1,2,3,4 (반응형/접근성, 각 에픽에 적용)
NFR-2,3,4 → Epic 1 (API 키 보안, 프로바이더/엔진 추상화)
NFR-5,6 → Epic 1 (인증, Railway 배포)
UX-DR1~3, UX-DR13 → Epic 1 (컬러/폰트/레이아웃/버튼)
UX-DR4,6,7,14 → Epic 2 (입력/결과 컴포넌트)
UX-DR5,8,9,10,16,17 → Epic 3 (지도/제안서 컴포넌트)
UX-DR11,12,15 → Epic 4 (게시판 컴포넌트)

## Epic List

### Epic 1: 프로젝트 기반 구축
관리자가 로그인하고 앱의 기본 골격이 동작한다.
**FRs covered:** ARCH-1~4,6, NFR-2~6, UX-DR1~3, UX-DR13

### Epic 2: 시뮬레이션 입력 & 결과 계산
관리자가 입지 조건을 입력하면 수익 시뮬레이션 결과(수치+판정)를 받는다.
**FRs covered:** FR-1, FR-2, FR-3(일부), UX-DR4,6,7, UX-DR14

### Epic 3: 지도 시각화 & 제안서 PDF 출력
관리자가 지도에서 결과를 확인하고 PDF 제안서를 다운로드한다.
**FRs covered:** FR-3(지도), FR-4, FR-5, ARCH-7, UX-DR5,8,9,10, UX-DR16,17

### Epic 4: 수익분석표 게시판 & 데이터 관리
관리자가 10년치 가상 데이터를 조회·정렬·필터하고 재생성/삭제한다.
**FRs covered:** FR-6, FR-7, FR-8, ARCH-5, UX-DR11,12,15

---

## Epic 1: 프로젝트 기반 구축

관리자가 로그인하고 앱의 기본 골격이 동작한다. 이후 모든 에픽의 기술적 토대를 마련한다.

### Story 1.1: 프로젝트 초기화 & Railway 배포 환경 구성

As a 개발자,
I want Vinta nextjs-fastapi-template 기반으로 프로젝트를 초기화하고 Railway에 자동 배포되는 환경을 구성하고 싶다,
So that 팀 전체가 동일한 개발 환경에서 시작하고 코드 푸시 시 Railway에 자동 배포할 수 있다.

**Acceptance Criteria:**

**Given** git clone 완료, uv sync, pnpm install 실행
**When** `make start-backend` 및 `make start-frontend` 실행
**Then** FastAPI가 :8000, Next.js가 :3000에서 정상 기동됨

**Given** main 브랜치에 push
**When** GitHub Actions CI 실행
**Then** pytest가 통과하고 Railway에 자동 배포됨

**Given** railway.toml에 fastapi-backend, nextjs-frontend 서비스 정의
**When** Railway 배포 실행
**Then** 3개 서비스(FastAPI, Next.js, PostgreSQL)가 독립적으로 빌드/기동됨

**Given** .env.example 파일 존재
**When** 신규 개발자가 .env 복사 후 SECRET_KEY 생성
**Then** `python3 -c "import secrets; print(secrets.token_hex(32))"` 명령으로 키 생성 가능

---

### Story 1.2: 데이터베이스 스키마 & Alembic 마이그레이션

As a 개발자,
I want 4개 테이블(branches, operations, members, sales)과 Alembic 마이그레이션을 구성하고 싶다,
So that 이후 모든 스토리가 DB에 데이터를 저장하고 조회할 수 있다.

**Acceptance Criteria:**

**Given** `alembic upgrade head` 실행
**When** PostgreSQL DB에 마이그레이션 적용
**Then** branches, operations, members, sales 테이블이 생성됨. sales 테이블에 2016~2025년 연도별 파티션 10개가 존재함

**Given** idx_sales_branch_date(복합), idx_sales_date_brin(BRIN) 인덱스 정의
**When** 마이그레이션 완료
**Then** 두 인덱스가 정상 생성됨

**Given** `alembic downgrade -1` 실행
**When** 롤백 수행
**Then** 직전 마이그레이션 상태로 복원됨 (롤백 성공 확인)

**Given** `postgresql+asyncpg://` 드라이버 URL 설정
**When** FastAPI 시작
**Then** 비동기 DB 커넥션이 정상 수립됨. `postgresql://` URL 사용 시 시작 시 경고 로그 출력됨

---

### Story 1.3: SimulationEngine & MapProvider 추상화 구현

As a 개발자,
I want SimulationEngine ABC와 MapProvider ABC를 구현하고 Kakao API 키 연결을 검증하고 싶다,
So that 시뮬레이션과 지도 기능이 나중에 다른 엔진/프로바이더로 교체 가능한 구조로 동작한다.

**Acceptance Criteria:**

**Given** `SIMULATION_ENGINE=rule_based` 환경 변수 설정
**When** `get_engine()` 팩토리 함수 호출
**Then** RuleBasedEngine 인스턴스가 반환됨

**Given** `SIMULATION_ENGINE=ml` 환경 변수 설정
**When** `get_engine()` 호출
**Then** MLEngine 인스턴스가 반환되고, predict() 호출 시 RuleBasedEngine에 위임됨 (stub 동작)

**Given** 유효한 KAKAO_REST_API_KEY 환경 변수
**When** `KakaoMapProvider.geocode("서울 강남구 역삼동 123")` 호출
**Then** 위경도 Coordinates 객체가 반환됨

**Given** KAKAO_REST_API_KEY 미설정
**When** FastAPI 서버 시작
**Then** 서버 기동 시 환경 변수 누락 오류 발생 (시작 차단)

**Given** `schemas/map.py`에 Coordinates, BranchPin 타입 정의
**When** MapProvider.get_nearby_branches() 호출
**Then** BranchPin 리스트 반환됨 (계약 준수)

---

### Story 1.4: JWT 인증 & 로그인 페이지

As a 관리자,
I want admin 계정으로 로그인하고 싶다,
So that 보호된 대시보드 페이지에 접근할 수 있다.

**Acceptance Criteria:**

**Given** `/login` 페이지에서 admin 자격증명 입력
**When** "로그인" 버튼 클릭
**Then** JWT HttpOnly Cookie가 발급되고 `/dashboard/simulation`으로 리다이렉트됨

**Given** 로그인하지 않은 상태
**When** `/dashboard/*` 경로 직접 접근
**Then** `middleware.ts`가 `/login`으로 리다이렉트함

**Given** 잘못된 비밀번호 입력
**When** 로그인 시도
**Then** "로그인 정보가 올바르지 않습니다" 오류 표시. FastAPI HTTP 401 응답.

**Given** JWT 토큰 만료
**When** 보호된 페이지 접근
**Then** `/login`으로 자동 리다이렉트됨

**Given** `POST /auth/logout` 요청
**When** 로그아웃 실행
**Then** JWT Cookie가 삭제되고 `/login`으로 리다이렉트됨

---

### Story 1.5: 기본 레이아웃 & 다락 브랜드 적용

As a 관리자,
I want 로그인 후 다락 브랜드가 적용된 네비게이션과 레이아웃을 보고 싶다,
So that 어떤 페이지에 있는지 파악하고 입지분석·게시판 사이를 이동할 수 있다.

**Acceptance Criteria:**

**Given** 로그인 완료 후 `/dashboard/*` 접근
**When** 레이아웃 렌더링
**Then** 상단 네비게이션에 다락 로고, "입지분석" 링크, "게시판" 링크가 표시됨

**Given** Pretendard 폰트, #2563EB 컬러 토큰 tailwind.config.ts 설정
**When** 페이지 렌더링
**Then** 모든 텍스트가 Pretendard로 표시되고 Primary 버튼이 #2563EB 배경으로 렌더링됨

**Given** 1280px 이상 데스크탑 화면
**When** `/dashboard/simulation` 접근
**Then** 좌측 380px 고정 패널 + 우측 flex-1 영역 레이아웃이 적용됨

**Given** 현재 페이지가 "입지분석"
**When** 네비게이션 렌더링
**Then** "입지분석" 링크가 활성 스타일(#2563EB 배경)로 강조됨

---

## Epic 2: 시뮬레이션 입력 & 결과 계산

관리자가 입지 조건을 입력하면 수익 시뮬레이션 결과(수치+판정)를 받는다.

### Story 2.1: 입지 조건 입력 폼

As a 관리자,
I want 검토 중인 부동산의 입지 조건을 입력하고 싶다,
So that 시뮬레이션 실행 버튼을 클릭하여 수익 분석을 시작할 수 있다.

**Acceptance Criteria:**

**Given** `/dashboard/simulation` 페이지 접근
**When** 페이지 렌더링
**Then** 주소(텍스트), 면적(숫자), 월 임대료(숫자), 관리비(숫자), 건축물용도(셀렉트), EV충전(토글), 주차대수(숫자) 입력 필드가 표시됨

**Given** 필수 항목(주소, 면적, 임대료) 중 하나 이상 미입력
**When** 폼 상태 확인
**Then** "시뮬레이션 실행" 버튼이 비활성(disabled) 상태임

**Given** 모든 필수 항목 입력 완료
**When** "시뮬레이션 실행" 버튼 클릭
**Then** 버튼이 비활성화되고 "분석 중..." 인라인 스피너가 표시됨 (UX-DR14)

**Given** 잘못된 데이터 형식(예: 면적에 문자 입력)
**When** 해당 필드에서 포커스 이탈(blur)
**Then** 필드 하단에 빨간 오류 메시지가 표시되고 테두리가 빨간색으로 강조됨

---

### Story 2.2: 수익 시뮬레이션 연산 API

As a 시스템,
I want 입력된 입지 조건으로 유사 지점을 추출하고 수익 지표를 계산하고 싶다,
So that 관리자에게 예상 월매출, 점유율, 순수익, 종합 판정을 반환할 수 있다.

**Acceptance Criteria:**

**Given** 유효한 입지 조건 JSON payload
**When** `POST /simulation/run` 호출
**Then** 3초 이내에 SimulationResult(monthly_revenue, occupancy_rate, net_profit, percentile, verdict) 반환됨

**Given** 면적±30%, 임대료±30%, 같은 구 기준 유사 지점 5개 이상 존재
**When** RuleBasedEngine.predict() 실행
**Then** 유사 지점군의 가중 평균(area 0.45/rent 0.30/region 0.25)으로 결과 계산됨

**Given** 1차 기준(±30%, 구) 유사 지점 5개 미만
**When** RuleBasedEngine.predict() 실행
**Then** 2차 기준(±50%, 시)으로 재검색. 여전히 부족하면 전체 평균 사용. 응답에 `fallback_used: true` 포함.

**Given** EV 충전 가능한 물건
**When** 시뮬레이션 계산
**Then** 예상 월매출에 1.08 보정 계수 적용됨

**Given** 전체 지점 중 순수익 상위 30% 물건
**When** 종합 판정 계산
**Then** verdict가 "추천"으로 반환됨. 30~60%는 "검토필요", 하위 40%는 "비추천".

---

### Story 2.3: 시뮬레이션 결과 화면 표시

As a 관리자,
I want 시뮬레이션 실행 후 예상 수익 수치와 종합 판정을 화면에서 확인하고 싶다,
So that 해당 부동산의 수익성을 즉시 파악하고 제안서 출력으로 이어갈 수 있다.

**Acceptance Criteria:**

**Given** 시뮬레이션 API 응답 수신
**When** 결과 화면 렌더링
**Then** SimulationResultCard에 예상 월매출, 점유율, 순수익이 수치로 표시되고 카드가 슬라이드인 애니메이션으로 등장함

**Given** verdict가 "추천"
**When** VerdictBadge 렌더링
**Then** 초록색(#16A34A) 배지에 "✅ 추천 — 상위 N%" 텍스트 표시됨

**Given** fallback_used가 true
**When** 결과 화면 렌더링
**Then** amber 경고 배너 "유사 지점 데이터 부족 — 전체 평균으로 대체합니다"가 비침습적으로 표시됨

**Given** 결과 표시 완료
**When** 하단 버튼 영역 렌더링
**Then** "제안서 출력" Primary 버튼이 활성 상태로 표시됨

---

## Epic 3: 지도 시각화 & 제안서 PDF 출력

관리자가 지도에서 결과를 시각적으로 확인하고 PDF 제안서를 다운로드한다.

### Story 3.1: 카카오맵 지도 시각화

As a 관리자,
I want 시뮬레이션 결과 화면에서 분석 대상 위치와 인근 기존 지점들을 지도에서 확인하고 싶다,
So that 입지의 상권 맥락을 직관적으로 파악할 수 있다.

**Acceptance Criteria:**

**Given** 시뮬레이션 실행 후 결과 수신
**When** KakaoMapView 렌더링
**Then** 카카오맵에 분석 대상 위치(★ 파란 핀)가 표시되고 0.3s 페이드인 애니메이션으로 등장함

**Given** 인근 가상 지점 데이터 수신
**When** 지도 핀 렌더링
**Then** 인근 가상 지점들이 ● 회색 핀으로 표시됨

**Given** 주소 입력 완료 후 시뮬레이션 실행
**When** 지오코딩 API 호출
**Then** 서버사이드(FastAPI KakaoMapProvider)에서 주소→좌표 변환됨. KAKAO_REST_API_KEY가 클라이언트에 노출되지 않음.

**Given** 지도 영역 렌더링
**When** 스크린리더 접근
**Then** 지도에 `aria-label="카카오맵 — 분석 위치 및 인근 지점 표시"` 속성이 적용됨 (UX-DR16)

**Given** Kakao API 호출 실패(네트워크 오류)
**When** 지오코딩 시도
**Then** 지도 없이 텍스트 주소만 표시하는 fallback UI가 렌더링됨

---

### Story 3.2: 제안서 팝업 & 비교 차트

As a 관리자,
I want "제안서 출력" 버튼 클릭 시 도표와 차트가 포함된 1페이지 제안서 팝업을 확인하고 싶다,
So that 시연 자리에서 바로 보고서 품질의 제안서를 보여줄 수 있다.

**Acceptance Criteria:**

**Given** 결과 화면에서 "제안서 출력" 클릭
**When** ProposalModal 렌더링
**Then** 2초 이내에 680px 너비(A4 비율) 팝업이 열림. 브랜드 로고, 물건 정보, 수치 도표, 비교 차트, 판정 배지, 출력 날짜가 모두 표시됨.

**Given** 유사 지점 대비 분석 대상의 월매출 데이터
**When** ComparisonBarChart 렌더링
**Then** Recharts 막대그래프에서 분석 대상 바가 #2563EB 파란색으로 강조되고 나머지는 #BFDBFE로 표시됨

**Given** ProposalModal이 열린 상태
**When** X 버튼 클릭
**Then** 팝업이 닫힘. ESC 키 또는 배경 클릭으로는 닫히지 않음 (의도적 UX).

**Given** 팝업 내 수치 도표
**When** 렌더링
**Then** 예상 월매출, 점유율, 순수익이 각각 강조된 카드 형태로 표시됨

---

### Story 3.3: PDF 다운로드

As a 관리자,
I want 제안서 팝업에서 "PDF 저장" 버튼을 클릭하여 제안서를 PDF 파일로 다운로드하고 싶다,
So that 이 파일을 제안 자료로 즉시 활용할 수 있다.

**Acceptance Criteria:**

**Given** ProposalModal이 열린 상태
**When** "PDF 저장" 버튼 클릭
**Then** 파일명 `수익분석제안서_{주소}_{날짜}.pdf` 형식으로 PDF 다운로드됨

**Given** PDF 생성 중
**When** html2canvas + jsPDF 실행
**Then** ProposalDocument(순수 CSS/SVG 차트) 영역이 캡처되어 A4 비율 PDF로 출력됨. Recharts SVG를 직접 캡처하지 않음.

**Given** 생성된 PDF 파일
**When** PDF 뷰어에서 열람
**Then** 브랜드 로고, 물건 정보, 수치 도표, 비교 차트, 판정 배지, 날짜가 레이아웃 깨짐 없이 표시됨

**Given** Pretendard 폰트 사용
**When** PDF 캡처
**Then** 한글 텍스트가 깨지지 않고 정상 렌더링됨

---

## Epic 4: 수익분석표 게시판 & 데이터 관리

관리자가 10년치 가상 지점 데이터를 조회·정렬·필터하고 재생성/삭제한다.

### Story 4.1: 수익분석표 게시판 & 정렬/필터

As a 관리자,
I want 전체 지점의 10년치 수익 실적을 테이블에서 조회하고 정렬·필터하고 싶다,
So that 원하는 지점이나 기간의 데이터를 빠르게 찾을 수 있다.

**Acceptance Criteria:**

**Given** `/dashboard/board` 접근
**When** BranchDataTable 렌더링
**Then** 지점명, 주소, 기준연월, 월 매출, 전기세, 운영비, 순수익, 점유율 컬럼이 표시되고 기준연월 내림차순으로 기본 정렬됨. 페이지당 50건.

**Given** 컬럼 헤더 클릭
**When** 정렬 토글
**Then** 오름/내림차순이 전환되고 URL 쿼리 파라미터(`?sort_by=sale_date&order=desc`)에 반영됨

**Given** 연도 필터 셀렉트에서 "2025" 선택
**When** 필터 적용
**Then** 2025년 데이터만 표시됨. URL에 `?year=2025` 파라미터 반영.

**Given** 지점명 검색창에 "강남" 입력
**When** 검색 실행
**Then** "강남"이 포함된 지점명의 행만 표시됨

**Given** 페이지네이션 버튼 클릭
**When** 페이지 이동
**Then** 서버사이드에서 해당 페이지 데이터만 조회됨 (전체 데이터 클라이언트 로드 없음)

---

### Story 4.2: 가상 데이터 전체 재생성

As a 관리자,
I want "전체 재생성" 버튼으로 수도권 가상 지점의 10년치 데이터를 새로 생성하고 싶다,
So that 시연 전 신선한 데이터로 테스트 환경을 초기화할 수 있다.

**Acceptance Criteria:**

**Given** "전체 재생성" 버튼 클릭
**When** 확인 다이얼로그 표시
**Then** "정말 전체 데이터를 재생성하시겠습니까?" 메시지와 확인/취소 버튼이 표시됨. 취소 시 아무 동작 없음.

**Given** 확인 다이얼로그에서 "확인" 클릭
**When** `POST /data/generate` 호출
**Then** HTTP 202 즉시 응답. 백그라운드에서 asyncpg COPY 프로토콜로 배치 생성 시작.

**Given** 배치 생성 완료 (60초 이내)
**When** 백그라운드 태스크 완료
**Then** 우측 하단에 초록색 Toast "데이터 재생성이 완료되었습니다" 3초간 표시됨

**Given** 220개 가상 지점 × 10년치 일별 매출 데이터
**When** asyncpg.copy_records_to_table() 실행
**Then** 총 레코드 생성 시 메모리 피크가 400MB 미만 유지됨 (지점별 청크 처리)

**Given** "전체 재생성" 중복 클릭
**When** 이미 생성 중인 상태
**Then** 버튼이 비활성화되어 중복 요청 방지됨

---

### Story 4.3: 가상 데이터 전체 삭제 & 빈 상태 UI

As a 관리자,
I want "전체 삭제" 버튼으로 전체 가상 데이터를 삭제하고 싶다,
So that 테스트 환경을 초기화하거나 재생성 전 데이터를 정리할 수 있다.

**Acceptance Criteria:**

**Given** "전체 삭제" 버튼 클릭
**When** AlertDialog 표시
**Then** "이 작업은 되돌릴 수 없습니다. 정말 삭제하시겠습니까?" 경고와 확인/취소 버튼 표시됨. ESC나 배경 클릭으로 닫히지 않음.

**Given** AlertDialog에서 "확인" 클릭
**When** `DELETE /data/all` 호출
**Then** 전체 sales, operations, members 데이터가 삭제됨. 완료 후 Toast "전체 데이터가 삭제되었습니다" 표시.

**Given** 데이터 삭제 완료 후 게시판 접근
**When** BranchDataTable 렌더링
**Then** "데이터가 없습니다. 전체 재생성 버튼을 눌러주세요." 빈 상태 메시지와 "전체 재생성" 바로가기 버튼이 표시됨 (UX-DR15)

**Given** 멱등성 확인 — 빈 상태에서 DELETE 재실행
**When** `DELETE /data/all` 재호출
**Then** 오류 없이 성공 응답 반환됨 (ON CONFLICT / 빈 삭제 허용)
