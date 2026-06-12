# Story 2.2: 수익 시뮬레이션 연산 API

Status: review

## Story

As a 시스템,
I want 입력된 입지 조건으로 유사 지점을 추출하고 수익 지표를 계산하고 싶다,
So that 관리자에게 예상 월매출, 점유율, 순수익, 종합 판정을 반환할 수 있다.

## Acceptance Criteria

1. **Given** 유효한 입지 조건 JSON payload **When** `POST /simulation/run` 호출 **Then** 3초 이내에 SimulationResult(estimated_monthly_revenue, occupancy_rate, net_profit, percentile, verdict) 반환됨

2. **Given** 면적±30%, 임대료±30%, 같은 구 기준 유사 지점 5개 이상 존재 **When** RuleBasedEngine.predict() 실행 **Then** 유사 지점군의 가중 평균(area 0.45/rent 0.30/region 0.25)으로 결과 계산됨

3. **Given** 1차 기준(±30%, 구) 유사 지점 5개 미만 **When** RuleBasedEngine.predict() 실행 **Then** 2차 기준(±50%, 시)으로 재검색. 여전히 부족하면 전체 평균 사용. 응답에 `fallback_used: true` 포함.

4. **Given** EV 충전 가능한 물건 **When** 시뮬레이션 계산 **Then** 예상 월매출에 1.08 보정 계수 적용됨

5. **Given** 전체 지점 중 순수익 상위 30% 물건 **When** 종합 판정 계산 **Then** verdict가 "추천"으로 반환됨. 30~60%는 "검토필요", 하위 40%는 "비추천".

## Tasks / Subtasks

- [x] Task 1: SimulationResult.verdict Literal 타입 추가 (AC: #5, deferred from 1-3)
  - [x] `fastapi_backend/app/schemas/simulation.py`에서 `verdict: str` → `verdict: Literal["추천", "검토필요", "비추천"]` 변경
  - [x] `Literal` import 추가

- [x] Task 2: SimulationEngine ABC에 db 파라미터 추가 (AC: #2)
  - [x] `fastapi_backend/app/engines/base.py`에서 `predict(self, location, db: AsyncSession)` 시그니처로 변경
  - [x] `fastapi_backend/app/engines/ml_engine.py` 동일 시그니처로 업데이트

- [x] Task 3: RuleBasedEngine.predict() 전체 구현 (AC: #2, #3, #4, #5)
  - [x] `extract_gu()`, `extract_si()` 주소 파싱 헬퍼 구현
  - [x] Tier 1 (±30%, 구), Tier 2 (±50%, 시), Tier 3 (전체) 3단계 fallback 쿼리
  - [x] 유사 지점별 가중치 계산 (area 0.45 / rent 0.30 / region 0.25, 정규화)
  - [x] 가중 평균으로 estimated_monthly_revenue, occupancy_rate, net_profit 계산
  - [x] EV 보정(×1.08) 적용
  - [x] 전체 지점 순수익 목록으로 백분위 → verdict 계산

- [x] Task 4: POST /simulation/run 라우터 생성 (AC: #1)
  - [x] `fastapi_backend/app/routes/simulation.py` 신규 생성
  - [x] JWT 쿠키(`access_token`) 검증 dependency(`require_admin`) 구현
  - [x] `POST /simulation/run` — LocationConditions 입력, SimulationResult 반환
  - [x] 3초 이내 응답 보장 (DB 쿼리 비동기)

- [x] Task 5: main.py에 simulation 라우터 등록 (AC: #1)
  - [x] `fastapi_backend/app/main.py`에 `simulation_router` import 및 등록 (`/simulation` prefix)

- [x] Task 6: simulation-action.ts 실제 API 연결 + 인증 가드 (defer 해결)
  - [x] `cookies()` from `next/headers`로 `access_token` 쿠키 읽기
  - [x] 토큰 없으면 `{ error: "인증이 필요합니다" }` 반환 (SSRF 방지)
  - [x] `API_URL` 환경변수 사용하여 FastAPI 엔드포인트 호출
  - [x] 반환 타입: `{ error?: string; result?: SimulationResultData }` — Story 2-3 확장 대비
  - [x] `SimulationResultData` 타입 `nextjs-frontend/lib/definitions.ts`에 export

- [x] Task 7: 테스트 (AC: all)
  - [x] `fastapi_backend/tests/routes/test_simulation.py` 신규 생성
  - [x] 헬퍼 함수 단위 테스트: `extract_gu`, `extract_si`, `_calc_verdict`
  - [x] `POST /simulation/run` 인증 없음 → 401
  - [x] `POST /simulation/run` 유효 payload + 인증 쿠키 → 200 (DB 없음 fallback 경로)

- [x] Task 8: TypeScript 타입 체크 (AC: all)
  - [x] `cd nextjs-frontend && npx tsc --noEmit` — 오류 없음 확인

## Dev Notes

### 알고리즘: FR-2 가중 유사도 기반 수익 예측

```python
# 1. 주소에서 구/시 추출 (정규식)
gu = extract_gu(address)   # e.g. "강남구"
si = extract_si(address)   # e.g. "서울"

# 2. 3단계 fallback으로 유사 지점 추출
branches = query(area±30%, rent±30%, gu_match)   # Tier 1
if len(branches) < 5:
    branches = query(area±50%, rent±50%, si_match)  # Tier 2, fallback_used=True
if len(branches) < 5:
    branches = query_all()                           # Tier 3

# 3. 가중치 계산 (지점별)
for b in branches:
    area_sim = 1 - abs(b.area_sqm - input.area_sqm) / max(input.area_sqm, 1)
    rent_sim = 1 - abs(b.monthly_rent - input.monthly_rent) / max(input.monthly_rent, 1)
    region_sim = 1.0 if gu and gu in b.address else 0.0
    weight = 0.45 * area_sim + 0.30 * rent_sim + 0.25 * region_sim

# 4. 가중 평균
total_w = sum(weights)
est_revenue = sum(b.avg_monthly_revenue * w for b, w in pairs) / total_w

# 5. EV 보정
if input.ev_charging:
    est_revenue *= 1.08

# 6. 점유율 = 추정 월매출 / (area_sqm * 10000) * 100, 0~99 클램프
occupancy_rate = min(99.0, max(0.0, est_revenue / max(area_sqm * 10_000, 1) * 100))

# 7. 순수익
net_profit = est_revenue - input.monthly_rent - (input.monthly_maintenance or 0) - weighted_avg_ops_cost

# 8. 백분위 (전체 지점 avg_monthly_revenue 기준)
# percentile = (지점 중 est_revenue 이하 수) / 전체 * 100
# 상위 30% (percentile>=70) → 추천
# 30~60% (40<=p<70)       → 검토필요
# 하위 40% (percentile<40) → 비추천
```

### auth dependency: require_admin

```python
from fastapi import Cookie, HTTPException, Depends
import jwt

async def require_admin(access_token: str | None = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
```

### simulation-action.ts — 인증 패턴

```ts
"use server";
import { cookies } from "next/headers";
const token = (await cookies()).get("access_token")?.value;
if (!token) return { error: "인증이 필요합니다" };

await fetch(`${API_URL}/simulation/run`, {
  method: "POST",
  headers: { "Content-Type": "application/json", Cookie: `access_token=${token}` },
  body: JSON.stringify(mapped_input),
});
```

### SimulationResultData 타입 (Story 2-3 사용)

```ts
export type SimulationResultData = {
  estimated_monthly_revenue: number;
  occupancy_rate: number;
  net_profit: number;
  percentile: number;
  verdict: "추천" | "검토필요" | "비추천";
  similar_branch_count: number;
  fallback_used: boolean;
};
```

### DB 없음 / 데이터 없음 fallback

Story 4.2 이전에는 branches 테이블이 비어 있어 Tier 3에서도 0개 → `_default_estimate()` 경로:
- estimated_monthly_revenue = monthly_rent * 2
- occupancy_rate = 65.0
- net_profit = monthly_rent * 1.0
- percentile = 50.0
- verdict = "검토필요"
- fallback_used = True

### 기존 파일 수정 대상

| 파일 | 변경 유형 |
|------|----------|
| `fastapi_backend/app/schemas/simulation.py` | 수정 — verdict Literal 추가 |
| `fastapi_backend/app/engines/base.py` | 수정 — db 파라미터 추가 |
| `fastapi_backend/app/engines/ml_engine.py` | 수정 — 시그니처 동기화 |
| `fastapi_backend/app/engines/rule_based.py` | 수정 — 전체 구현 |
| `fastapi_backend/app/main.py` | 수정 — simulation 라우터 등록 |
| `nextjs-frontend/lib/definitions.ts` | 수정 — SimulationResultData 타입 추가 |
| `nextjs-frontend/components/actions/simulation-action.ts` | 수정 — 실제 API 연결 |

| 파일 | 변경 유형 |
|------|----------|
| `fastapi_backend/app/routes/simulation.py` | 신규 |
| `fastapi_backend/tests/routes/test_simulation.py` | 신규 |

## Dev Agent Record

### Implementation Plan

1. schemas/simulation.py — verdict Literal 추가
2. engines/base.py — db: AsyncSession 파라미터 추가
3. engines/ml_engine.py — 시그니처 동기화
4. engines/rule_based.py — 전체 알고리즘 구현
5. routes/simulation.py — POST /simulation/run + require_admin
6. main.py — simulation_router 등록
7. lib/definitions.ts + simulation-action.ts — 프론트엔드 연결
8. tests/routes/test_simulation.py — 단위+통합 테스트
9. tsc --noEmit

### Debug Log

- `_empty_db_session()` Mock: `execute().scalars().all()` 체인 vs `execute().all()` 두 경로 모두 empty list 반환하도록 설정
- `LocationConditions` 필드 검증 없어서 area_sqm=-1, monthly_rent=0 통과 → `Field(gt=0)` 추가로 422 확보
- `_calc_verdict` boundary: percentile=70.0 → 추천 (>=70), percentile=40.0 → 검토필요 (>=40), 39.9 → 비추천

### Completion Notes

- AC1: POST /simulation/run 응답 < 3초 (DB 없음 경로 0.05s)
- AC2: 가중 평균(0.45/0.30/0.25) 구현, `_weighted_average()` 정규화
- AC3: 3단계 fallback (Tier1 ±30%구 → Tier2 ±50%시 → Tier3 전체 → default), fallback_used=True
- AC4: EV×1.08 보정 — test_ev_charging_increases_revenue 통과 확인
- AC5: percentile ≥70 → 추천, 40~70 → 검토필요, <40 → 비추천
- 추가: LocationConditions에 Field 범위 검증 추가 (Story 1-3 defer 해소)
- 12/12 pytest 통과, tsc --noEmit 오류 없음

## File List

**신규 생성:**
- `fastapi_backend/app/routes/simulation.py`
- `fastapi_backend/tests/routes/test_simulation.py`

**수정:**
- `fastapi_backend/app/schemas/simulation.py`
- `fastapi_backend/app/engines/base.py`
- `fastapi_backend/app/engines/ml_engine.py`
- `fastapi_backend/app/engines/rule_based.py`
- `fastapi_backend/app/main.py`
- `nextjs-frontend/lib/definitions.ts`
- `nextjs-frontend/components/actions/simulation-action.ts`

## Change Log

- 2026-06-12: Story 2-2 CS 생성. POST /simulation/run, FR-2 가중 유사도 알고리즘, EV 보정, 3단계 fallback, verdict 판정 스코프 정의.
- 2026-06-12: Story 2-2 DS 구현 완료. Literal verdict, DB 파라미터 ABC 업데이트, RuleBasedEngine 전체 구현, simulation 라우터, 프론트엔드 API 연결. 12/12 pytest 통과, tsc 오류 없음.
