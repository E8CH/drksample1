from app.config import settings
from app.engines.base import SimulationEngine
from app.engines.ml_engine import MLEngine
from app.engines.rule_based import RuleBasedEngine

# Singleton: engine is stateless (RuleBasedEngine) but MLEngine may load a model at init.
# Re-instantiating on every request would reload the model from disk each call.
_engine_instance: SimulationEngine | None = None


def get_engine() -> SimulationEngine:
    global _engine_instance
    if _engine_instance is None:
        if settings.SIMULATION_ENGINE == "ml":
            _engine_instance = MLEngine()
        else:
            _engine_instance = RuleBasedEngine()
    return _engine_instance
