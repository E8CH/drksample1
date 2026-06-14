## Deferred from: code review of 4-3-가상-데이터-전체-삭제-빈-상태-ui (2026-06-14)

- D1: `isDeleting=true` unmount leak — `handleConfirmDelete` awaits Server Action; if user navigates away mid-flight, `setIsDeleting(false)` + `router.refresh()` still fire on stale ref. React 18 suppresses the state-update warning; `router.refresh()` on stale ref causes spurious reload on next page. Admin-only tool, single user — low real impact [`nextjs-frontend/components/board/TableToolbar.tsx:92-103`]
- D2: `asyncpg` errors unhandled in `delete_all_data` — DB failure raises untyped exception → FastAPI returns generic 500. Admin sees "삭제 요청에 실패했습니다" with no distinction between DB-down vs partial failure. Transactional so DB is clean on failure; idempotent retry safe [`fastapi_backend/app/services/data_generator.py:164-177`]
- D3: `DELETE /data/all` returns HTTP 200 + body vs REST convention 204 No Content — frontend checks `res.ok`, so semantically equivalent. Clean-up in future API consistency pass [`fastapi_backend/app/routes/data.py:44-48`]
- D4: Double-polling structural issue — `TableToolbar` (`isGenerating`) and `BranchDataTable` (`isEmptyGenerating`) each own independent polling loops with no shared state. Low-probability race: both active simultaneously → double toast + double `router.refresh()`. Fix: lift generation state to shared context or parent prop [`nextjs-frontend/components/board/`]
- D5: AC1 confirm button label is "삭제" (implementation) vs spec wording "확인/취소 버튼" — "삭제" is better UX for a destructive-action dialog. Not a functional gap [`nextjs-frontend/components/board/TableToolbar.tsx:217`]
- D6: `deleteAllData()` Server Action no timeout — slow DB (large table) causes button stuck in "삭제 중..." indefinitely. `AbortSignal.timeout(30_000)` + frontend error handling would improve UX. Admin tool, transactional safe [`nextjs-frontend/actions/data.ts:43-47`]

## Deferred from: code review of 4-2-가상-데이터-전체-재생성 (2026-06-14)

- D1: `checkGenerationStatus` returns `"idle"` on backend crash — triggers false-success toast without distinguishing completion from failure [`nextjs-frontend/actions/data.ts:33-35`] — POC 단일 인스턴스 허용
- D2: Year dropdown shows 2026 (currentYear) with no data — `sales_2026` partition 없음, pre-existing from Story 4-1 [`nextjs-frontend/components/board/TableToolbar.tsx:22-25`]
- D3: `asyncio.sleep(0)` yields between branches but `_generate_*` runs synchronously — event loop starvation risk [`fastapi_backend/app/services/data_generator.py:155`] — POC acceptable
- D4: AC5 UI-only protection — second browser tab sees active button; backend 409 prevents actual duplicate runs [`nextjs-frontend/components/board/TableToolbar.tsx:133`] — POC single-admin
- D5: No timeout guard on `generate_all_data` — FR-8 (30s) / AC3 (60s) are guidelines, not enforced [`fastapi_backend/app/services/data_generator.py`]
- D6: Test cleanup race in `test_generate_authenticated` — background task may still run after `_STATUS` reset [`fastapi_backend/tests/test_data.py:37`] — CI DB 필요 패턴과 동일
- D7: AC3 toast lost if user navigates away from board page during polling [`nextjs-frontend/components/board/TableToolbar.tsx:39-52`] — POC limitation

## Deferred from: code review of 4-1-수익분석표-게시판-정렬-필터 (2026-06-12)

- D1: f-string SQL ORDER BY 구성 — sort_col/order_dir는 Literal 타입 검증 통과 값이므로 현재는 안전; 향후 allowlist 변경 시 injection 위험, text()+bindparams 패턴으로 교체 권장 [fastapi_backend/app/routes/sales.py]
- D2: formatMonth 입력 가드 없음 — TO_CHAR('YYYY-MM') 포맷이 안정적이므로 실제 발생 가능성 낮음; 방어적 코딩으로 null 체크 추가 권장 [nextjs-frontend/components/board/BranchDataTable.tsx:26]
- D3: occupancy_rate 레이블 — revenue/avg×100로 계산되는 상대 지표, 진짜 점유율(가동률)이 아님; 스펙 의도적 설계, 운영 전 레이블 명확화 검토 필요
- D4: Cookie 헤더 HTTP 전달 — API_URL이 HTTPS 아닐 경우 토큰 평문 전달; 기존 패턴(simulation.ts)과 동일, 운영 배포 시 HTTPS 강제 필요
- D5: buildParams 중복 정의 — BranchDataTable(page 유지)과 TableToolbar(page=1 초기화) 간 의도적 행동 차이 있음; 공유 유틸 추출 가능하나 현재 기능에 영향 없음
- D6: ILIKE % _ 와일드카드 — 사용자 입력의 % / _가 SQL LIKE 특수문자로 처리됨; 지점명 검색에서 자연어 와일드카드 허용으로 보안 이슈 없음, 운영 전 escape 옵션 검토 가능 (Story 2-2 F4와 동일)
- D7: API_URL 환경변수 null 체크 — undefined 시 "undefined/sales" URL 생성; 기존 서버 컴포넌트 패턴과 동일, 인프라 레벨 필수값 보장 필요
- D8: fetchSales 에러 경계 없음 — Next.js error.tsx로 상위 에러 처리 가능; 별도 에러 UX 스토리에서 처리

## Deferred from: code review of 3-3-pdf-다운로드 (2026-06-13)

- D1: today() 함수 중복 정의 (ProposalModal.tsx, ProposalDocument.tsx) — 리팩토링으로 공유 유틸 이동 권장; 기능 영향 없음
- D2: 이모지 "🏠" html2canvas 렌더링 위험 — 플랫폼/브라우저 따라 emoji 렌더링 불안정 가능; 스펙 의도적 포함이므로 운영 모니터링 권장

## Deferred from: code review of 3-2-제안서-팝업-비교-차트 (2026-06-12)

- D1: setMapLoading(false) 취소 경로 미호출 [SimulationContainer.tsx] — pre-existing Story 3-1, 쾌속 재제출 시 무한 스피너 가능
- D2: 12자 트런케이션 이름 충돌 [rule_based.py:252] — 동일 12자 접두사 지점 구분 불가; 저영향 edge case
- D3: _empty_db() 다중 쿼리 한계 [test_engines.py:14] — 단일 mock 반환값, 다중 DB 쿼리 패턴 변경 시 테스트 무력화 가능
- D4: fallback 경로 comparison_data=[] 빈 리스트 assertion 부재 [test_simulation.py:124] — 회귀 검출 blind spot

## Deferred from: code review of 2-2-수익-시뮬레이션-연산-api (2026-06-12)

- F2: `secure=False` 쿠키 — Railway 배포 시 `secure=True` 필요 (Story 1-4 F7과 동일)
- F4/E9: LIKE 와일드카드 미이스케이프 (`_`, `%`) — `\w+구/시` 정규식으로 특수문자 유입 위험 낮음; 운영 전 `escape="\\"` 추가 권장
- F7: `net_profit` 음수 허용 — 논리적으로 유효한 값(손실 상황); 프론트엔드 표시 시 "손실" 레이블 처리 필요
- F9: Server Action → FastAPI 서버간 JWT Cookie 헤더 전달 — 내부 네트워크 TLS 확인 필요; `API_URL` 반드시 HTTPS 사용
- E5: `area_sqm` 최소값 미지정 (`gt=0` 허용) — 1.0 미만 면적은 계산 의미 없음; 운영 전 `ge=1.0` 추가 권장
- E10: 백분위 계산 시 예측 지점 자신이 비교 풀에 포함 — 미미한 통계적 편향; 데이터 충분시 미미한 영향

## Deferred from: code review of 2-1-입지-조건-입력-폼 (2026-06-12)

- ~~Server Action `runSimulation` 인증 가드 없음~~ — Story 2-2에서 `cookies()` + Cookie 헤더 전달로 해소
- `z.coerce.number()` + NaN → `invalid_type_error` 메시지 Zod 버전 의존 — Zod 3.22+ 확인 필요, 필요 시 `.refine(!isNaN)` 추가
- buildingUse Select deselect 옵션 없음 — 선택 후 "미선택"으로 되돌리기 불가; UX 개선 여지
- EV충전 checkbox(시각적) vs toggle-switch(UX 스펙) — 기능은 동일, 시각적 개선은 shadcn Switch 설치 후 교체 가능
- `ValidatorFn` 수동 타입 — `z.SafeParseReturnType<unknown>` 사용으로 교체 권장 (Zod v4 대비)

## Deferred from: code review of 1-5-기본-레이아웃-다락-브랜드-적용 (2026-06-12)

- D1: CDN 폰트(Pretendard) SRI/CSP 없음 — jsdelivr subresource integrity 미적용; 운영 전 self-host 또는 `<link integrity="...">` 적용 필요
- D2: `--border` (shadcn) vs `dalock.border` (#E2E8F0) 색상 불일치 — shadcn 기반 컴포넌트에서 미세한 브랜드 색상 차이
- D3: CDN 폰트 preconnect/font-display 없음 — FOUT 위험; 운영 전 `<link rel="preconnect">` + `font-display=swap` 추가
- D4: Primary 버튼 UI 요소 부재(AC2 partial) — Story 2에서 실제 CTA 버튼 추가 시 자동 충족
- D5: `dvh` 완전 지원 — `min-h-[calc(100dvh-56px)]` 사용으로 모바일 브라우저 chrome 처리 개선 필요; Story 2에서 실제 레이아웃 구현 시 처리
- D6: CSP/보안 헤더 없음 — `next.config.mjs`의 `headers()`에 Content-Security-Policy 추가; 별도 보안 스토리에서 처리
- D7: `middleware.ts` — `SECRET_KEY` undefined 시 literal "undefined" 인코딩됨; 명시적 throw 가드 추가 필요

## Deferred from: code review of 1-4-jwt-인증-로그인-페이지 (2026-06-12)

- F7: `secure=False` 하드코딩 [auth.py] — POC 단계; Railway 배포 시 `secure=True`로 변경 필요
- F9: dashboard layout.tsx `onClick={logout}` 패턴 — pre-existing; Story 1-5 레이아웃 재작성 시 개선
- F10: 테스트가 실제 credentials 사용 — `.env` placeholder 값 사용으로 CI 안전, 개선 여지 있음
- F11: 로그인 rate limiting 없음 — POC 단계; 운영 전 추가 필요
- F12: timing-safe 비교 미사용 (== 연산자) — POC 단계; 운영 전 `hmac.compare_digest` 적용 필요
- F13: `NEXT_PUBLIC_API_URL` → `API_URL` rename 포함됨 (패치로 처리); 추가 노출 방지 확인 필요

## Deferred from: code review of 1-2-데이터베이스-스키마-alembic-마이그레이션 (2026-06-13)

- 2026년 이후 sales 파티션 없음 — 향후 스토리에서 default partition 또는 연장 처리 필요
- database.py URL 재구성 시 쿼리 파라미터 손실 (`?ssl=require` 등) — 기존 코드 이슈, 별도 수정 필요
- urlparse 특수문자 비밀번호 디코딩 후 미인코딩 삽입 — 기존 코드 이슈
- Branch.branch_name / Member.email 가변 텍스트 PK — FK ON UPDATE CASCADE 없음, 아키텍처 결정 필요
- Operation (branch_name, month) 유니크 제약 없음 — 데이터 정합성 위험
- Numeric 컬럼 precision/scale 미지정 (area_sqm, monthly_rent, daily_revenue 등)
- daily_revenue CHECK >= 0 없음 — 음수 매출 허용
- email 대소문자 구분 PK — lower(email) 정규화 필요
- BRIN 인덱스 향후 파티션 자동 상속 안 됨 — 신규 파티션 추가 시 수동 인덱스 생성 필요
- conftest create_all이 파티션 없는 sales 테이블 생성 — 향후 테스트 격리 개선 필요
- SIMULATION_ENGINE Literal["rule_based", "ml"] 타입 지정 필요
- Operation.month 월 첫째날 CHECK(EXTRACT(DAY FROM month)=1) 없음

## Deferred from: code review of 1-3-simulationengine-mapprovider-추상화-구현 (2026-06-12)

- raise_for_status() httpx.HTTPStatusError 미처리 — 라우터 에러 핸들링은 Story 2.2/3.1 범위
- resp.json() JSONDecodeError 미처리 — 동일 범위
- docs[0]["x"/"y"] 키 미존재 시 KeyError — Kakao API 응답 파싱 완전 구현은 Story 3.1
- verdict: str → Literal 타입 — Story 1-2에서 이미 defer됨, Story 2.2에서 처리
- SIMULATION_ENGINE Literal 타입 미지정 — Story 1-2 defer 항목, Story 2.2에서 처리
- AsyncClient 호출마다 생성(연결 풀링 없음) — Story 3.1에서 최적화
- _provider 모듈 레벨 싱글톤 lazy init — Story 3.1에서 재검토
- schemas/__init__.py map/simulation 미재export — 미래 개선
- Coordinates lat/lon 범위 검증 — Story 3.1 범위
- area_sqm/monthly_rent 음수 허용 — Story 2.1 범위
- percentile 0-100 범위 검증 — Story 2.2 범위
- MLEngine 매 호출마다 RuleBasedEngine 생성 — stub 설계, v2에서 교체
- AC5 BranchPin 빈 리스트 vacuous 검증 — Story 3.1에서 실질 검증
- AC2 위임 경로 미검증(결과값만 확인) — Story 2.2 실 구현 시 검증
- issubclass ABC 계약 테스트 없음 — low value
- NFR-2 API 키 응답 누출 방지 테스트 없음 — speculative

## Deferred from: code review of 1-1-프로젝트-초기화-railway-배포-환경-구성 (2026-06-12)

- `fastapi_backend/.env.example:13` 타이포 `genrated` → `generated` — Vinta 템플릿 기존 이슈, 기능에 영향 없음
