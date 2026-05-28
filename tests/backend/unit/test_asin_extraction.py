import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'backend'))

import pytest
try:
    from app.routers.datasets import extract_asin
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    extract_asin = None

skip_if_no_backend = pytest.mark.skipif(not BACKEND_AVAILABLE, reason="Backend not built")


@skip_if_no_backend
def test_bare_asin():
    assert extract_asin("B08N5WRWNW") == "B08N5WRWNW"


@skip_if_no_backend
def test_full_amazon_url():
    assert extract_asin("https://www.amazon.com/dp/B08N5WRWNW") == "B08N5WRWNW"


@skip_if_no_backend
def test_amazon_url_with_slug():
    assert extract_asin("https://www.amazon.com/Wireless-Headphones/dp/B08N5WRWNW/ref=sr_1_1") == "B08N5WRWNW"


@skip_if_no_backend
def test_amazon_co_uk():
    assert extract_asin("https://www.amazon.co.uk/dp/B08N5WRWNW") == "B08N5WRWNW"


@skip_if_no_backend
def test_lowercase_asin_rejected():
    with pytest.raises(Exception):
        extract_asin("b08n5wrwnw")


@skip_if_no_backend
def test_short_asin_rejected():
    with pytest.raises(Exception):
        extract_asin("B08N5WRW")


@skip_if_no_backend
def test_non_amazon_url_rejected():
    with pytest.raises(Exception):
        extract_asin("http://evil.com/dp/B08N5WRWNW")


@skip_if_no_backend
def test_localhost_rejected():
    with pytest.raises(Exception):
        extract_asin("http://localhost:8080/admin")


@skip_if_no_backend
def test_aws_metadata_rejected():
    with pytest.raises(Exception):
        extract_asin("http://169.254.169.254/latest/meta-data/")


@skip_if_no_backend
def test_random_string_rejected():
    with pytest.raises(Exception):
        extract_asin("not-an-asin-or-url")
