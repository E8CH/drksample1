from app.config import settings
from app.engines.base import SimulationEngine
from app.engines.ml_engine import MLEngine
from app.engines.rule_based import RuleBasedEngine


def get_engine() -> SimulationEngine:
    if settings.SIMULATION_ENGINE == "ml":
        return MLEngine()
    return RuleBasedEngine()
