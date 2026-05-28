"""Integration tests against the live backend at http://127.0.0.1:9000."""
import pytest
import httpx

BASE = "http://127.0.0.1:9000/api/v1"
DEFAULT_EMAIL = "analyst@firm.com"
DEFAULT_PASSWORD = "password123"


def login() -> str:
    """Login and return bearer token."""
    r = httpx.post(f"{BASE}/auth/login", json={"email": DEFAULT_EMAIL, "password": DEFAULT_PASSWORD})
    assert r.status_code == 200, f"Login failed: {r.text}"
    return r.json()["token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_health():
    r = httpx.get("http://127.0.0.1:9000/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_login_valid():
    r = httpx.post(f"{BASE}/auth/login", json={"email": DEFAULT_EMAIL, "password": DEFAULT_PASSWORD})
    assert r.status_code == 200
    data = r.json()
    assert "token" in data
    assert "expires_at" in data
    assert data["user"]["email"] == DEFAULT_EMAIL


def test_login_invalid_password():
    r = httpx.post(f"{BASE}/auth/login", json={"email": DEFAULT_EMAIL, "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["error_code"] == "INVALID_CREDENTIALS"


def test_login_invalid_email():
    r = httpx.post(f"{BASE}/auth/login", json={"email": "nobody@nowhere.com", "password": "anything"})
    assert r.status_code == 401


def test_protected_route_without_token():
    r = httpx.get(f"{BASE}/datasets")
    assert r.status_code == 401


def test_logout():
    token = login()
    r = httpx.post(f"{BASE}/auth/logout", headers=auth_headers(token))
    assert r.status_code == 204
    # Token should be invalid now
    r2 = httpx.get(f"{BASE}/datasets", headers=auth_headers(token))
    assert r2.status_code == 401


# ── Datasets ──────────────────────────────────────────────────────────────────

def test_list_datasets_empty_or_some():
    token = login()
    r = httpx.get(f"{BASE}/datasets", headers=auth_headers(token))
    assert r.status_code == 200
    assert "datasets" in r.json()


def test_create_dataset_valid_asin():
    token = login()
    r = httpx.post(f"{BASE}/datasets", json={"input": "B08N5WRWNW"}, headers=auth_headers(token))
    assert r.status_code in (201, 409)  # 409 if a scrape is already in progress
    if r.status_code == 201:
        data = r.json()
        assert data["asin"] == "B08N5WRWNW"
        assert data["status"] == "pending"
        return data["id"]


def test_create_dataset_invalid_asin():
    token = login()
    r = httpx.post(f"{BASE}/datasets", json={"input": "not-an-asin"}, headers=auth_headers(token))
    assert r.status_code == 422
    assert r.json()["error_code"] == "INVALID_ASIN"


def test_create_dataset_invalid_url():
    token = login()
    r = httpx.post(f"{BASE}/datasets", json={"input": "http://evil.com/dp/B08N5WRWNW"}, headers=auth_headers(token))
    assert r.status_code == 422
    assert r.json()["error_code"] == "INVALID_ASIN"


def test_create_dataset_from_full_url():
    token = login()
    r = httpx.post(
        f"{BASE}/datasets",
        json={"input": "https://www.amazon.com/Wireless/dp/B09XYZ1234"},
        headers=auth_headers(token)
    )
    assert r.status_code in (201, 409)
    if r.status_code == 201:
        assert r.json()["asin"] == "B09XYZ1234"


def test_get_dataset_not_found():
    token = login()
    r = httpx.get(f"{BASE}/datasets/nonexistent-id-123", headers=auth_headers(token))
    assert r.status_code == 404
    assert r.json()["error_code"] == "DATASET_NOT_FOUND"


def test_delete_dataset_not_found():
    token = login()
    r = httpx.delete(f"{BASE}/datasets/nonexistent-id-abc", headers=auth_headers(token))
    assert r.status_code == 404


# ── Scrape rate limit ─────────────────────────────────────────────────────────

def test_rate_limit_endpoint():
    token = login()
    r = httpx.get(f"{BASE}/scrape/rate-limit", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert "daily_limit" in data
    assert "reviews_fetched_today" in data
    assert "suspended" in data
    assert isinstance(data["suspended"], bool)


# ── Reviews & Summary for a ready dataset ────────────────────────────────────

@pytest.fixture(scope="module")
def ready_dataset_id():
    """Create a dataset and wait for it to be ready (uses mock scraper)."""
    import time
    token = login()
    headers = auth_headers(token)

    # Create dataset
    r = httpx.post(f"{BASE}/datasets", json={"input": "B00TEST123"}, headers=headers)
    if r.status_code == 422:
        pytest.skip(f"ASIN rejected: {r.text}")
    if r.status_code not in (201, 409):
        pytest.skip(f"Unexpected status: {r.status_code} {r.text}")
    if r.status_code == 409:
        # Another scrape in progress; get first ready dataset
        datasets_r = httpx.get(f"{BASE}/datasets", headers=headers)
        for ds in datasets_r.json().get("datasets", []):
            if ds["status"] == "ready":
                return ds["id"]
        pytest.skip("No ready dataset available and scrape in progress")

    dataset_id = r.json()["id"]

    # Poll for ready (mock scraper is instant, but there's async delay)
    for _ in range(30):
        time.sleep(2)
        status_r = httpx.get(f"{BASE}/datasets/{dataset_id}", headers=headers)
        if status_r.json().get("status") == "ready":
            return dataset_id
        if status_r.json().get("status") == "error":
            pytest.skip(f"Dataset errored: {status_r.json().get('error_message')}")

    pytest.skip("Dataset didn't reach ready state in time")


def test_reviews_endpoint(ready_dataset_id):
    token = login()
    r = httpx.get(f"{BASE}/datasets/{ready_dataset_id}/reviews", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert "total" in data
    assert "reviews" in data
    assert isinstance(data["reviews"], list)


def test_reviews_pagination(ready_dataset_id):
    token = login()
    r = httpx.get(f"{BASE}/datasets/{ready_dataset_id}/reviews?page=1&per_page=2", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert len(data["reviews"]) <= 2


def test_reviews_sort_stars(ready_dataset_id):
    token = login()
    r = httpx.get(f"{BASE}/datasets/{ready_dataset_id}/reviews?sort=stars_desc", headers=auth_headers(token))
    assert r.status_code == 200
    reviews = r.json()["reviews"]
    if len(reviews) >= 2:
        assert reviews[0]["star_rating"] >= reviews[-1]["star_rating"]


def test_summary_endpoint(ready_dataset_id):
    token = login()
    r = httpx.get(f"{BASE}/datasets/{ready_dataset_id}/summary", headers=auth_headers(token))
    assert r.status_code == 200
    data = r.json()
    assert "stats" in data
    assert "sentiment" in data
    assert "themes" in data
    assert data["stats"]["review_count"] > 0


def test_chat_not_ready_dataset():
    token = login()
    # Create a dataset that won't be ready
    r = httpx.post(f"{BASE}/datasets", json={"input": "B00PENDING0"}, headers=auth_headers(token))
    if r.status_code != 201:
        pytest.skip("Could not create pending dataset")
    ds_id = r.json()["id"]
    # Immediately try to chat (it'll be pending/scraping briefly before mock completes)
    # This might succeed if mock is too fast; just verify the endpoint doesn't 500
    chat_r = httpx.post(f"{BASE}/datasets/{ds_id}/chat", json={"message": "hello", "history": []}, headers=auth_headers(token))
    assert chat_r.status_code in (200, 400, 404)
