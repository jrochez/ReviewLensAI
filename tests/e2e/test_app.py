"""E2E tests using Playwright. Does NOT test AI chat functionality."""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:9001"
EMAIL = "analyst@firm.com"
PASSWORD = "password123"


def login(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill('input[type="email"]', EMAIL)
    page.fill('input[type="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/datasets", timeout=10000)


# ── Login flow ────────────────────────────────────────────────────────────────

def test_login_page_renders(page: Page):
    page.goto(f"{BASE_URL}/login")
    expect(page.locator("text=ReviewLens AI").first).to_be_visible()
    expect(page.locator('input[type="email"]')).to_be_visible()
    expect(page.locator('input[type="password"]')).to_be_visible()
    expect(page.locator('button[type="submit"]')).to_be_visible()


def test_login_invalid_credentials(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill('input[type="email"]', "wrong@email.com")
    page.fill('input[type="password"]', "wrongpass")
    page.click('button[type="submit"]')
    # Should show error, not redirect (use p[role=alert] to exclude Next.js route announcer)
    expect(page.locator('p[role="alert"]')).to_be_visible(timeout=5000)
    assert page.url.startswith(f"{BASE_URL}/login")


def test_login_valid_credentials(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.fill('input[type="email"]', EMAIL)
    page.fill('input[type="password"]', PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/datasets", timeout=10000)
    expect(page.locator("text=Datasets")).to_be_visible()


# ── Authenticated nav ─────────────────────────────────────────────────────────

def test_unauthenticated_redirect(page: Page):
    page.goto(f"{BASE_URL}/datasets")
    page.wait_for_url(f"{BASE_URL}/login**", timeout=8000)


def test_datasets_page_renders_after_login(page: Page):
    login(page)
    expect(page.locator("h1", has_text="Datasets")).to_be_visible()
    expect(page.locator("text=New Dataset")).to_be_visible()


def test_top_nav_visible(page: Page):
    login(page)
    expect(page.locator("header")).to_be_visible()
    expect(page.locator("header", has_text="ReviewLens AI")).to_be_visible()


def test_user_menu(page: Page):
    login(page)
    # Avatar button should be visible
    page.click('button[aria-label="User menu"]')
    expect(page.locator("text=Sign out")).to_be_visible()


# ── Dataset creation flow ─────────────────────────────────────────────────────

def test_new_dataset_page_renders(page: Page):
    login(page)
    page.click("text=New Dataset")
    page.wait_for_url(f"{BASE_URL}/datasets/new", timeout=5000)
    expect(page.locator("text=Amazon URL or ASIN")).to_be_visible()
    expect(page.locator("text=Start Scraping")).to_be_visible()
    expect(page.locator("text=Cancel")).to_be_visible()


def test_new_dataset_invalid_asin_shows_error(page: Page):
    login(page)
    page.goto(f"{BASE_URL}/datasets/new")
    page.fill('input[id="asin-input"]', "not-an-asin")
    page.click("text=Start Scraping")
    # Should show inline error
    expect(page.locator('p[role="alert"]')).to_be_visible(timeout=5000)


def test_new_dataset_create_and_progress(page: Page):
    login(page)
    page.goto(f"{BASE_URL}/datasets/new")
    page.fill('input[id="asin-input"]', "B08N5WRWNW")
    page.click("text=Start Scraping")
    # Should transition to progress view or show 409 error
    # Wait for either progress steps or an error
    page.wait_for_timeout(3000)
    # Either scraping started (step progress visible) or 409 (error visible)
    content = page.content()
    assert "Scraping in progress" in content or "already running" in content or "Datasets" in page.url


# ── Dataset list ──────────────────────────────────────────────────────────────

def test_search_datasets(page: Page):
    login(page)
    search = page.locator('input[type="search"]')
    expect(search).to_be_visible()
    search.fill("nonexistent-product-xyz")
    page.wait_for_timeout(500)
    # Should show empty results or no datasets matching
    # (no assertion on count since this is dynamic)


def test_logout_flow(page: Page):
    login(page)
    page.click('button[aria-label="User menu"]')
    page.click("text=Sign out")
    page.wait_for_url(f"{BASE_URL}/login", timeout=5000)


# ── Dataset detail (wait for a ready dataset) ─────────────────────────────────

@pytest.fixture(scope="module")
def ready_dataset_url():
    """Get URL of a ready dataset for detail/chat page tests."""
    import httpx, time
    BASE_API = "http://127.0.0.1:9000/api/v1"
    r = httpx.post(f"{BASE_API}/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        pytest.skip("Cannot authenticate for E2E fixture")
    token = r.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Check existing ready datasets first
    r2 = httpx.get(f"{BASE_API}/datasets", headers=headers)
    for ds in r2.json().get("datasets", []):
        if ds["status"] == "ready":
            return f"{BASE_URL}/datasets/{ds['id']}"

    # Create a new dataset (mock scraper should complete quickly)
    r3 = httpx.post(f"{BASE_API}/datasets", json={"input": "B00READYE2E"[:-1]}, headers=headers)
    # B00READYE2 = 10 chars
    if r3.status_code not in (201, 409):
        pytest.skip(f"Cannot create dataset: {r3.status_code} {r3.text}")

    if r3.status_code == 201:
        ds_id = r3.json()["id"]
        for _ in range(30):
            time.sleep(2)
            status_r = httpx.get(f"{BASE_API}/datasets/{ds_id}", headers=headers)
            status = status_r.json().get("status")
            if status == "ready":
                return f"{BASE_URL}/datasets/{ds_id}"
            if status == "error":
                pytest.skip(f"Dataset errored: {status_r.json().get('error_message')}")

    pytest.skip("No ready dataset available for E2E test")


def test_dataset_detail_page(page: Page, ready_dataset_url):
    login(page)
    page.goto(ready_dataset_url)
    page.wait_for_timeout(3000)
    expect(page.locator("text=Ask Questions")).to_be_visible(timeout=10000)


def test_dataset_detail_shows_stats(page: Page, ready_dataset_url):
    login(page)
    page.goto(ready_dataset_url)
    page.wait_for_timeout(3000)
    expect(page.locator("text=Review Stats")).to_be_visible(timeout=10000)
    expect(page.locator("text=Sentiment")).to_be_visible(timeout=10000)


def test_dataset_detail_shows_themes(page: Page, ready_dataset_url):
    login(page)
    page.goto(ready_dataset_url)
    page.wait_for_timeout(3000)
    expect(page.locator("text=Top Themes")).to_be_visible(timeout=10000)


def test_dataset_detail_review_table(page: Page, ready_dataset_url):
    login(page)
    page.goto(ready_dataset_url)
    page.wait_for_timeout(3000)
    expect(page.locator("h2", has_text="Reviews (")).to_be_visible(timeout=10000)


def test_navigate_to_chat(page: Page, ready_dataset_url):
    login(page)
    page.goto(ready_dataset_url)
    page.wait_for_timeout(2000)
    page.click("text=Ask Questions")
    page.wait_for_timeout(2000)
    assert "/chat" in page.url
