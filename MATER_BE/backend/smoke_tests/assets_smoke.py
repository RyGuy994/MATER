# filepath: backend/smoke_tests/assets_smoke.py

import os
import requests


def run_assets_smoke_test(base_url: str = "http://localhost:5000") -> None:
    """
    Basic backend self-check + a few admin endpoint checks.

    - Register (or ensure) a non-admin user exists: adminmade@test.com / adminmade
    - Login as secondary user to get its user_id (needed for admin share-user)
    - Login as admin
    - Create template
    - Create asset
    - Admin checks:
        - GET /api/admin/asset-templates
        - GET /api/admin/assets
        - PUT /api/admin/asset-templates/<id>/lock
        - PUT /api/admin/assets/<id>/lock
        - POST /api/admin/assets/<id>/share-user
    """
    # Admin creds
    email = os.environ.get("SMOKE_TEST_EMAIL", "test@test.com")
    password = os.environ.get("SMOKE_TEST_PASSWORD", "test")

    # Secondary user (created via public register route)
    secondary_email = os.environ.get("SMOKE_SECONDARY_EMAIL", "adminmade@test.com")
    secondary_password = os.environ.get("SMOKE_SECONDARY_PASSWORD", "adminmade")
    secondary_username = os.environ.get("SMOKE_SECONDARY_USERNAME", "adminmade")

    # 0) Ensure secondary user exists (ignore if already exists)
    reg = requests.post(
        f"{base_url}/auth/register",
        json={"email": secondary_email, "password": secondary_password, "username": secondary_username},
        timeout=10,
    )
    if reg.status_code not in (200, 201, 400):
        reg.raise_for_status()

    # 0.5) Login secondary to get user_id
    sec_login = requests.post(
        f"{base_url}/auth/login",
        json={"email": secondary_email, "password": secondary_password},
        timeout=10,
    )
    sec_login.raise_for_status()
    sec_token = sec_login.json().get("token")
    if not sec_token:
        raise RuntimeError("Secondary login succeeded but no token returned")

    sec_me = requests.get(
        f"{base_url}/auth/me",
        headers={"Authorization": f"Bearer {sec_token}"},
        timeout=10,
    )
    sec_me.raise_for_status()
    secondary_user_id = sec_me.json()["user"]["id"]

    # 1) Login as admin
    r = requests.post(
        f"{base_url}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    r.raise_for_status()

    token = r.json().get("token")
    if not token:
        raise RuntimeError("Smoke test login succeeded but no token returned")

    headers = {"Authorization": f"Bearer {token}"}

    # 2) Create template
    tmpl_payload = {
        "name": "Car",
        "description": "Smoke Vic",
        "fields": [
            {"field_name": "make", "field_label": "Make", "field_type": "text", "is_required": True, "display_order": 1},
            {"field_name": "year", "field_label": "Year", "field_type": "number", "is_required": False, "display_order": 2},
        ],
    }

    r2 = requests.post(
        f"{base_url}/api/asset-templates",
        json=tmpl_payload,
        headers=headers,
        timeout=10,
    )
    r2.raise_for_status()
    template_id = r2.json()["id"]

    # 3) Create asset
    asset_payload = {
        "asset_template_id": template_id,
        "name": "Smoke Toyota Camry 2020",
        "template_values": {"make": "Toyota", "year": 2020},
        "custom_fields": [],
    }

    r3 = requests.post(
        f"{base_url}/api/assets",
        json=asset_payload,
        headers=headers,
        timeout=10,
    )
    r3.raise_for_status()
    asset_id = r3.json()["id"]

    # -------------------------
    # Admin endpoint checks
    # -------------------------

    a1 = requests.get(f"{base_url}/api/admin/asset-templates", headers=headers, timeout=10)
    print("ADMIN list templates:", a1.status_code)
    a1.raise_for_status()

    a2 = requests.get(f"{base_url}/api/admin/assets", headers=headers, timeout=10)
    print("ADMIN list assets:", a2.status_code)
    a2.raise_for_status()

    a3 = requests.put(
        f"{base_url}/api/admin/asset-templates/{template_id}/lock",
        json={"is_locked": True},
        headers=headers,
        timeout=10,
    )
    print("ADMIN lock template:", a3.status_code)
    a3.raise_for_status()

    a4 = requests.put(
        f"{base_url}/api/admin/assets/{asset_id}/lock",
        json={"is_locked": True},
        headers=headers,
        timeout=10,
    )
    print("ADMIN lock asset:", a4.status_code)
    a4.raise_for_status()

    a5 = requests.post(
        f"{base_url}/api/admin/assets/{asset_id}/share-user",
        json={"user_id": secondary_user_id, "role": "viewer", "days_until_expiry": 7},
        headers=headers,
        timeout=10,
    )
    print("ADMIN share-user:", a5.status_code)
    a5.raise_for_status()

    print("SMOKE (basic + admin endpoints): PASS")


def should_run_startup_smoke_tests() -> bool:
    """
    Opt-in only.
    Also avoids running twice under Flask debug reloader by checking WERKZEUG_RUN_MAIN.
    """
    enabled = os.environ.get("RUN_SMOKE_TESTS_ON_STARTUP", "0") == "1"
    if not enabled:
        return False

    werkzeug_main = os.environ.get("WERKZEUG_RUN_MAIN")
    if werkzeug_main is None:
        return True

    return werkzeug_main == "true"
