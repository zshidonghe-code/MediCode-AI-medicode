"""Regression tests for repeatable application startup initialization."""
from unittest.mock import AsyncMock

import pytest

import src.main as main
from src.services.llm_engine import llm_engine


class _ScalarResult:
    def __init__(self, value: int):
        self.value = value

    def scalar(self):
        return self.value


class _StartupSession:
    def __init__(self, state: dict[str, int]):
        self.state = state

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, query):
        if str(query).upper().startswith("ANALYZE"):
            return None
        return _ScalarResult(self.state["patient_count"])


class _StartupEngine:
    def __init__(self):
        self.dispose = AsyncMock()


@pytest.mark.asyncio
async def test_lifespan_does_not_reseed_demo_data_on_second_start(monkeypatch):
    state = {"patient_count": 0}
    init_db = AsyncMock()
    seed_reference_data = AsyncMock(side_effect=[True, False])
    seed_pipeline_demo = AsyncMock(side_effect=lambda: state.update(patient_count=1))
    engine = _StartupEngine()

    monkeypatch.setattr(main, "init_db", init_db)
    monkeypatch.setattr(main, "async_session", lambda: _StartupSession(state))
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main.settings, "auto_seed_demo_data", True)
    monkeypatch.setattr(
        "src.scripts.seed_data.seed_reference_data_if_needed",
        seed_reference_data,
    )
    monkeypatch.setattr("src.scripts.seed_pipeline_demo.seed_pipeline_demo", seed_pipeline_demo)
    monkeypatch.setattr(llm_engine, "prewarm", AsyncMock(return_value="rule"))

    async with main.lifespan(main.app):
        pass
    async with main.lifespan(main.app):
        pass

    assert init_db.await_count == 2
    assert seed_reference_data.await_count == 2
    seed_pipeline_demo.assert_awaited_once_with()
    assert engine.dispose.await_count == 2


@pytest.mark.asyncio
async def test_lifespan_does_not_seed_demo_data_when_disabled(monkeypatch):
    state = {"patient_count": 0}
    init_db = AsyncMock()
    seed_reference_data = AsyncMock(return_value=False)
    seed_pipeline_demo = AsyncMock()
    engine = _StartupEngine()

    monkeypatch.setattr(main, "init_db", init_db)
    monkeypatch.setattr(main, "async_session", lambda: _StartupSession(state))
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.setattr(main.settings, "auto_seed_demo_data", False)
    monkeypatch.setattr(
        "src.scripts.seed_data.seed_reference_data_if_needed",
        seed_reference_data,
    )
    monkeypatch.setattr("src.scripts.seed_pipeline_demo.seed_pipeline_demo", seed_pipeline_demo)
    monkeypatch.setattr(llm_engine, "prewarm", AsyncMock(return_value="rule"))

    async with main.lifespan(main.app):
        pass

    seed_pipeline_demo.assert_not_awaited()
    assert engine.dispose.await_count == 1
