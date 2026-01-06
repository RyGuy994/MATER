# filepath: backend/smoke_tests/assets_smoke.py

import os
import requests


def run_assets_smoke_test(base_url: str = "http://localhost:5000") -> None:
    """
    Basic backend self-check + a few admin endpoint checks.

    - Register (or ensure) a non-admin user exists: [adminmade@test.com](mailto:adminmade@test.com) / adminmade
    - Login as secondary user to get its user_id (needed for admin share-user)
    - Login as admin
    - Create template
    - Create asset
    - TEST DROPDOWN FIELDS:
        - Create field with single-select dropdown
        - Create field with multi-select dropdown
        - Create asset with dropdown values
        - Update dropdown options
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

    # ===================================================================
    # NEW: TEST DROPDOWN FIELDS
    # ===================================================================

    # 2.5) Create single-select dropdown field
    single_select_field = {
        "field_name": "status",
        "field_label": "Vehicle Status",
        "field_type": "select",
        "select_type": "single",
        "is_required": True,
        "display_order": 3,
        "options": [
            {"label": "Active", "value": "active"},
            {"label": "Inactive", "value": "inactive"},
            {"label": "Sold", "value": "sold"},
        ],
    }

    r_single = requests.post(
        f"{base_url}/api/asset-templates/{template_id}/fields",
        json=single_select_field,
        headers=headers,
        timeout=10,
    )
    r_single.raise_for_status()
    single_field_id = r_single.json()["id"]
    print("CREATE single-select field:", r_single.status_code)

    # 2.6) Create multi-select dropdown field
    multi_select_field = {
        "field_name": "colors",
        "field_label": "Available Colors",
        "field_type": "select",
        "select_type": "multi",
        "is_required": False,
        "display_order": 4,
        "options": [
            {"label": "Red", "value": "red"},
            {"label": "Blue", "value": "blue"},
            {"label": "Green", "value": "green"},
            {"label": "Black", "value": "black"},
        ],
    }

    r_multi = requests.post(
        f"{base_url}/api/asset-templates/{template_id}/fields",
        json=multi_select_field,
        headers=headers,
        timeout=10,
    )
    r_multi.raise_for_status()
    multi_field_id = r_multi.json()["id"]
    print("CREATE multi-select field:", r_multi.status_code)

    # 2.7) Update dropdown options
    updated_options = {
        "options": [
            {"label": "Active", "value": "active"},
            {"label": "Inactive", "value": "inactive"},
            {"label": "Sold", "value": "sold"},
            {"label": "Archived", "value": "archived"},
        ]
    }

    r_update_opts = requests.put(
        f"{base_url}/api/asset-templates/{template_id}/fields/{single_field_id}/options",
        json=updated_options,
        headers=headers,
        timeout=10,
    )
    
    # ADD THIS DEBUG OUTPUT:
    if r_update_opts.status_code != 200:
        print(f"UPDATE options response: {r_update_opts.status_code}")
        print(f"Response body: {r_update_opts.text}")
        print(f"Response JSON: {r_update_opts.json()}")
    
    r_update_opts.raise_for_status()
    print("UPDATE dropdown options:", r_update_opts.status_code)

    # 2.8) Get dropdown field options
    r_get_opts = requests.get(
        f"{base_url}/api/asset-templates/{template_id}/fields/{single_field_id}/options",
        headers=headers,
        timeout=10,
    )
    r_get_opts.raise_for_status()
    print("GET dropdown options:", r_get_opts.status_code)

    # 3) Create asset WITH DROPDOWN VALUES
    asset_payload = {
        "asset_template_id": template_id,
        "name": "Smoke Toyota Camry 2020",
        "template_values": {
            "make": "Toyota",
            "year": 2020,
            "status": "active",
            "colors": ["red", "blue"],
        },
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
    print("CREATE asset with dropdowns:", r3.status_code)

    # 3.5) Verify asset has dropdown values
    r_get_asset = requests.get(
        f"{base_url}/api/assets/{asset_id}",
        headers=headers,
        timeout=10,
    )
    r_get_asset.raise_for_status()
    asset_data = r_get_asset.json()
    assert asset_data["template_values"]["status"] == "active", "Single-select value mismatch"
    assert asset_data["template_values"]["colors"] == ["red", "blue"], "Multi-select value mismatch"
    print("VERIFY asset dropdown values:", r_get_asset.status_code)

    # 3.6) List fields in template (should include dropdowns)
    r_list_fields = requests.get(
        f"{base_url}/api/asset-templates/{template_id}/fields",
        headers=headers,
        timeout=10,
    )
    r_list_fields.raise_for_status()
    fields = r_list_fields.json()
    assert len(fields) == 4, f"Expected 4 fields, got {len(fields)}"
    print("LIST template fields:", r_list_fields.status_code)

    # 3.7) Get single field
    r_get_field = requests.get(
        f"{base_url}/api/asset-templates/{template_id}/fields/{single_field_id}",
        headers=headers,
        timeout=10,
    )
    r_get_field.raise_for_status()
    field_data = r_get_field.json()
    assert field_data["field_type"] == "select", "Field type should be select"
    assert field_data["select_type"] == "single", "Select type should be single"
    assert len(field_data["options"]) == 4, "Should have 4 options after update"
    print("GET field with dropdowns:", r_get_field.status_code)

    # 3.8) Update field label
    r_update_field = requests.put(
        f"{base_url}/api/asset-templates/{template_id}/fields/{single_field_id}",
        json={"field_label": "Current Vehicle Status"},
        headers=headers,
        timeout=10,
    )
    r_update_field.raise_for_status()
    print("UPDATE field definition:", r_update_field.status_code)

    # ===================================================================
    # EXISTING: Admin endpoint checks
    # ===================================================================

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

    print("\n✅ SMOKE (basic + admin + dropdown fields): PASS")


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
