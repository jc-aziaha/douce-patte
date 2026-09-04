import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def valid_payload() -> dict:
    return {
        "name": "Camille Test",
        "email": "camille@example.com",
        "phone": "0612345678",
        "service": "dog_walking",
        "message": "Une promenade tous les matins si possible.",
        "website": "",
        "recaptcha_token": "test-token",
    }


@pytest.fixture(autouse=True)
def bypass_external_services(monkeypatch: pytest.MonkeyPatch):
    """Empêche les tests de contacter Google reCAPTCHA ou un serveur SMTP réel.

    Les tests qui veulent observer/faire échouer ces appels remplacent ces
    mêmes attributs avec leur propre monkeypatch, exécuté après celui-ci.
    """
    from app.routers import contact as contact_router

    async def fake_verify(token, settings):
        return True

    async def fake_send(data, settings):
        return None

    monkeypatch.setattr(contact_router, "verify_recaptcha", fake_verify)
    monkeypatch.setattr(contact_router, "send_contact_notification", fake_send)


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Isole chaque test du limiteur de débit en mémoire (état de module)."""
    from app.routers import contact as contact_router

    contact_router._request_log.clear()
    yield
    contact_router._request_log.clear()
