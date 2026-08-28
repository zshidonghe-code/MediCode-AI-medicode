"""Import ICD-10 clinical and ICD-9-CM-3 codes into the database.

Usage:
    python -m src.scripts.seed_icd_data
    # or inside Docker:
    docker compose exec backend python -m src.scripts.seed_icd_data
"""

import asyncio
import json
from pathlib import Path
from typing import Any, cast

from sqlalchemy import select

from src.models.database import async_session, init_db
from src.models.icd import ICDCode, ICDVersion

# 从统一的 JSON 数据文件加载 ICD 编码
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> list[dict[str, Any]]:
    path = _DATA_DIR / filename
    if not path.exists():
        print(f"WARNING: ICD data file not found: {path}")
        return []
    with open(path, encoding="utf-8") as f:
        return cast(list[dict[str, Any]], json.load(f))


ICD10_CODES: list[dict[str, Any]] = _load_json("icd_diagnoses.json")
ICD9_PROCEDURES: list[dict[str, Any]] = _load_json("icd_procedures.json")


async def seed():
    print("Initializing database...")
    await init_db()

    async with async_session() as session:
        # --- Insert ICD-10 diagnosis codes ---
        for item in ICD10_CODES:
            code = item["code"]
            existing = await session.execute(
                select(ICDCode).where(
                    ICDCode.code == code, ICDCode.version == ICDVersion.ICD10_CLINICAL
                )
            )
            if existing.scalar_one_or_none():
                continue
            session.add(
                ICDCode(
                    code=item["code"],
                    name=item["name"],
                    category=item["category"],
                    version=ICDVersion.ICD10_CLINICAL,
                    py_code=item["py"],
                    search_terms={"alias": []},
                )
            )

        # --- Insert ICD-9-CM-3 procedure codes ---
        for item in ICD9_PROCEDURES:
            code = item["code"]
            existing = await session.execute(
                select(ICDCode).where(ICDCode.code == code, ICDCode.version == ICDVersion.ICD9_CM3)
            )
            if existing.scalar_one_or_none():
                continue
            session.add(
                ICDCode(
                    code=item["code"],
                    name=item["name"],
                    category=item["category"],
                    version=ICDVersion.ICD9_CM3,
                    py_code=item["py"],
                    search_terms={"alias": []},
                )
            )

        await session.commit()

    diag_count = len(ICD10_CODES)
    proc_count = len(ICD9_PROCEDURES)
    print(
        f"Seeded {diag_count} ICD-10 diagnosis codes and {proc_count} ICD-9-CM-3 procedure codes."
    )


if __name__ == "__main__":
    asyncio.run(seed())
