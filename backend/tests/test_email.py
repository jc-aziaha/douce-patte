import pytest

from app.config import Settings
from app.schemas import ContactFields, ServiceType
from app.services import email as email_module


@pytest.fixture
def settings() -> Settings:
    return Settings(
        from_email="Douce Patte <contact@douce-patte.fr>",
        notify_email="manon@example.com",
    )


@pytest.fixture
def fields() -> ContactFields:
    return ContactFields(
        name="Camille Test",
        email="camille@example.com",
        phone="0612345678",
        service=ServiceType.DOG_WALKING,
        message="Une promenade tous les matins si possible.",
    )


async def test_sends_with_expected_headers_and_content(monkeypatch, settings, fields):
    captured = {}

    async def fake_send(message, **kwargs):
        captured["message"] = message
        captured["kwargs"] = kwargs

    monkeypatch.setattr(email_module.aiosmtplib, "send", fake_send)

    await email_module.send_contact_notification(fields, settings)

    message = captured["message"]
    assert message["To"] == settings.notify_email
    assert message["From"] == settings.from_email
    assert message["Reply-To"] == fields.email
    assert "Promenade de chiens" in message["Subject"]

    text_body = message.get_body(("plain",)).get_content()
    assert "Bonjour Manon" in text_body
    assert "Camille Test" in text_body
    assert "camille@example.com" in text_body
    assert "promenade tous les matins" in text_body

    html_body = message.get_body(("html",)).get_content()
    assert "Camille Test" in html_body
    assert "Promenade de chiens" in html_body
    assert "promenade tous les matins" in html_body

    assert captured["kwargs"]["hostname"] == settings.smtp_host
    assert captured["kwargs"]["port"] == settings.smtp_port


async def test_missing_message_uses_fallback_sentence(monkeypatch, settings, fields):
    fields = fields.model_copy(update={"message": None})
    captured = {}

    async def fake_send(message, **kwargs):
        captured["message"] = message

    monkeypatch.setattr(email_module.aiosmtplib, "send", fake_send)

    await email_module.send_contact_notification(fields, settings)

    message = captured["message"]
    assert "n'a pas laissé de message" in message.get_body(("plain",)).get_content()
    assert "n'a pas laissé de message" in message.get_body(("html",)).get_content()
