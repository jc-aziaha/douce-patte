import httpx
import pytest

from app.config import Settings
from app.services.recaptcha import verify_recaptcha


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict):
        self._payload = payload

    async def __aenter__(self) -> "_FakeClient":
        return self

    async def __aexit__(self, *exc_info) -> bool:
        return False

    async def post(self, url: str, data: dict) -> _FakeResponse:
        return _FakeResponse(self._payload)


def _patch_client(monkeypatch: pytest.MonkeyPatch, payload: dict) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", lambda timeout=5.0: _FakeClient(payload))


async def test_bypassed_when_secret_key_missing_outside_production():
    settings = Settings(recaptcha_secret_key="", environment="development")

    assert await verify_recaptcha("any-token", settings) is True


async def test_rejected_when_secret_key_missing_in_production():
    settings = Settings(recaptcha_secret_key="", environment="production")

    assert await verify_recaptcha("any-token", settings) is False


async def test_rejects_missing_token_when_configured():
    settings = Settings(recaptcha_secret_key="secret")

    assert await verify_recaptcha(None, settings) is False


async def test_accepts_high_score_matching_action(monkeypatch):
    settings = Settings(recaptcha_secret_key="secret", recaptcha_min_score=0.5)
    _patch_client(monkeypatch, {"success": True, "score": 0.9, "action": "contact"})

    assert await verify_recaptcha("token", settings) is True


async def test_rejects_low_score(monkeypatch):
    settings = Settings(recaptcha_secret_key="secret", recaptcha_min_score=0.5)
    _patch_client(monkeypatch, {"success": True, "score": 0.1, "action": "contact"})

    assert await verify_recaptcha("token", settings) is False


async def test_rejects_mismatched_action(monkeypatch):
    settings = Settings(recaptcha_secret_key="secret", recaptcha_min_score=0.5)
    _patch_client(monkeypatch, {"success": True, "score": 0.9, "action": "login"})

    assert await verify_recaptcha("token", settings) is False


async def test_rejects_unsuccessful_response(monkeypatch):
    settings = Settings(recaptcha_secret_key="secret", recaptcha_min_score=0.5)
    _patch_client(monkeypatch, {"success": False, "score": 0.9, "action": "contact"})

    assert await verify_recaptcha("token", settings) is False
