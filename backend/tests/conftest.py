"""Shared fixtures for API integration tests."""
import pytest
import httpx
import asyncio

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def auth_token():
    """Login and return a valid Bearer token for test requests."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as c:
        r = await c.post("/api/v1/auth/login", data={
            "username": "admin",
            "password": "medicode2024",
        })
        assert r.status_code == 200, f"Login failed: {r.text}"
        return r.json()["access_token"]


@pytest.fixture
async def client(auth_token):
    """Async HTTP client with auth header pre-configured."""
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as c:
        c.headers["Authorization"] = f"Bearer {auth_token}"
        yield c


# Reusable test case: classic PCI+STEMI
@pytest.fixture
def pci_case():
    return {
        "record_id": 9999,
        "record_type": "discharge",
        "content": (
            "入院情况：患者因'持续性胸痛3小时'入院，伴大汗。"
            "既往有高血压病史10年，2型糖尿病史5年。"
            "体格检查：BP160/95mmHg，HR78次/分。"
            "辅助检查：ECG示V1-V4导联ST段弓背向上抬高，肌钙蛋白I升高。"
            "入院诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，原发性高血压，2型糖尿病"
            "诊疗经过：急诊行冠状动脉造影+前降支PCI术，植入药物洗脱支架1枚。"
            "出院诊断：急性心肌梗死，冠状动脉粥样硬化性心脏病，原发性高血压，2型糖尿病"
            "出院医嘱：1.阿司匹林100mg qd 2.氯吡格雷75mg qd 3.阿托伐他汀20mg qn 4.一月后复查"
        ),
    }
