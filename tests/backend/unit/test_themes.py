import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

import pytest
try:
    from app.services.themes import extract_themes
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

skip_if_no_backend = pytest.mark.skipif(not BACKEND_AVAILABLE, reason="Backend not built")


@skip_if_no_backend
def test_empty_corpus():
    result = extract_themes([])
    assert result == []


@skip_if_no_backend
def test_single_review():
    result = extract_themes(["Great battery life and excellent sound quality"])
    assert isinstance(result, list)
    assert len(result) >= 1


@skip_if_no_backend
def test_multiple_reviews():
    corpus = [
        "The battery life is excellent and lasts all day",
        "Battery drains fast but sound quality is superb",
        "Great sound quality, poor battery life after months",
        "Setup was easy and the battery life is good",
        "Connectivity issues and the battery life is poor",
    ]
    result = extract_themes(corpus)
    themes = [t for t, _ in result]
    assert any("battery" in t for t in themes), f"Expected 'battery' in themes, got {themes}"


@skip_if_no_backend
def test_result_count_bounded():
    corpus = [f"This product is great with feature {i}" for i in range(50)]
    result = extract_themes(corpus)
    assert len(result) <= 30


@skip_if_no_backend
def test_results_are_tuples():
    result = extract_themes(["Good product with great quality and value"])
    for item in result:
        assert len(item) == 2
        assert isinstance(item[0], str)
        assert isinstance(item[1], int)
