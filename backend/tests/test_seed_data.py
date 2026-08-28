"""Regression tests for independent reference-data initialization."""
from unittest.mock import AsyncMock

import pytest

from src.scripts import seed_data


class _Result:
    def __init__(self, count: int):
        self._count = count

    def scalar(self):
        return self._count


class _Session:
    def __init__(self, existing: tuple[bool, bool, bool]):
        self._results = iter(_Result(int(value)) for value in existing)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def execute(self, _query):
        return next(self._results)


@pytest.mark.asyncio
async def test_seed_reference_data_fills_missing_dataset_when_icd_exists(monkeypatch):
    monkeypatch.setattr(
        seed_data,
        "async_session",
        lambda: _Session((True, False, False)),
    )
    seed_icd = AsyncMock()
    seed_drg = AsyncMock()
    seed_qc = AsyncMock()
    monkeypatch.setattr(seed_data, "seed_icd_codes", seed_icd)
    monkeypatch.setattr(seed_data, "seed_drg_groups", seed_drg)
    monkeypatch.setattr(seed_data, "seed_qc_rules", seed_qc)

    seeded = await seed_data.seed_reference_data_if_needed()

    assert seeded is True
    seed_icd.assert_not_awaited()
    seed_drg.assert_awaited_once_with()
    seed_qc.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_seed_reference_data_is_noop_when_all_datasets_exist(monkeypatch):
    monkeypatch.setattr(
        seed_data,
        "async_session",
        lambda: _Session((True, True, True)),
    )
    seed_icd = AsyncMock()
    seed_drg = AsyncMock()
    seed_qc = AsyncMock()
    monkeypatch.setattr(seed_data, "seed_icd_codes", seed_icd)
    monkeypatch.setattr(seed_data, "seed_drg_groups", seed_drg)
    monkeypatch.setattr(seed_data, "seed_qc_rules", seed_qc)

    seeded = await seed_data.seed_reference_data_if_needed()

    assert seeded is False
    seed_icd.assert_not_awaited()
    seed_drg.assert_not_awaited()
    seed_qc.assert_not_awaited()
