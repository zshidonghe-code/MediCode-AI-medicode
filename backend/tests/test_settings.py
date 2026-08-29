"""Production configuration safety checks."""
import pytest
from pydantic import ValidationError

from src.config.settings import Settings


def test_production_requires_strong_demo_passwords():
    with pytest.raises(ValidationError, match="at least 12 characters"):
        Settings(
            debug=False,
            secret_key="x" * 64,
            demo_admin_password="",
            demo_coder_password="short",
            demo_doctor_password="another-short",
        )


def test_production_requires_a_long_secret_key():
    with pytest.raises(ValidationError, match="SECRET_KEY must be at least 32 characters"):
        Settings(
            debug=False,
            secret_key="short-secret",
            demo_admin_password="valid-production-password",
            demo_coder_password="valid-production-password",
            demo_doctor_password="valid-production-password",
        )


def test_debug_mode_keeps_demo_defaults():
    settings = Settings(
        debug=True,
        secret_key="debug-secret",
        demo_admin_password="",
        demo_coder_password="",
        demo_doctor_password="",
    )

    assert settings.demo_admin_password == "123456"
    assert settings.demo_coder_password == "123456"
    assert settings.demo_doctor_password == "123456"
