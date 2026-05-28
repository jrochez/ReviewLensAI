# ReviewLens AI — Test Report

**Date:** 2026-05-27  
**Backend:** FastAPI on `http://127.0.0.1:9000`  
**Frontend:** Next.js on `http://localhost:9001`

---

## Summary

| Suite | Tests | Passed | Skipped | Failed |
|-------|-------|--------|---------|--------|
| Unit | 30 | 30 | 0 | 0 |
| Integration | 19 | 18 | 1 | 0 |
| E2E (Playwright) | 17 | 17 | 0 | 0 |
| **Total** | **66** | **65** | **1** | **0** |

---

## Unit Tests

**File:** `tests/backend/unit/`  
**Runner:** `pytest tests/backend/unit/ -v`  
**Result:** 30 passed

### ASIN Extraction (`test_asin_extraction.py`)

| Test | Result |
|------|--------|
| `test_bare_asin` | PASSED |
| `test_full_amazon_url` | PASSED |
| `test_amazon_url_with_slug` | PASSED |
| `test_amazon_co_uk` | PASSED |
| `test_lowercase_asin_rejected` | PASSED |
| `test_short_asin_rejected` | PASSED |
| `test_non_amazon_url_rejected` | PASSED |
| `test_localhost_rejected` | PASSED |
| `test_aws_metadata_rejected` | PASSED |
| `test_random_string_rejected` | PASSED |

### Security Layer (`test_security.py`)

| Test | Result |
|------|--------|
| `test_blocklist_scan_clean` | PASSED |
| `test_blocklist_scan_detected` | PASSED |
| `test_blocklist_case_insensitive` | PASSED |
| `test_input_guard_truncates` | PASSED |
| `test_input_guard_clean_message` | PASSED |
| `test_input_guard_injection_detected` | PASSED |
| `test_history_valid_roles_pass` | PASSED |
| `test_history_invalid_role_raises` | PASSED |
| `test_history_tool_role_raises` | PASSED |
| `test_history_capped_at_max_turns` | PASSED |
| `test_history_assistant_injection_dropped` | PASSED |
| `test_empty_history` | PASSED |
| `test_output_guard_clean` | PASSED |
| `test_output_guard_disclosure_redacted` | PASSED |
| `test_output_guard_injection_artifact_raises` | PASSED |

### Theme Extraction (`test_themes.py`)

| Test | Result |
|------|--------|
| `test_empty_corpus` | PASSED |
| `test_single_review` | PASSED |
| `test_multiple_reviews` | PASSED |
| `test_result_count_bounded` | PASSED |
| `test_results_are_tuples` | PASSED |

---

## Integration Tests

**File:** `tests/backend/integration/test_api.py`  
**Runner:** `pytest tests/backend/integration/ -v`  
**Result:** 18 passed, 1 skipped  
**Note:** Tests run against a live backend; backend must be running on `http://127.0.0.1:9000`

| Test | Result | Notes |
|------|--------|-------|
| `test_health` | PASSED | |
| `test_login_valid` | PASSED | |
| `test_login_invalid_password` | PASSED | |
| `test_login_invalid_email` | PASSED | |
| `test_protected_route_without_token` | PASSED | |
| `test_logout` | PASSED | Token invalidated after logout |
| `test_list_datasets_empty_or_some` | PASSED | |
| `test_create_dataset_valid_asin` | PASSED | |
| `test_create_dataset_invalid_asin` | PASSED | Returns 422 INVALID_ASIN |
| `test_create_dataset_invalid_url` | PASSED | Non-amazon URLs rejected |
| `test_create_dataset_from_full_url` | PASSED | ASIN extracted from full URL |
| `test_get_dataset_not_found` | PASSED | Returns 404 DATASET_NOT_FOUND |
| `test_delete_dataset_not_found` | PASSED | |
| `test_rate_limit_endpoint` | PASSED | |
| `test_reviews_endpoint` | PASSED | |
| `test_reviews_pagination` | PASSED | |
| `test_reviews_sort_stars` | PASSED | |
| `test_summary_endpoint` | PASSED | Stats, sentiment, themes all present |
| `test_chat_not_ready_dataset` | SKIPPED | Mock scraper completes too fast to test pending state |

---

## E2E Tests (Playwright / Chromium)

**File:** `tests/e2e/test_app.py`  
**Runner:** `pytest tests/e2e/ -v --browser chromium`  
**Result:** 17 passed  
**Note:** AI/chat functionality intentionally excluded per spec. Backend and frontend must be running.

### Login Flow

| Test | Result |
|------|--------|
| `test_login_page_renders` | PASSED |
| `test_login_invalid_credentials` | PASSED |
| `test_login_valid_credentials` | PASSED |

### Authenticated Navigation

| Test | Result |
|------|--------|
| `test_unauthenticated_redirect` | PASSED |
| `test_datasets_page_renders_after_login` | PASSED |
| `test_top_nav_visible` | PASSED |
| `test_user_menu` | PASSED |

### Dataset Creation Flow

| Test | Result |
|------|--------|
| `test_new_dataset_page_renders` | PASSED |
| `test_new_dataset_invalid_asin_shows_error` | PASSED |
| `test_new_dataset_create_and_progress` | PASSED |

### Dataset List

| Test | Result |
|------|--------|
| `test_search_datasets` | PASSED |
| `test_logout_flow` | PASSED |

### Dataset Detail Page

| Test | Result |
|------|--------|
| `test_dataset_detail_page` | PASSED |
| `test_dataset_detail_shows_stats` | PASSED |
| `test_dataset_detail_shows_themes` | PASSED |
| `test_dataset_detail_review_table` | PASSED |
| `test_navigate_to_chat` | PASSED |

---

## How to Run

### Prerequisites

```bash
# Backend (from ReviewLensAI/backend/)
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload

# Frontend (from ReviewLensAI/frontend/)
npm install
npm run dev -- --port 9001
```

### Unit + Integration Tests

```bash
cd backend
pytest ../tests/backend/ -v
```

### E2E Tests

```bash
cd backend
playwright install chromium  # first time only
pytest ../tests/e2e/ -v
```

### All Tests

```bash
cd backend
pytest ../tests/ -v --ignore=../tests/e2e  # backend only (no browser needed)
pytest ../tests/e2e/ -v                    # E2E (requires both servers running)
```
