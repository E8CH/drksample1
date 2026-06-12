# Story 1.2: 데이터베이스 스키마 & Alembic 마이그레이션

Status: done

## Story

As a 개발자,
I want 4개 테이블(branches, operations, members, sales)과 Alembic 마이그레이션을 구성하고 싶다,
so that 이후 모든 스토리가 DB에 데이터를 저장하고 조회할 수 있다.

## Acceptance Criteria

1. `alembic upgrade head` 실행 후 branches, operations, members, sales 테이블 생성됨. sales 테이블에 2016~2025년 연도별 파티션 10개(sales_2016 ~ sales_2025) 존재함
2. idx_sales_branch_date(복합), idx_sales_date_brin(BRIN) 인덱스 두 개 정상 생성됨
3. `alembic downgrade -1` 실행 시 직전 마이그레이션 상태로 복원됨 (branches, operations, members, sales + 파티션 전부 삭제)
4. `postgresql+asyncpg://` 드라이버로 FastAPI 시작 시 비동기 DB 커넥션 정상 수립. `postgresql://` URL 설정 시 startup 시 경고 로그 출력됨

## Tasks / Subtasks

- [x] Task 1: app/models/ 디렉토리 구조로 리팩터링 (AC: 사전조건)
  - [x] `app/models/user.py` 생성 — 기존 `app/models.py`의 Base, User, Item 이동
  - [x] `app/models/branch.py` 생성 — Branch 모델
  - [x] `app/models/member.py` 생성 — Member 모델
  - [x] `app/models/operations.py` 생성 — Operation 모델
  - [x] `app/models/sales.py` 생성 — Sales 모델
  - [x] `app/models/__init__.py` 생성 — 모든 모델 re-export
  - [x] `app/models.py` 삭제 (models/ 디렉토리와 공존 불가)
  - [x] `app/database.py` import 확인 (변경 불필요 — __init__.py re-export로 호환)
  - [x] `tests/conftest.py` import 확인 (변경 불필요)

- [x] Task 2: config.py 환경 변수 추가 (AC: #4)
  - [x] `SECRET_KEY: str` 필드 추가
  - [x] `KAKAO_REST_API_KEY: str` 필드 추가
  - [x] `SIMULATION_ENGINE: str = "rule_based"` 필드 추가

- [x] Task 3: database.py — postgresql:// 경고 로그 추가 (AC: #4)
  - [x] DATABASE_URL이 `postgresql+asyncpg://`로 시작하지 않을 경우 `logger.warning()` 출력

- [x] Task 4: Alembic 마이그레이션 파일 작성 (AC: #1, #2, #3)
  - [x] `alembic_migrations/versions/c1a2b3d4e5f6_add_drksample1_schema.py` 생성
  - [x] `down_revision = "b389592974f8"` 설정
  - [x] upgrade(): branches, members, operations 테이블 op.create_table()로 생성
  - [x] upgrade(): sales 테이블은 반드시 op.execute() raw SQL로 PARTITION BY RANGE 생성
  - [x] upgrade(): sales_2016~sales_2025 파티션 10개 op.execute()로 생성
  - [x] upgrade(): idx_sales_branch_date op.create_index(), idx_sales_date_brin op.execute(BRIN)
  - [x] downgrade(): 역순 — 인덱스→파티션→sales→operations→members→branches 삭제

- [x] Task 5: 마이그레이션 테스트 작성 (AC: #1, #2, #3, #4)
  - [x] `tests/test_migrations.py` 생성
  - [x] alembic upgrade head → 테이블/파티션/인덱스 존재 확인
  - [x] alembic downgrade -1 → 테이블 제거 확인
  - [x] asyncpg 드라이버 경고 로그 테스트

### Review Findings (AI Senior Dev — 2026-06-13)

- [x] [Review][Patch] SECRET_KEY, KAKAO_REST_API_KEY 기본값 `""` 제거 — 스펙은 필수 필드, 빈 문자열 기본값은 보안 위험 [app/config.py:37-38]
- [x] [Review][Patch] sales.py 미사용 `pg_dialect` import 제거 [app/models/sales.py:2] — 이미 제거된 상태였음
- [x] [Review][Patch] test_asyncpg 테스트 후 모듈 상태 복원 누락 — 이후 테스트 오염 방지 [tests/test_migrations.py:76]
- [x] [Review][Patch] downgrade 테스트에서 복구용 `upgrade head` return code 미체크 [tests/test_migrations.py:73]
- [x] [Review][Patch] 마이그레이션 테스트 engine.dispose() — assert 실패 시 연결 누수. try/finally 추가 [tests/test_migrations.py:31,62]
- [x] [Review][Defer] 2026년 이후 데이터 삽입 시 파티션 없음 오류 — 스토리 1-2 스펙은 2016-2025만 정의, 향후 스토리에서 처리
- [x] [Review][Defer] URL 재구성 시 쿼리 파라미터 손실 (`?ssl=require` 등) — database.py 기존 코드, 이번 변경 범위 외
- [x] [Review][Defer] urlparse 비밀번호 특수문자 디코딩 후 재인코딩 없이 삽입 — database.py 기존 코드, 이번 변경 범위 외
- [x] [Review][Defer] Branch/Member 가변 텍스트 PK (branch_name, email) — FK ON UPDATE CASCADE 없음, 아키텍처 결정 사항
- [x] [Review][Defer] Operation (branch_name, month) 유니크 제약 없음 — 향후 스토리 범위
- [x] [Review][Defer] Numeric 컬럼 precision/scale 미지정 — 아키텍처 결정 사항
- [x] [Review][Defer] daily_revenue CHECK >= 0 없음 — 향후 스토리 범위
- [x] [Review][Defer] email 대소문자 구분 PK 이슈 — 향후 스토리 범위
- [x] [Review][Defer] BRIN 인덱스 향후 파티션에 자동 상속 안 됨 — 알려진 PostgreSQL 동작
- [x] [Review][Defer] conftest create_all이 파티션 없는 sales 테이블 생성 — Dev Notes에 문서화됨
- [x] [Review][Defer] SIMULATION_ENGINE Literal 타입 미지정 — 향후 개선
- [x] [Review][Defer] 수동 revision ID c1a2b3d4e5f6 — 동작 정상, 변경 시 마이그레이션 체인 수정 필요
- [x] [Review][Defer] pytest.mark.asyncio 데코레이터 asyncio_mode=auto와 중복 — 마이너 클린업
- [x] [Review][Defer] Base를 user.py에 정의 — 기존 패턴
- [x] [Review][Defer] Operation.month 월 첫째날 CHECK 없음 — 향후 스토리 범위

## Dev Notes

### ⚠️ CRITICAL: models.py → models/ 디렉토리 마이그레이션

현재 `app/models.py` (단일 파일)이 존재하고 `database.py`와 `conftest.py`가 이를 임포트함.
아키텍처는 `app/models/` 디렉토리를 요구. **파일과 디렉토리 동명 공존 불가** — 반드시 `models.py` 삭제 후 `models/` 생성.

```python
# app/models/user.py — 기존 models.py 내용 그대로 이동
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")

class Item(Base):
    __tablename__ = "items"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    user = relationship("User", back_populates="items")
```

```python
# app/models/__init__.py
from .user import Base, User, Item
from .branch import Branch
from .member import Member
from .operations import Operation
from .sales import Sales

__all__ = ["Base", "User", "Item", "Branch", "Member", "Operation", "Sales"]
```

`app/database.py`와 `tests/conftest.py`의 `from app.models import Base, User` 임포트는 **변경 불필요**.

### ⚠️ CRITICAL: Alembic — 파티션 테이블은 반드시 op.execute() raw SQL

SQLAlchemy/Alembic `op.create_table()`은 `PARTITION BY RANGE`를 지원하지 않음.
`sales` 테이블과 10개 파티션은 **반드시 raw SQL**로 생성해야 함.

```python
# alembic_migrations/versions/xxxx_add_drksample1_schema.py
"""Add drksample1 schema: branches, members, operations, sales

Revision ID: <자동생성>
Revises: b389592974f8
Create Date: <자동생성>
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "<자동생성>"
down_revision: Union[str, None] = "b389592974f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # branches (마스터)
    op.create_table(
        "branches",
        sa.Column("branch_name", sa.Text(), primary_key=True),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("area_sqm", sa.Numeric(), nullable=True),
        sa.Column("monthly_rent", sa.Numeric(), nullable=True),
        sa.Column("maintenance_fee", sa.Numeric(), nullable=True),
        sa.Column("building_usage", sa.Text(), nullable=True),
        sa.Column("ev_charging", sa.Boolean(), server_default="false"),
        sa.Column("parking_count", sa.Integer(), server_default="0"),
    )

    # members
    op.create_table(
        "members",
        sa.Column("email", sa.Text(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
    )

    # operations (월별 운영비)
    op.create_table(
        "operations",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("branch_name", sa.Text(), sa.ForeignKey("branches.branch_name"), nullable=False),
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("electricity_fee", sa.Numeric(), nullable=True),
        sa.Column("operating_cost", sa.Numeric(), nullable=True),
    )

    # sales — PARTITION BY RANGE: 반드시 raw SQL
    op.execute("""
        CREATE TABLE sales (
            id          BIGSERIAL,
            branch_name TEXT REFERENCES branches(branch_name),
            member_email TEXT REFERENCES members(email),
            sale_date   DATE NOT NULL,
            daily_revenue NUMERIC NOT NULL
        ) PARTITION BY RANGE (sale_date)
    """)

    # 연도별 파티션 2016~2025
    for year in range(2016, 2026):
        op.execute(f"""
            CREATE TABLE sales_{year} PARTITION OF sales
            FOR VALUES FROM ('{year}-01-01') TO ('{year + 1}-01-01')
        """)

    # 인덱스
    op.create_index("idx_sales_branch_date", "sales", ["branch_name", "sale_date"])
    # BRIN 인덱스 — op.create_index() 미지원, raw SQL 필수
    op.execute("CREATE INDEX idx_sales_date_brin ON sales USING BRIN (sale_date)")


def downgrade() -> None:
    # 역순: 인덱스 → 파티션 → sales → operations → members → branches
    op.execute("DROP INDEX IF EXISTS idx_sales_date_brin")
    op.execute("DROP INDEX IF EXISTS idx_sales_branch_date")
    for year in range(2025, 2015, -1):
        op.execute(f"DROP TABLE IF EXISTS sales_{year}")
    op.execute("DROP TABLE IF EXISTS sales")
    op.drop_table("operations")
    op.drop_table("members")
    op.drop_table("branches")
```

**마이그레이션 파일 생성 방법:**
```bash
cd fastapi_backend
alembic revision -m "add_drksample1_schema"
# 생성된 파일에 위 upgrade()/downgrade() 내용을 직접 작성
# autogenerate 사용 금지 — 파티션 테이블이 잘못 생성됨
```

### SQLAlchemy ORM 모델 정의

파티션은 마이그레이션에서 처리. ORM 모델은 컬럼 정의만.

```python
# app/models/branch.py
from sqlalchemy import Column, Text, Numeric, Boolean, Integer
from .user import Base

class Branch(Base):
    __tablename__ = "branches"
    branch_name = Column(Text, primary_key=True)
    address = Column(Text, nullable=False)
    area_sqm = Column(Numeric, nullable=True)
    monthly_rent = Column(Numeric, nullable=True)
    maintenance_fee = Column(Numeric, nullable=True)
    building_usage = Column(Text, nullable=True)
    ev_charging = Column(Boolean, default=False)
    parking_count = Column(Integer, default=0)
```

```python
# app/models/member.py
from sqlalchemy import Column, Text
from .user import Base

class Member(Base):
    __tablename__ = "members"
    email = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    phone = Column(Text, nullable=True)
    address = Column(Text, nullable=True)
```

```python
# app/models/operations.py
from sqlalchemy import Column, BigInteger, Text, Date, Numeric, ForeignKey
from .user import Base

class Operation(Base):
    __tablename__ = "operations"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    branch_name = Column(Text, ForeignKey("branches.branch_name"), nullable=False)
    month = Column(Date, nullable=False)
    electricity_fee = Column(Numeric, nullable=True)
    operating_cost = Column(Numeric, nullable=True)
```

```python
# app/models/sales.py
from sqlalchemy import Column, BigInteger, Text, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import dialect as pg_dialect
from .user import Base

class Sales(Base):
    __tablename__ = "sales"
    # PARTITION BY RANGE는 마이그레이션에서 raw SQL로 처리됨
    # ORM에서는 컬럼 정의만
    __table_args__ = {"postgresql_partition_by": "RANGE (sale_date)"}
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    branch_name = Column(Text, ForeignKey("branches.branch_name"), nullable=True)
    member_email = Column(Text, ForeignKey("members.email"), nullable=True)
    sale_date = Column(Date, nullable=False)
    daily_revenue = Column(Numeric, nullable=False)
```

### config.py 추가 필드

`app/config.py`의 `Settings` 클래스에 추가:

```python
# drksample1 추가 설정 (기존 코드 아래에 추가)
SECRET_KEY: str  # python3 -c "import secrets; print(secrets.token_hex(32))"
KAKAO_REST_API_KEY: str
SIMULATION_ENGINE: str = "rule_based"
```

### database.py — postgresql:// 경고 로그

```python
import logging
logger = logging.getLogger(__name__)

# DATABASE_URL 파싱 직전에 추가
if not settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
    logger.warning(
        "DATABASE_URL should use postgresql+asyncpg:// driver. "
        "Using postgresql:// causes event loop blocking. Auto-converting."
    )
```

### ⚠️ CRITICAL: conftest.py와 파티션 테이블 호환성

기존 `conftest.py`는 `Base.metadata.create_all`을 사용. 이 방식으로 `sales` 테이블을 생성하면 파티션 자식 테이블이 생성되지 않아 INSERT 시 오류 발생.

**기존 test_health.py 등 sales 테이블을 사용하지 않는 테스트는 영향 없음.**

마이그레이션 테스트(`test_migrations.py`)는 alembic을 직접 실행하는 별도 방식 사용:

```python
# tests/test_migrations.py
import pytest
import asyncpg
import subprocess
import os
from sqlalchemy.ext.asyncio import create_async_engine, text

TEST_DB_URL = os.getenv("DATABASE_URL", "")

@pytest.mark.asyncio(loop_scope="function")
async def test_migration_upgrade_and_downgrade():
    """alembic upgrade head → 테이블 확인 → downgrade -1 확인"""
    # upgrade
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"alembic upgrade failed: {result.stderr}"

    engine = create_async_engine(TEST_DB_URL)
    async with engine.connect() as conn:
        for table in ["branches", "members", "operations", "sales"]:
            result = await conn.execute(
                text(f"SELECT to_regclass('public.{table}')")
            )
            assert result.scalar() is not None, f"Table {table} not found"

        # 파티션 확인
        for year in range(2016, 2026):
            result = await conn.execute(
                text(f"SELECT to_regclass('public.sales_{year}')")
            )
            assert result.scalar() is not None, f"Partition sales_{year} not found"

        # 인덱스 확인
        for idx in ["idx_sales_branch_date", "idx_sales_date_brin"]:
            result = await conn.execute(
                text(f"SELECT indexname FROM pg_indexes WHERE indexname = '{idx}'")
            )
            assert result.scalar() is not None, f"Index {idx} not found"
    await engine.dispose()

    # downgrade
    result = subprocess.run(
        ["uv", "run", "alembic", "downgrade", "-1"],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"alembic downgrade failed: {result.stderr}"

    engine = create_async_engine(TEST_DB_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT to_regclass('public.branches')"))
        assert result.scalar() is None, "branches table should not exist after downgrade"
    await engine.dispose()
```

### 파일 구조 변경 요약

```
fastapi_backend/app/
├── models.py          ← 삭제 (models/ 디렉토리로 교체)
└── models/
    ├── __init__.py    ← NEW: Base, User, Item, Branch, Member, Operation, Sales re-export
    ├── user.py        ← NEW: 기존 models.py 내용 (Base, User, Item)
    ├── branch.py      ← NEW
    ├── member.py      ← NEW
    ├── operations.py  ← NEW
    └── sales.py       ← NEW

fastapi_backend/app/
├── config.py          ← UPDATE: SECRET_KEY, KAKAO_REST_API_KEY, SIMULATION_ENGINE 추가
└── database.py        ← UPDATE: postgresql:// 경고 로그 추가

fastapi_backend/alembic_migrations/versions/
└── xxxx_add_drksample1_schema.py  ← NEW

fastapi_backend/tests/
└── test_migrations.py  ← NEW
```

### alembic_migrations/env.py 주의사항

현재 `env.py`는 `from app.models import Base`를 임포트하고 `target_metadata = Base.metadata`를 사용.
`models/__init__.py`에서 모든 모델을 임포트하면 `Base.metadata`가 새 테이블들도 포함 — **env.py 변경 불필요**.

### 아키텍처 필수 준수 사항

- DB 컬럼명: `snake_case` 필수 (`branchName` 사용 금지)
- DB 드라이버: `postgresql+asyncpg://` 필수 (`postgresql://` 절대 금지)
- 인덱스 네이밍: `idx_{table}_{column}` 규칙 — `idx_sales_branch_date`, `idx_sales_date_brin`
- sales 테이블 `month` 컬럼: `DATE` 타입, 월 첫째날로 정규화 (예: `2025-12-01`)

### 스토리 1.1에서 가져온 패턴

- 테스트 실행: `cd fastapi_backend && uv run pytest tests/ -v`
- DB 드라이버 변환 로직: `database.py`의 `urlparse` + `postgresql+asyncpg://` 조립 패턴 이미 존재 — 재구현 금지
- conftest.py의 `test_client` fixture: `Base.metadata.create_all` 사용 — sales 테이블 테스트는 별도 fixture 필요

### 참고 소스

- [Source: architecture.md#3.1-데이터-아키텍처] DB 스키마 정의 (SQL DDL 포함)
- [Source: architecture.md#4-네이밍-규칙] snake_case, idx_ 네이밍
- [Source: architecture.md#AI-에이전트-필수-준수-사항] asyncpg 드라이버 필수

## Dev Agent Record

### Agent Model Used
claude-sonnet-4-6

### Completion Notes List

- 모든 모델 파일(user, branch, member, operations, sales)이 `app/models/` 디렉토리에 정확히 구현되어 있었음. `app/models.py`는 이미 삭제되어 있음.
- `app/config.py`에 `SECRET_KEY`, `KAKAO_REST_API_KEY`, `SIMULATION_ENGINE` 필드 추가 완료. `SECRET_KEY`는 기본값 `""`로 설정하여 개발 환경 시작 허용.
- `app/database.py`에 `postgresql+asyncpg://` 드라이버 경고 로그 추가 완료. 모듈 로드 시점에 즉시 체크.
- Alembic 마이그레이션 파일 `c1a2b3d4e5f6_add_drksample1_schema.py` 생성 완료. `PARTITION BY RANGE`는 raw SQL로 처리, BRIN 인덱스도 raw SQL 사용.
- `tests/test_migrations.py` 작성 완료. `test_asyncpg_driver_warning_on_plain_url` 테스트에서 `importlib.reload` 시 `app.config`도 함께 재로드해야 경고가 올바르게 캡처됨 — 이 점을 수정함.
- 모든 모델이 `Base.metadata`에 등록됨 확인: ['user', 'items', 'branches', 'members', 'operations', 'sales']
- DB 불필요한 테스트 9개 통과 (test_database.py 5개, test_email.py 2개, test_utils.py 1개, test_asyncpg_warning 1개)
- DB 의존 마이그레이션 테스트(upgrade/downgrade)는 CI에서 PostgreSQL과 함께 실행됨

### File List
- NEW: `fastapi_backend/app/models/__init__.py`
- NEW: `fastapi_backend/app/models/user.py`
- NEW: `fastapi_backend/app/models/branch.py`
- NEW: `fastapi_backend/app/models/member.py`
- NEW: `fastapi_backend/app/models/operations.py`
- NEW: `fastapi_backend/app/models/sales.py`
- NEW: `fastapi_backend/alembic_migrations/versions/c1a2b3d4e5f6_add_drksample1_schema.py`
- NEW: `fastapi_backend/tests/test_migrations.py`
- DELETE: `fastapi_backend/app/models.py`
- UPDATE: `fastapi_backend/app/config.py`
- UPDATE: `fastapi_backend/app/database.py`

### Change Log
- 2026-06-12: 스토리 1-2 구현 완료. models/ 디렉토리 리팩터링, config.py 환경 변수 추가, database.py 경고 로그, Alembic 마이그레이션(파티션/인덱스 포함), 마이그레이션 테스트 작성. test_asyncpg_driver_warning_on_plain_url 테스트에서 app.config 재로드 버그 수정.
