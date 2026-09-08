def test_honeypot_filled_is_rejected_without_sending_email(client, valid_payload, monkeypatch):
    from app.routers import contact as contact_router

    called = False

    async def fake_send(data, settings):
        nonlocal called
        called = True

    monkeypatch.setattr(contact_router, "send_contact_notification", fake_send)

    payload = {**valid_payload, "website": "http://spam.example"}
    response = client.post("/contact", json=payload)

    assert response.status_code == 400
    assert called is False


def test_recaptcha_failure_is_rejected(client, valid_payload, monkeypatch):
    from app.routers import contact as contact_router

    async def fake_verify(token, settings):
        return False

    monkeypatch.setattr(contact_router, "verify_recaptcha", fake_verify)

    response = client.post("/contact", json=valid_payload)

    assert response.status_code == 400


def test_valid_submission_sends_email_and_returns_200(client, valid_payload, monkeypatch):
    from app.routers import contact as contact_router

    sent = {}

    async def fake_send(data, settings):
        sent["email"] = data.email
        sent["service"] = data.service

    monkeypatch.setattr(contact_router, "send_contact_notification", fake_send)

    response = client.post("/contact", json=valid_payload)

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert sent["email"] == valid_payload["email"]
    assert sent["service"] == "dog_walking"


def test_email_send_failure_returns_502(client, valid_payload, monkeypatch):
    from app.routers import contact as contact_router

    async def failing_send(data, settings):
        raise RuntimeError("SMTP down")

    monkeypatch.setattr(contact_router, "send_contact_notification", failing_send)

    response = client.post("/contact", json=valid_payload)

    assert response.status_code == 502


def test_rate_limit_blocks_excessive_requests(client, valid_payload):
    for _ in range(5):
        assert client.post("/contact", json=valid_payload).status_code == 200

    response = client.post("/contact", json=valid_payload)

    assert response.status_code == 429


def test_rate_limit_is_scoped_per_ip(client, valid_payload, monkeypatch):
    from app.routers import contact as contact_router

    for _ in range(5):
        client.post("/contact", json=valid_payload)
    assert client.post("/contact", json=valid_payload).status_code == 429

    monkeypatch.setattr(contact_router, "_client_ip", lambda request: "203.0.113.9")

    assert client.post("/contact", json=valid_payload).status_code == 200


def test_rate_limit_ignores_client_supplied_leftmost_forwarded_ip(client, valid_payload):
    """Le premier maillon de X-Forwarded-For vient du client : le falsifier
    (une IP différente à chaque requête) ne doit pas permettre de contourner
    la limite de débit — seul le dernier maillon (ajouté par Render) compte.
    """
    for i in range(5):
        response = client.post(
            "/contact",
            json=valid_payload,
            headers={"x-forwarded-for": f"203.0.113.{i}, 198.51.100.7"},
        )
        assert response.status_code == 200

    response = client.post(
        "/contact",
        json=valid_payload,
        headers={"x-forwarded-for": "203.0.113.250, 198.51.100.7"},
    )

    assert response.status_code == 429
