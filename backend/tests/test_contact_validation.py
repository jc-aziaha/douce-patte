def test_missing_required_field_returns_422(client, valid_payload):
    payload = dict(valid_payload)
    del payload["email"]

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_invalid_email_returns_422(client, valid_payload):
    payload = {**valid_payload, "email": "not-an-email"}

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_invalid_service_returns_422(client, valid_payload):
    payload = {**valid_payload, "service": "unknown_service"}

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_name_too_short_returns_422(client, valid_payload):
    payload = {**valid_payload, "name": "A"}

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_phone_too_short_returns_422(client, valid_payload):
    payload = {**valid_payload, "phone": "123"}

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_name_with_newline_returns_422(client, valid_payload):
    payload = {**valid_payload, "name": "Camille\r\nBcc: attacker@evil.example"}

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_phone_with_newline_returns_422(client, valid_payload):
    payload = {**valid_payload, "phone": "0612345678\r\nX-Injected: 1"}

    response = client.post("/contact", json=payload)

    assert response.status_code == 422


def test_message_is_optional(client, valid_payload):
    payload = dict(valid_payload)
    del payload["message"]

    response = client.post("/contact", json=payload)

    assert response.status_code == 200


def test_blank_message_is_treated_as_absent(client, valid_payload):
    payload = {**valid_payload, "message": "   "}

    response = client.post("/contact", json=payload)

    assert response.status_code == 200


def test_fields_are_stripped_of_surrounding_whitespace(client, valid_payload, monkeypatch):
    from app.routers import contact as contact_router

    captured = {}

    async def fake_send(data, settings):
        captured["name"] = data.name
        captured["phone"] = data.phone

    monkeypatch.setattr(contact_router, "send_contact_notification", fake_send)

    payload = {**valid_payload, "name": "  Camille Test  ", "phone": "  0612345678  "}
    response = client.post("/contact", json=payload)

    assert response.status_code == 200
    assert captured["name"] == "Camille Test"
    assert captured["phone"] == "0612345678"
