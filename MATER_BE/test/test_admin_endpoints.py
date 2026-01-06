# filepath: tests/test_admin_endpoints.py
from backend.seed import ensure_test_admin


def _register_user(client, email: str, password: str, username: str):
    return client.post(
        "/auth/register",
        json={"email": email, "password": password, "username": username},
    )


def _login(client, email: str, password: str) -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.get_data(as_text=True)
    data = resp.get_json() or {}
    token = data.get("token")
    assert token, f"Login returned no token: {data}"
    return token


def test_admin_requires_auth(client):
    resp = client.get("/api/admin/asset-templates")
    assert resp.status_code == 401, resp.get_data(as_text=True)


def test_admin_forbidden_for_non_admin(client, app):
    # Create a normal user
    r = _register_user(client, "user1@test.com", "pass123", "user1")
    assert r.status_code in (200, 201, 400), r.get_data(as_text=True)

    token = _login(client, "user1@test.com", "pass123")

    resp = client.get(
        "/api/admin/asset-templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403, resp.get_data(as_text=True)


def test_admin_ok_for_admin(client, app):
    # Ensure seeded admin exists in the test DB
    with app.app_context():
        ensure_test_admin()

    token = _login(client, "test@test.com", "test")

    resp = client.get(
        "/api/admin/asset-templates",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.get_data(as_text=True)
