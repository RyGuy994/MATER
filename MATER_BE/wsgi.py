# filepath: wsgi.py
import os
import threading
import time
import urllib.request
import urllib.error

from backend import create_app
from backend.models.user import db, User
from backend.seed import ensure_test_admin

app = create_app()


def _should_run_smoke_tests_on_startup() -> bool:
    """
    Opt-in only, controlled by env var.

    Also avoids running twice under Flask debug reloader.
    """
    if os.environ.get("RUN_SMOKE_TESTS_ON_STARTUP", "0") != "1":
        return False

    if "WERKZEUG_RUN_MAIN" in os.environ:
        return os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    return True


def _wait_for_http(url: str, timeout_seconds: int = 30) -> None:
    """
    Wait until an HTTP endpoint is reachable (or raise TimeoutError).

    IMPORTANT:
    - urllib raises HTTPError for non-2xx (like 401).
    - For our purposes, 401 still proves the server is up and accepting connections,
      so we treat HTTPError as success.
    """
    start = time.time()
    last_err = None

    while time.time() - start < timeout_seconds:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                _ = resp.read()
                return
        except urllib.error.HTTPError:
            # Server is reachable; endpoint returned an HTTP status like 401.
            return
        except Exception as e:
            last_err = e
            time.sleep(0.5)

    raise TimeoutError(
        f"Server not reachable at {url} after {timeout_seconds}s. Last error: {last_err}"
    )


def _run_startup_smoke_tests_async():
    """
    Runs in a background thread AFTER the server is listening.
    """
    try:
        base_url = os.environ.get("SMOKE_TEST_BASE_URL", "http://127.0.0.1:5000")

        # /auth/me is a GET endpoint; it may return 401, which is fine for readiness.
        _wait_for_http(f"{base_url}/auth/me", timeout_seconds=45)

        from backend.smoke_tests.assets_smoke import run_assets_smoke_test

        run_assets_smoke_test(base_url=base_url)
        print("SMOKE TESTS: PASS")
    except Exception as e:
        print(f"SMOKE TESTS: FAIL: {e}")


# Auto-seed test user on startup (idempotent)
with app.app_context():
    ensure_test_admin()
    print("✓ Test user ensured admin: test@test.com / test")


# Kick off smoke tests in background (only if enabled)
if _should_run_smoke_tests_on_startup():
    t = threading.Thread(target=_run_startup_smoke_tests_async, daemon=True)
    t.start()


@app.shell_context_processor
def make_shell_context():
    """Provides objects to `flask shell` command."""
    return {"db": db, "User": User}


@app.cli.command("seed-db")
def seed_db():
    """Seed the database with test data (manual)."""
    with app.app_context():
        ensure_test_admin()
        print("✓ Test user ensured (admin): test@test.com / test")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
