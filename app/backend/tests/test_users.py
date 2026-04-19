"""Tests endpoints /users/ — RBAC & opérations CRUD."""
import pytest


# ── /users/me ──────────────────────────────────────────────────────────────

def test_me_admin(client, admin_token):
    r = client.get("/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "admin@test.dev"
    assert body["role"] == "admin"
    assert body["is_active"] is True


def test_me_user(client, user_token):
    r = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "user"


def test_me_no_token(client):
    r = client.get("/users/me")
    assert r.status_code == 403  # HTTPBearer renvoie 403 si absent


def test_me_invalid_token(client):
    r = client.get("/users/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert r.status_code == 401


# ── GET /users/ (admin only) ───────────────────────────────────────────────

def test_list_users_admin(client, admin_token):
    r = client.get("/users/", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "admin@test.dev" in emails
    assert "user@test.dev" in emails


def test_list_users_forbidden_for_user(client, user_token):
    r = client.get("/users/", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403


# ── POST /users/ (admin only) ──────────────────────────────────────────────

def test_create_user_admin(client, admin_token):
    r = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "new@test.dev", "password": "NewPass1!", "role_id": 2},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "new@test.dev"
    assert body["role"] == "user"
    assert body["is_active"] is True


def test_create_user_duplicate_email(client, admin_token):
    client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "dup@test.dev", "password": "NewPass1!", "role_id": 2},
    )
    r = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "dup@test.dev", "password": "NewPass1!", "role_id": 2},
    )
    assert r.status_code == 409


def test_create_user_forbidden_for_user(client, user_token):
    r = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"email": "x@test.dev", "password": "Pass1234!", "role_id": 2},
    )
    assert r.status_code == 403


def test_create_user_invalid_role(client, admin_token):
    r = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "norl@test.dev", "password": "Pass1234!", "role_id": 999},
    )
    assert r.status_code == 404


# ── DELETE /users/{id} (admin only) ───────────────────────────────────────

def test_delete_user_admin(client, admin_token):
    # Créer un user à supprimer
    r = client.post(
        "/users/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": "todel@test.dev", "password": "ToDel1!", "role_id": 2},
    )
    user_id = r.json()["id_user"]

    r = client.delete(
        f"/users/{user_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 204


def test_delete_self_forbidden(client, admin_token):
    me = client.get("/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    my_id = me.json()["id_user"]

    r = client.delete(
        f"/users/{my_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 400


def test_delete_user_forbidden_for_user(client, user_token):
    r = client.delete("/users/1", headers={"Authorization": f"Bearer {user_token}"})
    assert r.status_code == 403
