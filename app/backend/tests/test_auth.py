"""Tests endpoint /auth/login."""


def test_login_success_admin(client):
    r = client.post("/auth/login", json={"email": "admin@test.dev", "password": "Admin1234!"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_login_success_user(client):
    r = client.post("/auth/login", json={"email": "user@test.dev", "password": "User1234!"})
    assert r.status_code == 200


def test_login_wrong_password(client):
    r = client.post("/auth/login", json={"email": "admin@test.dev", "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Identifiants incorrects"


def test_login_unknown_email(client):
    r = client.post("/auth/login", json={"email": "ghost@test.dev", "password": "whatever"})
    # Même message — protection contre l'énumération (OWASP)
    assert r.status_code == 401
    assert r.json()["detail"] == "Identifiants incorrects"


def test_login_inactive_account(client):
    r = client.post("/auth/login", json={"email": "inactive@test.dev", "password": "Inactive1!"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Compte désactivé"


def test_login_invalid_email_format(client):
    r = client.post("/auth/login", json={"email": "not-an-email", "password": "Admin1234!"})
    assert r.status_code == 422  # validation Pydantic
