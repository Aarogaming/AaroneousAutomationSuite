import os

from core.health_manager import HealthAggregator


class DummyDB:
    def __init__(self):
        self.checked = False

    def get_session(self):
        class Session:
            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                return False

            def execute(self_inner, _):
                self.checked = True

        return Session()


def test_health_aggregator_includes_overall_status(monkeypatch):
    # Avoid real network / web / ipc touches
    monkeypatch.setenv("AAS_HEALTH_SKIP_LATENCY", "1")
    monkeypatch.setenv("AAS_HEALTH_SKIP_WEB", "1")
    monkeypatch.setenv("AAS_HEALTH_SKIP_IPC", "1")
    monkeypatch.setenv("AAS_ARTIFACTS_DIR", "artifacts")

    agg = HealthAggregator(db_manager=DummyDB())
    summary = agg.scan()

    assert "overall_status" in summary
    assert summary["overall_status"] in {"healthy", "warning", "critical"}
    assert summary["components"]["database"] in {"connected", "error"}
    assert summary["components"]["workspace"] in {"healthy", "warning", "error", "unknown"}
    # Ensure DB check ran
    assert agg._db_manager.checked is True
