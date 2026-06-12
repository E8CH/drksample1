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
