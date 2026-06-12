import importlib
import os
import sys
import unittest.mock as mock
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.engines.ml_engine import MLEngine
from app.engines.rule_based import RuleBasedEngine
from app.schemas.simulation import LocationConditions, SimulationResult


def _empty_db():
    """Mock AsyncSession that returns empty results → triggers _default_estimate path."""
    session = AsyncMock()
    empty_scalars = MagicMock()
    empty_scalars.all.return_value = []
    empty_result = MagicMock()
    empty_result.scalars.return_value = empty_scalars
    empty_result.all.return_value = []
    session.execute.return_value = empty_result
    return session


def _reload_service():
    import app.config as config_module
    importlib.reload(config_module)
    import app.services.simulation_service as svc
    importlib.reload(svc)
    return svc


def _restore_service():
    importlib.reload(sys.modules["app.config"])
    importlib.reload(sys.modules["app.services.simulation_service"])


def test_get_engine_rule_based():
    with mock.patch.dict(os.environ, {"SIMULATION_ENGINE": "rule_based"}):
        svc = _reload_service()
        engine = svc.get_engine()
    try:
        assert isinstance(engine, RuleBasedEngine)
    finally:
        _restore_service()


def test_get_engine_ml():
    with mock.patch.dict(os.environ, {"SIMULATION_ENGINE": "ml"}):
        svc = _reload_service()
        engine = svc.get_engine()
    try:
        assert isinstance(engine, MLEngine)
    finally:
        _restore_service()


@pytest.mark.asyncio(loop_scope="function")
async def test_rule_based_engine_returns_simulation_result():
    engine = RuleBasedEngine()
    location = LocationConditions(address="서울 강남구 역삼동 123", area_sqm=100.0, monthly_rent=5000000.0)
    result = await engine.predict(location, _empty_db())
    assert isinstance(result, SimulationResult)
    assert result.verdict == "검토필요"
    assert result.similar_branch_count == 0
    assert isinstance(result.comparison_data, list)


@pytest.mark.asyncio(loop_scope="function")
async def test_ml_engine_delegates_to_rule_based():
    engine = MLEngine()
    location = LocationConditions(address="서울 강남구 역삼동 123", area_sqm=100.0, monthly_rent=5000000.0)
    result = await engine.predict(location, _empty_db())
    assert isinstance(result, SimulationResult)
    assert result.verdict == "검토필요"
