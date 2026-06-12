# Story 1.3: SimulationEngine & MapProvider 추상화 구현

Status: done

## Story

As a 개발자,
I want SimulationEngine ABC와 MapProvider ABC를 구현하고 Kakao API 키 연결을 검증하고 싶다,
so that 시뮬레이션과 지도 기능이 나중에 다른 엔진/프로바이더로 교체 가능한 구조로 동작한다.

## Acceptance Criteria

1. `SIMULATION_ENGINE=rule_based` 설정 시 `get_engine()` 호출이 RuleBasedEngine 인스턴스를 반환함
2. `SIMULATION_ENGINE=ml` 설정 시 `get_engine()` 호출이 MLEngine 인스턴스를 반환하고, `MLEngine.predict()` 호출 시 RuleBasedEngine에 위임됨 (stub 동작)
3. 유효한 KAKAO_REST_API_KEY 환경 변수 설정 시 `KakaoMapProvider.geocode("서울 강남구 역삼동 123")` 호출이 위경도 Coordinates 객체를 반환함
4. KAKAO_REST_API_KEY 미설정 시 FastAPI 서버 기동이 환경 변수 누락 오류로 차단됨 (시작 블록)
5. `schemas/map.py`에 Coordinates, BranchPin 타입 정의가 존재하고, `MapProvider.get_nearby_branches()` 호출이 BranchPin 리스트를 반환함 (계약 준수)

## Tasks / Subtasks

- [x] Task 1: app/schemas/ 디렉토리 구조로 마이그레이션 (사전조건)
  - [x] `app/schemas/__init__.py` 생성 — 기존 `schemas.py`의 UserRead, UserCreate, UserUpdate, ItemBase, ItemCreate, ItemRead 전부 re-export
  - [x] `app/schemas.py` 삭제 (schemas/ 디렉토리와 공존 불가)
  - [x] `app/main.py` import 경로 확인 (`from .schemas import UserRead, UserCreate, UserUpdate` — __init__.py re-export로 변경 불필요)

- [x] Task 2: app/schemas/map.py 생성 (AC: #3, #5)
  - [x] `Coordinates` Pydantic 모델 — latitude: float, longitude: float
  - [x] `BranchPin` Pydantic 모델 — branch_name: str, address: str, latitude: float, longitude: float

- [x] Task 3: app/schemas/simulation.py 생성 (엔진 인터페이스 타입 계약 — AC: #1, #2)
  - [x] `LocationConditions` Pydantic 모델 — address: str, area_sqm: float, monthly_rent: float, monthly_maintenance: Optional[float]=None, building_usage: Optional[str]=None, ev_charging: bool=False, parking_count: int=0
  - [x] `SimulationResult` Pydantic 모델 — estimated_monthly_revenue: float, occupancy_rate: float, net_profit: float, percentile: float, verdict: str, similar_branch_count: int, fallback_used: bool=False

- [x] Task 4: app/engines/ 패키지 생성 (AC: #1, #2)
  - [x] `app/engines/__init__.py` — SimulationEngine, RuleBasedEngine, MLEngine re-export
  - [x] `app/engines/base.py` — SimulationEngine ABC (predict() abstractmethod)
  - [x] `app/engines/rule_based.py` — RuleBasedEngine stub (predict()는 zeroed-out SimulationResult 반환, Story 2.2에서 완전 구현)
  - [x] `app/engines/ml_engine.py` — MLEngine stub (predict()는 RuleBasedEngine().predict()에 위임)

- [x] Task 5: app/services/simulation_service.py 생성 (AC: #1, #2)
  - [x] `get_engine() -> SimulationEngine` 팩토리 함수 — `settings.SIMULATION_ENGINE == "ml"` → MLEngine(), 아니면 RuleBasedEngine()

- [x] Task 6: app/providers/ 패키지 생성 (AC: #3, #5)
  - [x] `app/providers/__init__.py` — MapProvider, KakaoMapProvider re-export
  - [x] `app/providers/base.py` — MapProvider ABC (geocode(), get_nearby_branches() abstractmethod)
  - [x] `app/providers/kakao.py` — KakaoMapProvider: geocode()는 httpx로 `https://dapi.kakao.com/v2/local/geo/address.json` 호출, `Authorization: KakaoAK {KAKAO_REST_API_KEY}` 헤더 사용; get_nearby_branches()는 빈 리스트 반환 (Story 3.1에서 구현)

- [x] Task 7: app/services/map_service.py 생성 (AC: #3, #5)
  - [x] `geocode(address: str) -> Coordinates` 함수 — KakaoMapProvider 위임
  - [x] `get_nearby_branches(coords: Coordinates, radius_km: float = 2.0) -> list[BranchPin]` 함수 — KakaoMapProvider 위임

- [x] Task 8: AC4 검증 테스트 (AC: #4)
  - [x] KAKAO_REST_API_KEY 미설정 시 pydantic-settings ValidationError 발생 테스트
  - [x] config.py의 `KAKAO_REST_API_KEY: str` 필수 필드 (기본값 없음) 이미 구현됨 — 테스트로 확인

- [x] Task 9: 엔진/프로바이더 테스트 작성 (AC: #1, #2, #3, #5)
  - [x] `tests/test_engines.py` 생성
    - [x] `test_get_engine_rule_based()` — SIMULATION_ENGINE=rule_based 시 RuleBasedEngine 반환 확인
    - [x] `test_get_engine_ml()` — SIMULATION_ENGINE=ml 시 MLEngine 반환 확인
    - [x] `test_ml_engine_delegates_to_rule_based()` — MLEngine.predict() 호출 시 RuleBasedEngine에 위임되어 SimulationResult 반환 확인
    - [x] `test_rule_based_engine_returns_simulation_result()` — RuleBasedEngine.predict() 호출 시 SimulationResult 반환 확인
  - [x] `tests/test_providers.py` 생성
    - [x] `test_kakao_geocode_returns_coordinates()` — httpx 응답 mock으로 Coordinates 반환 확인
    - [x] `test_kakao_geocode_no_results_raises()` — 빈 documents 응답 시 ValueError 발생 확인
    - [x] `test_map_provider_get_nearby_branches_returns_list()` — get_nearby_branches() 반환 타입 list[BranchPin] 확인
    - [x] `test_kakao_rest_api_key_required()` — KAKAO_REST_API_KEY 필수 필드 (is_required()) 확인

## Dev Notes

### ⚠️ CRITICAL: schemas.py → schemas/ 디렉토리 마이그레이션

현재 `app/schemas.py` (단일 파일)이 존재하고 `app/main.py`가 `from .schemas import UserRead, UserCreate, UserUpdate`로 임포트함.
아키텍처는 `app/schemas/` 디렉토리를 요구. **파일과 디렉토리 동명 공존 불가** — 반드시 `schemas.py` 삭제 후 `schemas/` 생성.

```python
# app/schemas/__init__.py — 기존 schemas.py 내용 전체 re-export
import uuid
from fastapi_users import schemas
from pydantic import BaseModel
from uuid import UUID

class UserRead(schemas.BaseUser[uuid.UUID]):
    pass

class UserCreate(schemas.BaseUserCreate):
    pass

class UserUpdate(schemas.BaseUserUpdate):
    pass

class ItemBase(BaseModel):
    name: str
    description: str | None = None
    quantity: int | None = None

class ItemCreate(ItemBase):
    pass

class ItemRead(ItemBase):
    id: UUID
    user_id: UUID
    model_config = {"from_attributes": True}
```

`app/main.py`의 `from .schemas import UserCreate, UserRead, UserUpdate` 임포트는 **변경 불필요** (`__init__.py` re-export로 호환).

### SimulationEngine ABC 구조

```python
# app/engines/base.py
from abc import ABC, abstractmethod
from app.schemas.simulation import LocationConditions, SimulationResult

class SimulationEngine(ABC):
    @abstractmethod
    async def predict(self, location: LocationConditions) -> SimulationResult: ...
```

```python
# app/engines/rule_based.py
from app.engines.base import SimulationEngine
from app.schemas.simulation import LocationConditions, SimulationResult

class RuleBasedEngine(SimulationEngine):
    async def predict(self, location: LocationConditions) -> SimulationResult:
        # Story 2.2에서 완전 구현 (FR-2: 유사 지점 추출 → 가중 평균 → EV/주차 보정 → 판정)
        return SimulationResult(
            estimated_monthly_revenue=0.0,
            occupancy_rate=0.0,
            net_profit=0.0,
            percentile=0.0,
            verdict="검토필요",
            similar_branch_count=0,
        )
```

```python
# app/engines/ml_engine.py
from app.engines.base import SimulationEngine
from app.engines.rule_based import RuleBasedEngine
from app.schemas.simulation import LocationConditions, SimulationResult

class MLEngine(SimulationEngine):
    async def predict(self, location: LocationConditions) -> SimulationResult:
        # TODO: scripts/train_model.py ML 모델 추론으로 교체 (v2)
        return await RuleBasedEngine().predict(location)
```

### get_engine() 팩토리

```python
# app/services/simulation_service.py
from app.config import settings
from app.engines.base import SimulationEngine
from app.engines.rule_based import RuleBasedEngine
from app.engines.ml_engine import MLEngine

def get_engine() -> SimulationEngine:
    if settings.SIMULATION_ENGINE == "ml":
        return MLEngine()
    return RuleBasedEngine()
```

### MapProvider ABC + KakaoMapProvider

```python
# app/providers/base.py
from abc import ABC, abstractmethod
from app.schemas.map import Coordinates, BranchPin

class MapProvider(ABC):
    @abstractmethod
    async def geocode(self, address: str) -> Coordinates: ...

    @abstractmethod
    async def get_nearby_branches(self, coords: Coordinates, radius_km: float) -> list[BranchPin]: ...
```

```python
# app/providers/kakao.py
import httpx
from app.config import settings
from app.providers.base import MapProvider
from app.schemas.map import Coordinates, BranchPin

class KakaoMapProvider(MapProvider):
    BASE_URL = "https://dapi.kakao.com/v2/local"

    async def geocode(self, address: str) -> Coordinates:
        headers = {"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/geo/address.json",
                params={"query": address},
                headers=headers,
            )
            resp.raise_for_status()
            docs = resp.json().get("documents", [])
            if not docs:
                raise ValueError(f"주소 '{address}'에 대한 지오코딩 결과 없음")
            return Coordinates(latitude=float(docs[0]["y"]), longitude=float(docs[0]["x"]))

    async def get_nearby_branches(self, coords: Coordinates, radius_km: float) -> list[BranchPin]:
        # Story 3.1에서 DB 조회 + 지도 핀 렌더링으로 구현
        return []
```

### AC4 — KAKAO_REST_API_KEY 필수 필드 (이미 Story 1-2에서 구현)

`app/config.py`의 `KAKAO_REST_API_KEY: str` 필드는 기본값이 없는 필수 필드임.
pydantic-settings가 `.env` 파일/환경 변수에 KAKAO_REST_API_KEY 없으면 `ValidationError` 발생 → FastAPI 앱 기동 불가.
Story 1-3에서는 **추가 구현 없이 테스트로 확인**만 수행.

### httpx 의존성

`httpx`가 아직 pyproject.toml에 없을 수 있음. `uv add httpx`로 추가 필요.
asyncio 기반 HTTP 클라이언트: `httpx.AsyncClient()` 사용 (requests 사용 금지 — 동기 블로킹).

### KakaoMapProvider 지오코딩 API 응답 구조

```json
{
  "documents": [
    {
      "x": "127.038604",
      "y": "37.498095",
      "address_name": "서울 강남구 역삼동 123",
      ...
    }
  ],
  "meta": { "total_count": 1, ... }
}
```
- `x` = 경도(longitude), `y` = 위도(latitude)
- `documents` 빈 배열 = 주소 못 찾음 → `ValueError` 발생

### 테스트 패턴 — httpx mock

```python
# tests/test_providers.py
import pytest
import respx
import httpx
from app.providers.kakao import KakaoMapProvider
from app.schemas.map import Coordinates

@pytest.mark.asyncio(loop_scope="function")
async def test_kakao_geocode_returns_coordinates():
    provider = KakaoMapProvider()
    mock_response = {
        "documents": [{"x": "127.038604", "y": "37.498095"}],
        "meta": {"total_count": 1}
    }
    with respx.mock:
        respx.get("https://dapi.kakao.com/v2/local/geo/address.json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )
        result = await provider.geocode("서울 강남구 역삼동 123")
    assert isinstance(result, Coordinates)
    assert result.latitude == pytest.approx(37.498095)
    assert result.longitude == pytest.approx(127.038604)
```

`respx` 패키지로 httpx mock: `uv add respx --dev` (테스트 전용).

### SIMULATION_ENGINE 테스트 패턴

```python
# tests/test_engines.py
import os
import importlib
import unittest.mock as mock

def test_get_engine_rule_based():
    with mock.patch.dict(os.environ, {"SIMULATION_ENGINE": "rule_based"}):
        import app.config as config_module
        importlib.reload(config_module)
        import app.services.simulation_service as svc
        importlib.reload(svc)
        from app.engines.rule_based import RuleBasedEngine
        engine = svc.get_engine()
    assert isinstance(engine, RuleBasedEngine)
    importlib.reload(sys.modules["app.config"])
    importlib.reload(sys.modules["app.services.simulation_service"])
```

### 이전 스토리 학습 사항 (Story 1-2)

- importlib.reload()로 config 모듈 먼저 재로드해야 Settings()가 패치된 환경변수를 읽음
- 테스트 후 반드시 `importlib.reload(sys.modules["app.config"])` 호출로 모듈 상태 복원
- asyncio 테스트는 `@pytest.mark.asyncio(loop_scope="function")` 사용

### 아키텍처 제약

- Kakao API 키: FastAPI `.env`에만 보관, 프론트엔드 코드에 절대 포함 금지 (NFR-2)
- `KakaoMapProvider.get_nearby_branches()`: Story 3.1에서 DB 조회로 구현, 현재는 빈 리스트 반환
- `RuleBasedEngine.predict()`: FR-2 알고리즘(유사 지점 추출, 가중 평균 등)은 Story 2.2에서 완전 구현, 현재는 stub

## Dev Agent Record

### Implementation Plan

1. schemas.py → schemas/ 마이그레이션 (models.py 패턴 재사용)
2. schemas/map.py, schemas/simulation.py 신규 타입 정의
3. engines/ 패키지 (SimulationEngine ABC + RuleBasedEngine + MLEngine stub)
4. simulation_service.get_engine() 팩토리
5. providers/ 패키지 (MapProvider ABC + KakaoMapProvider with httpx)
6. map_service.py 퍼사드
7. httpx, respx 의존성 추가 (pyproject.toml)
8. .env 로컬 개발용 플레이스홀더 생성 (테스트 실행을 위한 필수 조건)
9. test_engines.py (4개), test_providers.py (4개) 작성 및 8/8 통과 확인

### Debug Log

- schemas.py 삭제 전 schemas/__init__.py 먼저 생성 → main.py import 영향 없음 확인
- KAKAO_REST_API_KEY 미설정 검증: importlib.reload 방식 대신 Settings.model_fields.is_required() 검증으로 간소화 (pydantic-settings .env 파일 무시 문제 회피)
- respx 0.21.1 설치 확인, respx.mock 컨텍스트 매니저로 httpx 요청 인터셉트

### Completion Notes

- AC1 ✅: get_engine(rule_based) → RuleBasedEngine (test_get_engine_rule_based PASSED)
- AC2 ✅: get_engine(ml) → MLEngine, predict() delegates to RuleBasedEngine (test_get_engine_ml, test_ml_engine_delegates_to_rule_based PASSED)
- AC3 ✅: KakaoMapProvider.geocode() respx mock으로 Coordinates 반환 확인 (test_kakao_geocode_returns_coordinates PASSED)
- AC4 ✅: KAKAO_REST_API_KEY: str 필수 필드 (기본값 없음) → Settings.model_fields.is_required() 확인 (test_kakao_rest_api_key_required PASSED)
- AC5 ✅: schemas/map.py Coordinates+BranchPin 정의, get_nearby_branches() list[BranchPin] 반환 (test_map_provider_get_nearby_branches_returns_list PASSED)
- 전체 테스트: 8/8 신규 PASSED, 기존 non-DB 테스트 전원 PASSED, DB 연결 필요 테스트는 로컬 PostgreSQL 없어서 기존과 동일하게 실패 (CI에서만 실행)

## File List

신규 생성:
- fastapi_backend/app/schemas/__init__.py
- fastapi_backend/app/schemas/map.py
- fastapi_backend/app/schemas/simulation.py
- fastapi_backend/app/engines/__init__.py
- fastapi_backend/app/engines/base.py
- fastapi_backend/app/engines/rule_based.py
- fastapi_backend/app/engines/ml_engine.py
- fastapi_backend/app/services/simulation_service.py
- fastapi_backend/app/providers/__init__.py
- fastapi_backend/app/providers/base.py
- fastapi_backend/app/providers/kakao.py
- fastapi_backend/app/services/map_service.py
- fastapi_backend/tests/test_engines.py
- fastapi_backend/tests/test_providers.py
- fastapi_backend/.env (로컬 개발용, gitignore 제외)

수정:
- fastapi_backend/pyproject.toml (httpx 의존성 추가, respx dev 의존성 추가)

삭제:
- fastapi_backend/app/schemas.py (schemas/ 디렉토리로 대체)

## Change Log

- 2026-06-12: Story 1-3 구현 완료 — SimulationEngine ABC + RuleBasedEngine + MLEngine stub + MapProvider ABC + KakaoMapProvider + schemas/map.py + schemas/simulation.py + 8개 테스트 추가

## Review Findings (AI Senior Dev — 2026-06-12)

- [x] [Review][Patch] httpx timeout 미설정 — AsyncClient(timeout=10.0) 추가 [app/providers/kakao.py:13]
- [x] [Review][Patch] _restore_service() 테스트 정리 try/finally 누락 — try/finally로 래핑 [tests/test_engines.py:27-31,34-39]
- [x] [Review][Patch] AC4 테스트 metadata 확인만 — IsolatedSettings + ValidationError 실제 검증으로 교체 [tests/test_providers.py:59-65]
- [x] [Review][Patch] AC3 테스트 Authorization 헤더 미검증 — route.calls.last.request.headers 검증 추가 [tests/test_providers.py:27-36]
- [x] [Review][Defer] raise_for_status() httpx.HTTPStatusError 미처리 — 라우터 에러 핸들링은 Story 2.2/3.1 범위
- [x] [Review][Defer] resp.json() JSONDecodeError 미처리 — 동일, Story 2.2/3.1 범위
- [x] [Review][Defer] docs[0]["x"/"y"] 키 미존재 시 KeyError — Kakao API 응답 파싱 완전 구현은 Story 3.1
- [x] [Review][Defer] verdict: str → Literal["추천","검토필요","비추천"] — Story 1-2에서 이미 defer됨
- [x] [Review][Defer] SIMULATION_ENGINE Literal 타입 미지정 — Story 1-2에서 이미 defer됨
- [x] [Review][Defer] AsyncClient 호출마다 생성 (연결 풀링 없음) — Story 3.1에서 최적화
- [x] [Review][Defer] _provider 모듈 레벨 싱글톤 — 현재 무상태, Story 3.1에서 재검토
- [x] [Review][Defer] schemas/__init__.py map/simulation 미재export — 현재 임포트 모두 명시적 경로 사용, 미래 개선
- [x] [Review][Defer] Coordinates lat/lon 범위 검증 없음 — Story 3.1 범위
- [x] [Review][Defer] area_sqm/monthly_rent 음수 허용 — Story 2.1 범위
- [x] [Review][Defer] percentile 0-100 범위 검증 없음 — Story 2.2 범위
- [x] [Review][Defer] MLEngine 매 호출마다 RuleBasedEngine 생성 — stub 설계, v2 대체 예정
- [x] [Review][Defer] AC5 BranchPin 빈 리스트 vacuous 검증 — stub이 [] 반환, Story 3.1에서 실질 검증
- [x] [Review][Defer] AC2 위임 경로 미검증 (결과값만 확인) — Story 2.2에서 실 구현 시 검증
- [x] [Review][Defer] issubclass ABC 계약 테스트 없음 — low value
- [x] [Review][Defer] NFR-2 API 키 응답 누출 방지 테스트 없음 — speculative, defer
