import logging
import os
import subprocess

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://testuser:testpass@localhost:5432/testdb",
)

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run_alembic(command: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "alembic"] + command,
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )


@pytest.mark.asyncio(loop_scope="function")
async def test_migration_upgrade_creates_tables_and_partitions():
    result = _run_alembic(["upgrade", "head"])
    assert result.returncode == 0, f"alembic upgrade failed:\n{result.stderr}"

    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            for table in ("branches", "members", "operations", "sales"):
                row = await conn.execute(
                    text(f"SELECT to_regclass('public.{table}')")
                )
                assert row.scalar() is not None, f"Table '{table}' was not created"

            for year in range(2016, 2026):
                row = await conn.execute(
                    text(f"SELECT to_regclass('public.sales_{year}')")
                )
                assert row.scalar() is not None, f"Partition 'sales_{year}' was not created"

            for idx in ("idx_sales_branch_date", "idx_sales_date_brin"):
                row = await conn.execute(
                    text(
                        "SELECT indexname FROM pg_indexes "
                        f"WHERE indexname = '{idx}'"
                    )
                )
                assert row.scalar() is not None, f"Index '{idx}' was not created"
    finally:
        await engine.dispose()


@pytest.mark.asyncio(loop_scope="function")
async def test_migration_downgrade_removes_tables():
    result = _run_alembic(["downgrade", "-1"])
    assert result.returncode == 0, f"alembic downgrade failed:\n{result.stderr}"

    engine = create_async_engine(TEST_DB_URL)
    try:
        async with engine.connect() as conn:
            for table in ("branches", "members", "operations", "sales"):
                row = await conn.execute(
                    text(f"SELECT to_regclass('public.{table}')")
                )
                assert row.scalar() is None, f"Table '{table}' should not exist after downgrade"
    finally:
        await engine.dispose()

    # 다시 upgrade하여 이후 테스트에 영향 없도록 복구
    restore = _run_alembic(["upgrade", "head"])
    assert restore.returncode == 0, f"alembic upgrade (restore) failed:\n{restore.stderr}"


def test_asyncpg_driver_warning_on_plain_url(caplog):
    """postgresql:// URL 사용 시 database.py 로드 시점에 warning 로그 출력 확인."""
    import importlib
    import sys
    import unittest.mock as mock

    with mock.patch.dict(
        os.environ,
        {"DATABASE_URL": "postgresql://user:pass@localhost/db"},
    ):
        with caplog.at_level(logging.WARNING, logger="app.database"):
            # config 먼저 재로드해야 Settings()가 패치된 DATABASE_URL을 읽음
            import app.config as config_module
            importlib.reload(config_module)
            import app.database as db_module
            importlib.reload(db_module)

    warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
    assert any(
        "postgresql+asyncpg" in msg for msg in warning_messages
    ), f"Expected asyncpg warning not found. Got: {warning_messages}"

    # 다른 테스트에 영향 없도록 원래 DATABASE_URL로 모듈 상태 복원
    importlib.reload(sys.modules["app.config"])
    importlib.reload(sys.modules["app.database"])
