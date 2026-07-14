"""LLM engine fallback tests that do not require a running model."""

from types import SimpleNamespace
from typing import cast
from unittest.mock import AsyncMock

import pytest

import src.services.llm_engine as llm_module
from src.services.icd_coder.coder import ICDCoder
from src.services.llm_engine.engine import LLMEngine, OllamaBackend


@pytest.mark.asyncio
async def test_code_recommend_falls_back_when_ollama_generation_fails() -> None:
    engine = LLMEngine()
    engine._ollama = cast(
        OllamaBackend,
        SimpleNamespace(
            is_available=AsyncMock(return_value=True),
            generate_json=AsyncMock(side_effect=RuntimeError("model request failed")),
        ),
    )
    candidate = SimpleNamespace(code="I21.9", name="Acute myocardial infarction", score=0.72)

    result = await engine.code_recommend("cardiac event", [candidate])

    assert result is not None
    assert result.code == candidate.code
    assert result.confidence == candidate.score
    assert engine.backend_type == "ollama"


@pytest.mark.asyncio
async def test_recommend_does_not_call_llm_without_validated_candidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coder = ICDCoder()
    monkeypatch.setattr(coder, "_db_search", AsyncMock(return_value=[]))
    monkeypatch.setattr(coder, "_local_search", lambda _text: [])
    monkeypatch.setattr(coder, "_ensure_vector_index", lambda: None)
    coder._vector_ready = False

    recommend_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(llm_module.llm_engine, "code_recommend", recommend_mock)

    result = await coder.recommend("no known clinical code", use_llm=True)

    assert result == []
    recommend_mock.assert_not_awaited()
