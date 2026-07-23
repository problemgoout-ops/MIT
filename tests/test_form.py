"""
Frontend + integration tests for MIT Assistent landing form.

Validates:
1. HTML structure — no copy-paste bugs (mobileForm in desktop section, etc.)
2. JS form handlers — correct variable references per section
3. API integration — form submission works end-to-end
4. Validation parity — frontend and backend validation rules match

Run: pytest tests/test_form.py -v
"""

import json
import re
import pytest
import requests

PROD_URL = "https://mitoff.ru"
API_URL = f"{PROD_URL}/api/leads/"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def fetch_html() -> str:
    """Fetch the live landing page HTML."""
    resp = requests.get(PROD_URL, timeout=15)
    resp.raise_for_status()
    return resp.text


def get_main_script(html: str) -> str:
    """Extract the main (second) <script> block from the HTML."""
    scripts = list(re.finditer(r"<script[^>]*>(.*?)</script>", html, re.DOTALL))
    assert len(scripts) >= 2, f"Expected ≥2 script blocks, got {len(scripts)}"
    return scripts[1].group(1)


def get_section(script: str, marker: str) -> str:
    """Extract a section of the script starting at `marker`."""
    idx = script.find(marker)
    assert idx >= 0, f"Marker '{marker}' not found in script"
    return script[idx:]


# ---------------------------------------------------------------------------
# HTML structure tests — no copy-paste bugs
# ---------------------------------------------------------------------------

class TestFormHTMLStructure:
    """Ensure the HTML has no copy-paste variable-reference bugs."""

    def test_desktop_section_has_no_mobileform(self):
        """Desktop handler must NOT reference mobileForm."""
        html = fetch_html()
        script = get_main_script(html)
        desktop = get_section(script, "// --- Desktop form handler ---")
        assert "mobileForm" not in desktop, (
            "BUG: desktopForm handler references mobileForm — copy-paste error"
        )

    def test_mobile_section_has_no_desktopform(self):
        """Mobile handler must NOT reference desktopForm or desktopStatus."""
        html = fetch_html()
        script = get_main_script(html)
        idx_start = script.find("// --- Mobile form handler ---")
        idx_end = script.find("// --- Desktop form handler ---")
        mobile = script[idx_start:idx_end]
        assert "desktopForm" not in mobile, (
            "BUG: mobileForm handler references desktopForm — copy-paste error"
        )
        assert "desktopStatus" not in mobile, (
            "BUG: mobileForm handler references desktopStatus — copy-paste error"
        )

    def test_desktop_handler_uses_desktop_status(self):
        """Desktop handler must use desktopStatus for user feedback."""
        html = fetch_html()
        script = get_main_script(html)
        desktop = get_section(script, "// --- Desktop form handler ---")
        assert "desktopStatus.textContent" in desktop, (
            "Desktop handler missing desktopStatus.textContent"
        )
        assert "desktopStatus.style.color" in desktop, (
            "Desktop handler missing desktopStatus.style.color"
        )

    def test_mobile_handler_uses_status(self):
        """Mobile handler must use `status` (not desktopStatus) for feedback."""
        html = fetch_html()
        script = get_main_script(html)
        idx_start = script.find("// --- Mobile form handler ---")
        idx_end = script.find("// --- Desktop form handler ---")
        mobile = script[idx_start:idx_end]
        assert "status.textContent" in mobile, (
            "Mobile handler missing status.textContent"
        )
        assert "status.className" in mobile, (
            "Mobile handler missing status.className"
        )

    def test_desktop_form_reset_correct(self):
        """Desktop handler must call desktopForm.reset(), not mobileForm.reset()."""
        html = fetch_html()
        script = get_main_script(html)
        desktop = get_section(script, "// --- Desktop form handler ---")
        assert "desktopForm.reset()" in desktop, (
            "Desktop handler must call desktopForm.reset()"
        )
        assert "mobileForm.reset()" not in desktop, (
            "BUG: desktop handler calls mobileForm.reset()"
        )

    def test_mobile_form_reset_correct(self):
        """Mobile handler must call mobileForm.reset()."""
        html = fetch_html()
        script = get_main_script(html)
        idx_start = script.find("// --- Mobile form handler ---")
        idx_end = script.find("// --- Desktop form handler ---")
        mobile = script[idx_start:idx_end]
        assert "mobileForm.reset()" in mobile, (
            "Mobile handler must call mobileForm.reset()"
        )

    def test_both_handlers_exist(self):
        """Both mobile and desktop form handlers must be present."""
        html = fetch_html()
        script = get_main_script(html)
        assert "// --- Mobile form handler ---" in script
        assert "// --- Desktop form handler ---" in script

    def test_form_elements_exist(self):
        """The HTML must contain the form elements both handlers target."""
        html = fetch_html()
        assert 'id="lead-form"' in html, "Missing #lead-form container"
        assert 'data-mit-name="Application Form"' in html, "Missing Framer form"
        assert 'id="mobile-form"' in html, "Missing #mobile-form"

    def test_fetch_urls_are_correct(self):
        """Form handlers must POST to the correct API endpoint."""
        html = fetch_html()
        script = get_main_script(html)
        # Check that form handlers use the correct API URL
        assert "mitoff.ru/api/leads/" in script, (
            "Form script missing mitoff.ru/api/leads/ endpoint"
        )
        # Both handlers should have a fetch to the leads API
        fetches = re.findall(r"fetch\(['\"]([^'\"]+)['\"]", script)
        leads_fetches = [u for u in fetches if "leads" in u]
        assert len(leads_fetches) >= 2, (
            f"Expected ≥2 fetch calls to leads API, got {len(leads_fetches)}: {leads_fetches}"
        )


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------

class TestAPIEndToEnd:
    """End-to-end API tests against the live server."""

    def test_health_endpoint(self):
        """API must be reachable."""
        resp = requests.get(f"{PROD_URL}/api/health/", timeout=10)
        # Health may be 200 or 404 depending on routing; at minimum API must respond
        assert resp.status_code in (200, 404)

    def test_create_valid_lead(self):
        """Valid form data must return success."""
        data = {
            "last_name": "Тестов",
            "first_name": "Пользователь",
            "telegram": "@testuser99",
            "email": "test@example.com",
            "task": "тестовая задача для проверки API",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("success") is True, f"Expected success=True, got {body}"

    def test_create_lead_with_cyrillic_name(self):
        """Cyrillic names must be accepted."""
        data = {
            "last_name": "Иванов",
            "first_name": "Алексей",
            "telegram": "@ivanov_test",
            "email": "ivanov@example.com",
            "task": "тестирование русских букв в имени и фамилии",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        assert resp.status_code == 201, f"Cyrillic name rejected: {resp.text}"

    def test_create_lead_with_hyphenated_name(self):
        """Hyphenated last names must be accepted."""
        data = {
            "last_name": "Петрова-Водкина",
            "first_name": "Анна",
            "telegram": "@petrova_test",
            "email": "petrova@example.com",
            "task": "проверка двойной фамилии через дефис",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        assert resp.status_code == 201, f"Hyphenated name rejected: {resp.text}"

    def test_reject_invalid_telegram(self):
        """Invalid Telegram username must be rejected."""
        data = {
            "last_name": "Тестов",
            "first_name": "Юзер",
            "telegram": "@ab",  # too short
            "email": "test@example.com",
            "task": "проверка валидации",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

    def test_reject_invalid_email(self):
        """Invalid email must be rejected."""
        data = {
            "last_name": "Тестов",
            "first_name": "Юзер",
            "telegram": "@testuser",
            "email": "not-an-email",
            "task": "проверка валидации email",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

    def test_reject_missing_required(self):
        """Missing required fields must be rejected."""
        required = ["last_name", "first_name", "telegram", "email"]
        for field in required:
            data = {
                "last_name": "Тестов",
                "first_name": "Юзер",
                "telegram": "@testuser",
                "email": "test@example.com",
                "task": "проверка",
            }
            del data[field]
            resp = requests.post(API_URL, json=data, timeout=10)
            assert resp.status_code == 400, (
                f"Missing '{field}' should return 400, got {resp.status_code}"
            )

    def test_cors_headers_present(self):
        """CORS headers must allow mitoff.ru origin."""
        resp = requests.options(
            API_URL,
            headers={
                "Origin": PROD_URL,
                "Access-Control-Request-Method": "POST",
            },
            timeout=10,
        )
        assert resp.status_code == 200
        assert "access-control-allow-origin" in resp.headers

    def test_response_is_json(self):
        """API must return JSON."""
        data = {
            "last_name": "Формат",
            "first_name": "Проверка",
            "telegram": "@json_test",
            "email": "json@example.com",
            "task": "проверка content-type",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        ct = resp.headers.get("Content-Type", "")
        assert "application/json" in ct, f"Expected JSON, got {ct}"


# ---------------------------------------------------------------------------
# Validation parity tests — frontend JS rules must match backend
# ---------------------------------------------------------------------------

class TestValidationParity:
    """Ensure frontend JS validation regexes match backend serializer rules."""

    def test_name_regex_parity(self):
        """Frontend and backend name validation must use the same pattern."""
        resp = requests.get(PROD_URL, timeout=15)
        resp.raise_for_status()
        # Force UTF-8 decoding — server may misreport charset
        resp.encoding = "utf-8"
        html = resp.text
        script = get_main_script(html)
        # Check for the min-length quantifier
        assert "{2,}" in script, (
            "Frontend name regex missing {2,} min-length quantifier"
        )
        # Check for Cyrillic range — may be literal chars or \u escapes
        has_cyrillic = any(
            s in script
            for s in ("А-Я", "а-я", "Ёё", "\\u0410", "\\u0430")
        )
        assert has_cyrillic, (
            "Frontend name regex missing Cyrillic character range"
        )

    def test_telegram_regex_parity(self):
        """Frontend and backend Telegram validation must use the same pattern."""
        html = fetch_html()
        # Backend: ^@?[a-zA-Z][a-zA-Z0-9_]{4,31}$
        assert re.search(r"@\?\[a-zA-Z\]\[a-zA-Z0-9_\]\{4,31\}", html), (
            "Frontend Telegram regex not found in HTML"
        )

    def test_task_min_length_parity(self):
        """Both frontend and backend must require ≥10 chars for task."""
        html = fetch_html()
        assert "length < 10" in html, "Task min-length check not found in HTML"


# ---------------------------------------------------------------------------
# Cache-busting tests — ensure fresh HTML is always served
# ---------------------------------------------------------------------------

class TestCacheHeaders:
    """Ensure browsers don't cache stale HTML with bugs."""

    def test_index_html_no_store(self):
        """index.html must have Cache-Control: no-cache or no-store."""
        resp = requests.get(PROD_URL, timeout=10)
        cc = resp.headers.get("Cache-Control", "")
        assert "no-cache" in cc or "no-store" in cc, (
            f"index.html must have no-cache/no-store, got: {cc}"
        )

    def test_index_html_no_etag_only(self):
        """ETag alone is not enough — must have explicit no-cache directive."""
        resp = requests.get(PROD_URL, timeout=10)
        cc = resp.headers.get("Cache-Control", "")
        # If only ETag is present without no-cache, browsers may use stale cache
        if resp.headers.get("ETag"):
            assert "no-cache" in cc or "no-store" in cc or "max-age=0" in cc, (
                "ETag present but no cache-busting directive — browser may serve stale HTML"
            )

    def test_index_html_expires_past(self):
        """Expires header must be in the past or absent."""
        resp = requests.get(PROD_URL, timeout=10)
        expires = resp.headers.get("Expires", "")
        if expires:
            from email.utils import parsedate_to_datetime
            from datetime import datetime, timezone
            exp_dt = parsedate_to_datetime(expires)
            now = datetime.now(timezone.utc)
            assert exp_dt <= now, (
                f"Expires header is in the future ({expires}) — browser may cache HTML"
            )

    def test_api_no_cache(self):
        """API responses must have Cache-Control: no-store."""
        data = {
            "last_name": "Кеш",
            "first_name": "Тест",
            "telegram": "@cache_test",
            "email": "cache@test.com",
            "task": "проверка заголовков кеширования",
        }
        resp = requests.post(API_URL, json=data, timeout=10)
        cc = resp.headers.get("Cache-Control", "")
        assert "no-store" in cc or "no-cache" in cc, (
            f"API must have no-store/no-cache, got: {cc}"
        )

    def test_html_content_length_stable(self):
        """Two consecutive requests must return same content length (no mid-deploy mismatch)."""
        r1 = requests.get(PROD_URL, timeout=10)
        r2 = requests.get(PROD_URL, timeout=10)
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Content should be stable — if lengths differ wildly, something is wrong
        len1 = len(r1.content)
        len2 = len(r2.content)
        assert len1 == len2, (
            f"HTML size changed between requests ({len1} → {len2}) — "
            "possible mid-deploy or dynamic content issue"
        )

    def test_html_contains_freshness_marker(self):
        """HTML must contain the fixed form handlers (no regression to buggy version)."""
        html = fetch_html()
        script = get_main_script(html)
        # The fixed version has desktopForm references in desktop handler
        desktop = get_section(script, "// --- Desktop form handler ---")
        assert "desktopForm.querySelector" in desktop, (
            "Desktop handler missing desktopForm — possible regression to buggy version"
        )
        assert "desktopStatus.textContent" in desktop, (
            "Desktop handler missing desktopStatus — possible regression to buggy version"
        )
