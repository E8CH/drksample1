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
